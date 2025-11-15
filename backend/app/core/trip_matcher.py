"""
Trip Matching Module

Handles fuzzy matching of OCR-extracted text to trips in the database.
"""

import asyncpg
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz
from app.core.supabase_client import get_conn


async def get_daily_trips() -> List[Dict[str, Any]]:
    """
    Fetch all trips from the database with their display names.
    
    Returns:
        List of trip dictionaries with trip_id, display_name, route_id, etc.
    """
    pool = await get_conn()
    
    query = """
        SELECT 
            t.trip_id,
            t.display_name,
            t.route_id,
            t.trip_date,
            t.live_status,
            r.route_name,
            r.shift_time,
            p.path_name
        FROM daily_trips t
        LEFT JOIN routes r ON t.route_id = r.route_id
        LEFT JOIN paths p ON r.path_id = p.path_id
        ORDER BY t.trip_id
    """
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        
    trips = []
    for row in rows:
        # Format shift_time if it exists
        shift_time_str = None
        if row["shift_time"]:
            shift_time_str = str(row["shift_time"])[:5]  # HH:MM format
        
        trips.append({
            "trip_id": row["trip_id"],
            "display_name": row["display_name"],
            "route_id": row["route_id"],
            "trip_date": row["trip_date"].strftime("%Y-%m-%d") if row["trip_date"] else None,
            "scheduled_time": shift_time_str,  # Using shift_time from routes table
            "live_status": row["live_status"],
            "route_name": row["route_name"],
            "path_name": row["path_name"],
        })
    
    return trips


def compute_fuzzy_score(candidate: str, trip: Dict[str, Any]) -> float:
    """
    Compute weighted fuzzy matching score between candidate text and trip.
    
    Scoring components:
    - Display name match: 60 points (most important)
    - Time match: 25 points
    - Keyword match (route, path): 15 points
    
    Uses multiple fuzzy matching algorithms:
    - fuzz.ratio: Overall similarity
    - fuzz.partial_ratio: Substring matching
    - fuzz.token_set_ratio: Order-independent word matching
    
    Args:
        candidate: Candidate text string from OCR
        trip: Trip dictionary
        
    Returns:
        Score from 0.0 to 1.0
    """
    score = 0.0
    
    # Normalize candidate
    candidate = candidate.lower().strip()
    
    # Component 1: Display name matching (60 points max)
    display_name = trip.get("display_name", "").lower()
    if display_name:
        # Use best of three fuzzy methods
        ratio = fuzz.ratio(candidate, display_name) / 100.0
        partial = fuzz.partial_ratio(candidate, display_name) / 100.0
        token_set = fuzz.token_set_ratio(candidate, display_name) / 100.0
        
        # Take the maximum score
        best_name_score = max(ratio, partial, token_set)
        score += best_name_score * 60.0
    
    # Component 2: Time matching (25 points max)
    scheduled_time = trip.get("scheduled_time")
    if scheduled_time:
        # Check if time appears in candidate
        if scheduled_time in candidate:
            score += 25.0
        else:
            # Fuzzy time matching (in case OCR misread digits)
            time_ratio = fuzz.ratio(scheduled_time, candidate) / 100.0
            score += time_ratio * 25.0
    
    # Component 3: Keyword matching (15 points max)
    keywords = []
    
    if trip.get("route_name"):
        keywords.append(trip["route_name"].lower())
    if trip.get("path_name"):
        keywords.append(trip["path_name"].lower())
    
    if keywords:
        keyword_scores = []
        for keyword in keywords:
            kw_ratio = fuzz.partial_ratio(candidate, keyword) / 100.0
            keyword_scores.append(kw_ratio)
        
        # Use best keyword match
        best_keyword_score = max(keyword_scores) if keyword_scores else 0.0
        score += best_keyword_score * 15.0
    
    # Normalize to 0.0 - 1.0
    return score / 100.0


