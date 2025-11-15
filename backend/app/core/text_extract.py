"""
Text Extraction and Cleaning Module

Handles text normalization, cleaning, and candidate extraction from OCR output.
"""

import re
from typing import List, Set


def clean_text(text: str) -> str:
    """
    Clean and normalize OCR text output.
    
    Steps:
    1. Convert to lowercase
    2. Fix common OCR errors
    3. Remove extra whitespace
    4. Normalize punctuation
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Fix common OCR errors
    ocr_corrections = {
        '|': 'i',
        '0': 'o',  # In words, 0 might be o
        '1': 'i',  # In words, 1 might be i or l
        '5': 's',  # Sometimes 5 is read as s
        '@': 'a',
        '$': 's',
        '!': 'i',
    }
    
    # Apply corrections cautiously (only for alphabetic contexts)
    # More sophisticated: only replace if surrounded by letters
    for wrong, correct in ocr_corrections.items():
        # Replace only if not part of a number
        text = re.sub(f'(?<=[a-z]){re.escape(wrong)}(?=[a-z])', correct, text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Normalize dashes
    text = text.replace('—', '-').replace('–', '-')
    
    return text


def extract_time_patterns(text: str) -> List[str]:
    """
    Extract time patterns from text.
    
    Patterns:
    - HH:MM (24-hour format)
    - H:MM
    - HH.MM (with dot separator)
    - HHMM (no separator)
    
    Args:
        text: Input text
        
    Returns:
        List of time strings
    """
    times = []
    
    # Pattern 1: HH:MM or H:MM
    pattern1 = r'\b([0-2]?[0-9]):([0-5][0-9])\b'
    matches = re.findall(pattern1, text)
    for hour, minute in matches:
        times.append(f"{hour}:{minute}")
    
    # Pattern 2: HH.MM
    pattern2 = r'\b([0-2]?[0-9])\.([0-5][0-9])\b'
    matches = re.findall(pattern2, text)
    for hour, minute in matches:
        times.append(f"{hour}:{minute}")
    
    # Pattern 3: HHMM (4 digits)
    pattern3 = r'\b([0-2][0-9])([0-5][0-9])\b'
    matches = re.findall(pattern3, text)
    for hour, minute in matches:
        times.append(f"{hour}:{minute}")
    
    return list(set(times))  # Remove duplicates


def extract_route_keywords(text: str) -> List[str]:
    """
    Extract potential route names and keywords.
    
    Common patterns:
    - "Route X"
    - "Path X"
    - "Line X"
    - City names
    - Area names
    
    Args:
        text: Input text
        
    Returns:
        List of route keywords
    """
    keywords = []
    
    # Pattern 1: Route/Path/Line followed by name
    pattern1 = r'\b(route|path|line|bus)\s+([a-z0-9\-]+)\b'
    matches = re.findall(pattern1, text, re.IGNORECASE)
    for prefix, name in matches:
        keywords.append(f"{prefix} {name}".lower())
        keywords.append(name.lower())
    
    # Pattern 2: Capitalized words (potential area names)
    # Look for sequences of capitalized words in original text before lowercasing
    original_caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    keywords.extend([word.lower() for word in original_caps])
    
    # Pattern 3: Hyphenated phrases (common in route names)
    pattern3 = r'\b([a-z]+(?:-[a-z]+)+)\b'
    matches = re.findall(pattern3, text, re.IGNORECASE)
    keywords.extend([m.lower() for m in matches])
    
    return list(set(keywords))  # Remove duplicates


def extract_shift_patterns(text: str) -> List[str]:
    """
    Extract shift-style patterns like "Bulk - 00:01".
    
    Args:
        text: Input text
        
    Returns:
        List of shift pattern strings
    """
    patterns = []
    
    # Pattern: Word - Time
    # Example: "Bulk - 00:01", "BTM - 08:30"
    pattern = r'\b([a-z]+)\s*-\s*([0-2]?[0-9]:[0-5][0-9])\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    for name, time in matches:
        patterns.append(f"{name.lower()} - {time}")
    
    return patterns


def extract_candidates(text: str) -> List[str]:
    """
    Extract all candidate strings that might match a trip.
    
    Returns a comprehensive list of:
    - Full text
    - Individual lines
    - Time patterns
    - Route keywords
    - Shift patterns
    - N-grams (2-3 word sequences)
    
    Args:
        text: Cleaned OCR text
        
    Returns:
        List of candidate strings (10-30 items typically)
    """
    if not text:
        return []
    
    candidates: Set[str] = set()
    
    # 1. Full text
    candidates.add(text)
    
    # 2. Individual lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    candidates.update(lines)
    
    # 3. Time patterns
    times = extract_time_patterns(text)
    candidates.update(times)
    
    # 4. Route keywords
    keywords = extract_route_keywords(text)
    candidates.update(keywords)
    
    # 5. Shift patterns
    shifts = extract_shift_patterns(text)
    candidates.update(shifts)
    
    # 6. Word sequences (bigrams and trigrams)
    words = text.split()
    for i in range(len(words)):
        # Bigrams
        if i < len(words) - 1:
            bigram = f"{words[i]} {words[i+1]}"
            if len(bigram) > 3:  # Skip very short sequences
                candidates.add(bigram)
        
        # Trigrams
        if i < len(words) - 2:
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            if len(trigram) > 5:
                candidates.add(trigram)
    
    # 7. Individual words (if meaningful)
    meaningful_words = [w for w in words if len(w) > 2]
    candidates.update(meaningful_words)
    
    # Convert to list and sort by length (longer strings first)
    candidate_list = sorted(list(candidates), key=len, reverse=True)
    
    # Limit to top 30 candidates
    return candidate_list[:30]


def normalize_text(text: str) -> str:
    """
    Full normalization pipeline: clean + extract candidates.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned and normalized text
    """
    return clean_text(text)
