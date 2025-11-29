"""
Automatic Trip Status Updater

This module handles automatic status transitions for trips based on current time:
- SCHEDULED → IN_PROGRESS (when current time >= trip start time)
- IN_PROGRESS → COMPLETED (when current time >= trip end time)

The updater runs as a background task and updates the database accordingly.
"""

import asyncio
import logging
from datetime import datetime, time as dt_time, timedelta
from typing import Dict, List, Any
import re

from app.core.supabase_client import get_conn

logger = logging.getLogger(__name__)

class TripStatusUpdater:
    """Handles automatic trip status transitions based on time"""
    
    def __init__(self):
        self.is_running = False
        self.update_interval = 60  # Check every minute
        self.trip_duration_hours = 2  # Default trip duration
        
    async def start_updater(self):
        """Start the background status updater"""
        if self.is_running:
            logger.warning("Status updater is already running")
            return
            
        self.is_running = True
        logger.info("🚀 Starting automatic trip status updater")
        
        while self.is_running:
            try:
                await self.update_trip_statuses()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"❌ Error in status updater: {e}")
                await asyncio.sleep(self.update_interval)  # Continue even if error occurs
    
    def stop_updater(self):
        """Stop the background status updater"""
        self.is_running = False
        logger.info("⏹️ Stopped automatic trip status updater")
    
    async def update_trip_statuses(self):
        """Check all trips and update their statuses based on current time"""
        try:
            pool = await get_conn()
            async with pool.acquire() as conn:
                # Get current time
                current_time = datetime.now()
                current_date = current_time.date()
                current_time_only = current_time.time()
                
                logger.debug(f"🕐 Checking trip statuses at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Get all trips that might need status updates
                trips = await conn.fetch("""
                    SELECT 
                        dt.trip_id,
                        dt.display_name,
                        dt.live_status,
                        dt.trip_date,
                        r.shift_time
                    FROM daily_trips dt
                    LEFT JOIN routes r ON dt.route_id = r.route_id
                    WHERE dt.live_status IN ('SCHEDULED', 'IN_PROGRESS')
                    AND dt.trip_date = $1
                    ORDER BY dt.trip_id
                """, current_date)
                
                updates_made = 0
                
                for trip in trips:
                    trip_updated = await self._update_single_trip_status(
                        conn, trip, current_time_only
                    )
                    if trip_updated:
                        updates_made += 1
                
                if updates_made > 0:
                    logger.info(f"✅ Updated {updates_made} trip status(es)")
                else:
                    logger.debug("🔄 No trip status updates needed")
                    
        except Exception as e:
            logger.error(f"❌ Error updating trip statuses: {e}")
            import traceback
            traceback.print_exc()
    
    async def _update_single_trip_status(
        self, 
        conn, 
        trip: Dict[str, Any], 
        current_time: dt_time
    ) -> bool:
        """Update status for a single trip if needed"""
        try:
            trip_id = trip['trip_id']
            display_name = trip['display_name']
            current_status = trip['live_status']
            shift_time = trip['shift_time']
            
            # Extract time from display_name if shift_time is None
            trip_start_time = self._extract_trip_time(display_name, shift_time)
            
            if not trip_start_time:
                logger.debug(f"⏭️ Trip {trip_id}: Cannot determine start time, skipping")
                return False
            
            # Calculate trip end time (start time + duration)
            trip_end_time = self._calculate_end_time(trip_start_time)
            
            # Determine what status should be
            new_status = self._determine_new_status(
                current_status, current_time, trip_start_time, trip_end_time
            )
            
            # Update if status should change
            if new_status and new_status != current_status:
                await conn.execute("""
                    UPDATE daily_trips 
                    SET live_status = $1 
                    WHERE trip_id = $2
                """, new_status, trip_id)
                
                logger.info(
                    f"🔄 Trip {trip_id} ({display_name}): {current_status} → {new_status}"
                )
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Error updating trip {trip.get('trip_id', 'unknown')}: {e}")
            return False
    
    def _extract_trip_time(self, display_name: str, shift_time: dt_time = None) -> dt_time:
        """Extract trip start time from display_name or use shift_time"""
        if shift_time:
            return shift_time
            
        # Extract time from display_name (format: "Path-1 - 08:00")
        if display_name:
            time_match = re.search(r'(\d{1,2}):(\d{2})', display_name)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                return dt_time(hour, minute)
        
        return None
    
    def _calculate_end_time(self, start_time: dt_time) -> dt_time:
        """Calculate trip end time based on start time + duration"""
        # Convert to datetime for calculation
        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = start_datetime + timedelta(hours=self.trip_duration_hours)
        return end_datetime.time()
    
    def _determine_new_status(
        self, 
        current_status: str, 
        current_time: dt_time,
        trip_start_time: dt_time,
        trip_end_time: dt_time
    ) -> str:
        """Determine what the trip status should be based on current time"""
        
        if current_status == 'SCHEDULED':
            # Should transition to IN_PROGRESS if current time >= start time
            if current_time >= trip_start_time:
                return 'IN_PROGRESS'
        
        elif current_status == 'IN_PROGRESS':
            # Should transition to COMPLETED if current time >= end time
            if current_time >= trip_end_time:
                return 'COMPLETED'
        
        # No status change needed
        return None

# Global instance
_status_updater = None

async def start_status_updater():
    """Start the global status updater"""
    global _status_updater
    if _status_updater is None:
        _status_updater = TripStatusUpdater()
    
    # Start the updater in the background
    asyncio.create_task(_status_updater.start_updater())
    logger.info("🚀 Status updater started successfully")

def stop_status_updater():
    """Stop the global status updater"""
    global _status_updater
    if _status_updater:
        _status_updater.stop_updater()

async def force_update_trip_statuses():
    """Force an immediate update of all trip statuses (for testing/manual trigger)"""
    global _status_updater
    if _status_updater is None:
        _status_updater = TripStatusUpdater()
    
    await _status_updater.update_trip_statuses()
    logger.info("🔄 Forced trip status update completed")

# Utility function for manual status override
async def manually_update_trip_status(trip_id: int, new_status: str, user_id: int = None):
    """Manually override a trip's status (for dispatcher use)"""
    valid_statuses = ['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
    
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
    
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get current status
            current = await conn.fetchrow("""
                SELECT live_status, display_name FROM daily_trips WHERE trip_id = $1
            """, trip_id)
            
            if not current:
                raise ValueError(f"Trip {trip_id} not found")
            
            # Update status
            await conn.execute("""
                UPDATE daily_trips SET live_status = $1 WHERE trip_id = $2
            """, new_status, trip_id)
            
            # Log the change
            if user_id:
                await conn.execute("""
                    INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details)
                    VALUES ($1, $2, $3, $4, $5)
                """, 'manual_status_update', 'trip', trip_id, user_id,
                     f'{{"old_status": "{current["live_status"]}", "new_status": "{new_status}"}}')
            
            logger.info(
                f"👤 Manual status update - Trip {trip_id} ({current['display_name']}): "
                f"{current['live_status']} → {new_status}"
            )
            
            return {
                "success": True,
                "trip_id": trip_id,
                "old_status": current['live_status'],
                "new_status": new_status
            }
            
    except Exception as e:
        logger.error(f"❌ Error manually updating trip status: {e}")
        raise