async def match_candidates(candidates: List[str], confidence_threshold: float = 0.65) -> Dict[str, Any]:
    """
    Match OCR candidates against database trips using fuzzy matching.
    
    Returns one of three structured responses:
    
    CASE A - Single Match (Confident):
    {
        "match_type": "single",
        "trip_id": 12,
        "display_name": "Bulk - 00:01",
        "confidence": 0.88,
        "auto_forward": true
    }
    
    CASE B - Multiple Matches (Ambiguous):
    {
        "match_type": "multiple",
        "candidates": [
            {"trip_id": 12, "display_name": "Bulk - 00:01", "confidence": 0.74},
            {"trip_id": 15, "display_name": "BTM - 00:05", "confidence": 0.61}
        ],
        "auto_forward": false,
        "needs_clarification": true
    }
    
    CASE C - No Match:
    {
        "match_type": "none",
        "message": "I could not identify a trip from this image.",
        "auto_forward": false
    }
    
    Args:
        candidates: List of candidate strings from OCR
        confidence_threshold: Minimum confidence for a match (default 0.65)
        
    Returns:
        Structured match result dictionary
    """
    if not candidates:
        return {
            "match_type": "none",
            "message": "No text extracted from image.",
            "auto_forward": False
        }
    
    # Get all trips from database
    trips = await get_daily_trips()
    
    if not trips:
        return {
            "match_type": "none",
            "message": "No trips available in the system.",
            "auto_forward": False
        }
    
    # Score all trips against all candidates
    trip_scores = {}
    
    for trip in trips:
        trip_id = trip["trip_id"]
        max_score = 0.0
        
        # Try each candidate against this trip
        for candidate in candidates:
            score = compute_fuzzy_score(candidate, trip)
            if score > max_score:
                max_score = score
        
        trip_scores[trip_id] = {
            "trip": trip,
            "confidence": max_score
        }
    
    # Sort by confidence (descending)
    sorted_matches = sorted(
        trip_scores.items(),
        key=lambda x: x[1]["confidence"],
        reverse=True
    )
    
    # Filter by threshold
    valid_matches = [
        (trip_id, data)
        for trip_id, data in sorted_matches
        if data["confidence"] >= confidence_threshold
    ]
    
    # CASE C: No matches above threshold
    if len(valid_matches) == 0:
        # Get best match even if below threshold
        best_match = sorted_matches[0] if sorted_matches else None
        if best_match:
            confidence = best_match[1]["confidence"]
            return {
                "match_type": "none",
                "message": f"I could not confidently identify a trip from this image. Best match was only {confidence:.0%} confident.",
                "auto_forward": False,
                "best_guess": {
                    "trip_id": best_match[0],
                    "display_name": best_match[1]["trip"]["display_name"],
                    "confidence": confidence
                }
            }
        else:
            return {
                "match_type": "none",
                "message": "I could not identify a trip from this image.",
                "auto_forward": False
            }
    
    # CASE A: Single confident match
    if len(valid_matches) == 1:
        trip_id, data = valid_matches[0]
        return {
            "match_type": "single",
            "trip_id": trip_id,
            "display_name": data["trip"]["display_name"],
            "confidence": data["confidence"],
            "auto_forward": True,
            "scheduled_time": data["trip"]["scheduled_time"],
            "route_name": data["trip"]["route_name"]
        }
    
    # CASE B: Multiple matches (ambiguous)
    # Check if top match is significantly better (>15% higher)
    top_confidence = valid_matches[0][1]["confidence"]
    second_confidence = valid_matches[1][1]["confidence"]
    
    if top_confidence - second_confidence > 0.15:
        # Clear winner - treat as single match
        trip_id, data = valid_matches[0]
        return {
            "match_type": "single",
            "trip_id": trip_id,
            "display_name": data["trip"]["display_name"],
            "confidence": data["confidence"],
            "auto_forward": True,
            "scheduled_time": data["trip"]["scheduled_time"],
            "route_name": data["trip"]["route_name"]
        }
    else:
        # Return top 3-5 candidates for clarification
        top_candidates = []
        for trip_id, data in valid_matches[:5]:
            top_candidates.append({
                "trip_id": trip_id,
                "display_name": data["trip"]["display_name"],
                "confidence": data["confidence"],
                "scheduled_time": data["trip"]["scheduled_time"],
                "route_name": data["trip"]["route_name"]
            })
        
        return {
            "match_type": "multiple",
            "candidates": top_candidates,
            "auto_forward": False,
            "needs_clarification": True,
            "message": "I found multiple possible trips. Which one did you mean?"
        }
