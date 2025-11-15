-- Migration: 004_agent_sessions.sql
-- Purpose: Create agent_sessions table for managing confirmation workflows
-- Date: Day 7 - LangGraph Agent Implementation

-- Table: agent_sessions
-- Stores pending actions that require user confirmation
CREATE TABLE IF NOT EXISTS agent_sessions (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id INT NOT NULL,
  
  -- The action that is pending confirmation
  pending_action JSONB NOT NULL,
  
  -- Current status of the session
  status TEXT NOT NULL CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELLED', 'DONE', 'EXPIRED')),
  
  -- User's response (if any)
  user_response JSONB,
  
  -- Execution result (after action is performed)
  execution_result JSONB,
  
  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ DEFAULT (now() + INTERVAL '1 hour')
);

-- Index for faster lookups by user
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id 
ON agent_sessions(user_id);

-- Index for status-based queries
CREATE INDEX IF NOT EXISTS idx_agent_sessions_status 
ON agent_sessions(status);

-- Index for expiration cleanup
CREATE INDEX IF NOT EXISTS idx_agent_sessions_expires_at 
ON agent_sessions(expires_at);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_agent_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the update function
DROP TRIGGER IF EXISTS trigger_update_agent_sessions_updated_at ON agent_sessions;
CREATE TRIGGER trigger_update_agent_sessions_updated_at
  BEFORE UPDATE ON agent_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_agent_sessions_updated_at();

-- Add comments for documentation
COMMENT ON TABLE agent_sessions IS 'Stores agent conversation sessions requiring user confirmation';
COMMENT ON COLUMN agent_sessions.session_id IS 'Unique session identifier (UUID)';
COMMENT ON COLUMN agent_sessions.pending_action IS 'JSON representation of the action awaiting confirmation';
COMMENT ON COLUMN agent_sessions.status IS 'Current state: PENDING, CONFIRMED, CANCELLED, DONE, EXPIRED';
COMMENT ON COLUMN agent_sessions.user_response IS 'User confirmation response data';
COMMENT ON COLUMN agent_sessions.execution_result IS 'Result of executing the confirmed action';
COMMENT ON COLUMN agent_sessions.expires_at IS 'Session expiration time (default: 1 hour from creation)';

-- Insert sample data for testing (optional)
-- INSERT INTO agent_sessions (user_id, pending_action, status)
-- VALUES (
--   1,
--   '{"action": "remove_vehicle", "trip_id": 12, "trip_label": "Bulk - 00:01"}'::jsonb,
--   'PENDING'
-- );

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ Migration 004_agent_sessions completed successfully';
  RAISE NOTICE '   Created table: agent_sessions';
  RAISE NOTICE '   Created indexes: idx_agent_sessions_user_id, idx_agent_sessions_status, idx_agent_sessions_expires_at';
  RAISE NOTICE '   Created trigger: trigger_update_agent_sessions_updated_at';
END $$;
