-- ========================================================
-- MOVI Schema Alignment Migration
-- Day 6 Patch: Fix column name mismatches
-- ========================================================
-- This script is IDEMPOTENT and safe to re-run
-- ========================================================

-- ========================================================
-- STOPS TABLE FIX
-- ========================================================

-- Add missing 'status' column to stops table
-- Backend expects: INSERT INTO stops (name, status) VALUES (...)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'stops' AND column_name = 'status'
    ) THEN
        ALTER TABLE stops ADD COLUMN status TEXT DEFAULT 'Active';
    END IF;
END $$;

-- ========================================================
-- PATHS TABLE FIX
-- ========================================================

-- Rename 'name' to 'path_name' to match backend expectations
-- Backend expects: INSERT INTO paths (path_name) VALUES (...)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'paths' AND column_name = 'name'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'paths' AND column_name = 'path_name'
    ) THEN
        ALTER TABLE paths RENAME COLUMN name TO path_name;
    END IF;
END $$;

-- ========================================================
-- ROUTES TABLE FIX
-- ========================================================

-- Rename 'route_display_name' to 'route_name' to match backend
-- Backend expects: INSERT INTO routes (route_name, shift_time, path_id, direction)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'routes' AND column_name = 'route_display_name'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'routes' AND column_name = 'route_name'
    ) THEN
        ALTER TABLE routes RENAME COLUMN route_display_name TO route_name;
    END IF;
END $$;

-- ========================================================
-- VEHICLES TABLE FIX
-- ========================================================

-- Rename 'license_plate' to 'registration_number' to match backend models
-- Backend models expect: registration_number field
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vehicles' AND column_name = 'license_plate'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vehicles' AND column_name = 'registration_number'
    ) THEN
        ALTER TABLE vehicles RENAME COLUMN license_plate TO registration_number;
    END IF;
END $$;

-- ========================================================
-- UPDATE VIEW (if it references old column names)
-- ========================================================

-- Drop and recreate the trips_with_deployments view with correct column names
DROP VIEW IF EXISTS trips_with_deployments;

CREATE OR REPLACE VIEW trips_with_deployments AS
SELECT 
  dt.trip_id,
  dt.display_name,
  dt.trip_date,
  dt.booking_status_percentage,
  dt.live_status,
  r.route_name,
  v.registration_number,
  v.vehicle_type,
  d.name as driver_name,
  d.phone as driver_phone
FROM daily_trips dt
LEFT JOIN routes r ON dt.route_id = r.route_id
LEFT JOIN deployments dep ON dt.trip_id = dep.trip_id
LEFT JOIN vehicles v ON dep.vehicle_id = v.vehicle_id
LEFT JOIN drivers d ON dep.driver_id = d.driver_id;

-- ========================================================
-- VERIFICATION QUERIES
-- ========================================================
-- Run these after migration to verify:

-- Check stops table has status column
-- SELECT stop_id, name, status FROM stops LIMIT 1;

-- Check paths table has path_name column
-- SELECT path_id, path_name FROM paths LIMIT 1;

-- Check routes table has route_name column
-- SELECT route_id, route_name, shift_time FROM routes LIMIT 1;

-- Check vehicles table has registration_number column
-- SELECT vehicle_id, registration_number, capacity FROM vehicles LIMIT 1;

-- ========================================================
-- MIGRATION COMPLETE
-- ========================================================
