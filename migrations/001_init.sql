-- =============================
-- MOVI DATABASE INITIALIZATION
-- Stop → Path → Route → Trip Hierarchy
-- =============================

-- Drop existing tables if any (for clean re-runs)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS deployments CASCADE;
DROP TABLE IF EXISTS daily_trips CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS path_stops CASCADE;
DROP TABLE IF EXISTS paths CASCADE;
DROP TABLE IF EXISTS stops CASCADE;

-- ---------- STATIC ASSETS ----------

-- Table: stops
-- Individual locations in the transport network
CREATE TABLE stops (
  stop_id serial PRIMARY KEY,
  name text NOT NULL UNIQUE,
  latitude numeric(10, 6),
  longitude numeric(10, 6),
  address text,
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE stops IS 'Physical locations where vehicles pick up/drop off passengers';

-- Table: paths
-- Named sequences of stops
CREATE TABLE paths (
  path_id serial PRIMARY KEY,
  name text NOT NULL UNIQUE,
  description text,
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE paths IS 'Ordered sequences of stops forming a route backbone';

-- Mapping: path_stops
-- Ordered list of stops for each path
CREATE TABLE path_stops (
  id serial PRIMARY KEY,
  path_id int REFERENCES paths(path_id) ON DELETE CASCADE,
  stop_id int REFERENCES stops(stop_id) ON DELETE CASCADE,
  stop_order int NOT NULL,
  UNIQUE(path_id, stop_id),
  UNIQUE(path_id, stop_order)
);

COMMENT ON TABLE path_stops IS 'Many-to-many mapping with order: Path → Stops';

-- Table: routes
-- Combines a Path + Time + Direction + Status
CREATE TABLE routes (
  route_id serial PRIMARY KEY,
  path_id int REFERENCES paths(path_id) ON DELETE SET NULL,
  route_display_name text NOT NULL UNIQUE,
  shift_time time,
  direction text CHECK (direction IN ('up','down')) DEFAULT 'up',
  start_point text,
  end_point text,
  status text CHECK (status IN ('active','deactivated')) DEFAULT 'active',
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE routes IS 'Scheduled routes = Path + Time. Used by manageRoute page';

-- ---------- DYNAMIC ASSETS ----------

-- Table: vehicles
-- Physical transport assets
CREATE TABLE vehicles (
  vehicle_id serial PRIMARY KEY,
  license_plate text UNIQUE NOT NULL,
  vehicle_type text CHECK (vehicle_type IN ('Bus','Cab')) NOT NULL,
  capacity int CHECK (capacity > 0),
  status text CHECK (status IN ('available','deployed','maintenance')) DEFAULT 'available',
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE vehicles IS 'Transport vehicles (buses/cabs) available for deployment';

-- Table: drivers
-- Personnel assigned to vehicles
CREATE TABLE drivers (
  driver_id serial PRIMARY KEY,
  name text NOT NULL,
  phone text UNIQUE,
  license_number text,
  status text CHECK (status IN ('available','on_trip','off_duty')) DEFAULT 'available',
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE drivers IS 'Drivers who operate vehicles';

-- Table: daily_trips
-- The live trips displayed on busDashboard
CREATE TABLE daily_trips (
  trip_id serial PRIMARY KEY,
  route_id int REFERENCES routes(route_id) ON DELETE CASCADE,
  display_name text NOT NULL,
  trip_date date DEFAULT CURRENT_DATE,
  booking_status_percentage int DEFAULT 0 CHECK (booking_status_percentage >= 0 AND booking_status_percentage <= 100),
  live_status text CHECK (live_status IN ('SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED')) DEFAULT 'SCHEDULED',
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE daily_trips IS 'Daily trip instances. Core entity for busDashboard page';

-- Table: deployments
-- Vehicle + Driver assigned to a specific trip
CREATE TABLE deployments (
  deployment_id serial PRIMARY KEY,
  trip_id int REFERENCES daily_trips(trip_id) ON DELETE CASCADE UNIQUE,
  vehicle_id int REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
  driver_id int REFERENCES drivers(driver_id) ON DELETE SET NULL,
  deployed_at timestamptz DEFAULT now()
);

COMMENT ON TABLE deployments IS 'Links vehicle + driver to a daily trip';

-- Table: bookings
-- Employee bookings for trips (for percentage calculation & consequence checking)
CREATE TABLE bookings (
  booking_id serial PRIMARY KEY,
  trip_id int REFERENCES daily_trips(trip_id) ON DELETE CASCADE,
  user_id int NOT NULL,
  user_name text,
  seats int DEFAULT 1 CHECK (seats > 0),
  status text CHECK (status IN ('CONFIRMED','CANCELLED')) DEFAULT 'CONFIRMED',
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE bookings IS 'Employee bookings. Used for tribal knowledge checks';

-- Table: audit_logs
-- Track agent actions for accountability
CREATE TABLE audit_logs (
  log_id serial PRIMARY KEY,
  action text NOT NULL,
  user_id int,
  entity_type text,
  entity_id int,
  details jsonb,
  created_at timestamptz DEFAULT now()
);

COMMENT ON TABLE audit_logs IS 'Audit trail for all Movi agent actions';

-- ---------- INDEXES ----------
CREATE INDEX idx_routes_path ON routes(path_id);
CREATE INDEX idx_routes_status ON routes(status);
CREATE INDEX idx_daily_trips_route ON daily_trips(route_id);
CREATE INDEX idx_daily_trips_date ON daily_trips(trip_date);
CREATE INDEX idx_daily_trips_status ON daily_trips(live_status);
CREATE INDEX idx_bookings_trip ON bookings(trip_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_deployments_trip ON deployments(trip_id);
CREATE INDEX idx_path_stops_path ON path_stops(path_id);

-- ---------- VIEWS (Optional - for easier querying) ----------

-- View: trips_with_deployments
-- Combines trip info with vehicle/driver details
CREATE OR REPLACE VIEW trips_with_deployments AS
SELECT 
  dt.trip_id,
  dt.display_name,
  dt.trip_date,
  dt.booking_status_percentage,
  dt.live_status,
  r.route_display_name,
  v.license_plate,
  v.vehicle_type,
  d.name as driver_name,
  d.phone as driver_phone
FROM daily_trips dt
LEFT JOIN routes r ON dt.route_id = r.route_id
LEFT JOIN deployments dep ON dt.trip_id = dep.trip_id
LEFT JOIN vehicles v ON dep.vehicle_id = v.vehicle_id
LEFT JOIN drivers d ON dep.driver_id = d.driver_id;

COMMENT ON VIEW trips_with_deployments IS 'Denormalized view for busDashboard display';

-- ---------- FUNCTIONS ----------

-- Function: update_booking_percentage
-- Automatically recalculates booking percentage when bookings change
CREATE OR REPLACE FUNCTION update_booking_percentage()
RETURNS TRIGGER AS $$
DECLARE
  total_bookings int;
  vehicle_capacity int;
  trip_vehicle_id int;
BEGIN
  -- Get vehicle capacity for this trip
  SELECT v.capacity INTO vehicle_capacity
  FROM deployments dep
  JOIN vehicles v ON dep.vehicle_id = v.vehicle_id
  WHERE dep.trip_id = COALESCE(NEW.trip_id, OLD.trip_id);
  
  -- If no vehicle assigned, set to 0
  IF vehicle_capacity IS NULL THEN
    UPDATE daily_trips 
    SET booking_status_percentage = 0 
    WHERE trip_id = COALESCE(NEW.trip_id, OLD.trip_id);
    RETURN NEW;
  END IF;
  
  -- Calculate total confirmed seats
  SELECT COALESCE(SUM(seats), 0) INTO total_bookings
  FROM bookings
  WHERE trip_id = COALESCE(NEW.trip_id, OLD.trip_id) 
    AND status = 'CONFIRMED';
  
  -- Update percentage (cap at 100)
  UPDATE daily_trips 
  SET booking_status_percentage = LEAST(100, (total_bookings * 100) / vehicle_capacity)
  WHERE trip_id = COALESCE(NEW.trip_id, OLD.trip_id);
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: recalculate booking percentage on insert/update/delete
CREATE TRIGGER trg_update_booking_percentage_insert
AFTER INSERT ON bookings
FOR EACH ROW EXECUTE FUNCTION update_booking_percentage();

CREATE TRIGGER trg_update_booking_percentage_update
AFTER UPDATE ON bookings
FOR EACH ROW EXECUTE FUNCTION update_booking_percentage();

CREATE TRIGGER trg_update_booking_percentage_delete
AFTER DELETE ON bookings
FOR EACH ROW EXECUTE FUNCTION update_booking_percentage();

-- ---------- SAMPLE QUERY TESTS ----------
-- Uncomment to test after seeding:

-- SELECT * FROM stops LIMIT 5;
-- SELECT * FROM routes WHERE status = 'active';
-- SELECT * FROM trips_with_deployments WHERE booking_status_percentage > 50;
-- SELECT COUNT(*) FROM bookings WHERE status = 'CONFIRMED';

-- =============================
-- MIGRATION COMPLETE
-- =============================
