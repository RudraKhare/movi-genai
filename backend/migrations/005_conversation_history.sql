-- Migration: 005_conversation_history.sql
-- Purpose: Add conversation_history column to agent_sessions for session memory
-- Date: Context-aware implementation

-- Add conversation_history column to store chat history for context-aware responses
ALTER TABLE agent_sessions 
ADD COLUMN IF NOT EXISTS conversation_history JSONB DEFAULT '[]';

-- Update table comment
COMMENT ON COLUMN agent_sessions.conversation_history IS 'Array of conversation messages for context-aware AI responses';

-- Create index for conversation history queries (if needed for analytics)
CREATE INDEX IF NOT EXISTS idx_agent_sessions_conversation_history 
ON agent_sessions USING GIN (conversation_history);
