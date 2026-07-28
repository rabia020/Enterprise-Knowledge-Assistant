-- ============================================================
-- Memory Schema — Enterprise LangGraph + n8n Architecture
-- ============================================================

CREATE DATABASE agent_memory;
\c agent_memory

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── 1. AGENT STATE  (structured memory per user/session/agent)
-- Stores: user context, last_report, active_agents, routing decisions, etc.
CREATE TABLE IF NOT EXISTS agent_state (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "user"      TEXT NOT NULL,
    session_id  TEXT NOT NULL DEFAULT 'default',
    agent       TEXT NOT NULL DEFAULT 'supervisor',   -- supervisor|planner|research|rag|reporting
    key         TEXT NOT NULL,
    value       JSONB,
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE ("user", session_id, agent, key)
);

CREATE INDEX idx_state_lookup ON agent_state ("user", session_id, agent);

-- ── 2. ACTION LOG  (append-only audit of every n8n call)
-- Stores: web_search, email, calendar, jira, slack, database actions
CREATE TABLE IF NOT EXISTS action_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "user"      TEXT NOT NULL,
    session_id  TEXT NOT NULL,
    agent       TEXT NOT NULL,
    action_type TEXT NOT NULL,    -- 'web_search'|'email'|'calendar'|'jira'|'slack'|'database'
    payload     JSONB,            -- what was sent to n8n
    result      JSONB,            -- what n8n returned
    status      TEXT DEFAULT 'pending',  -- 'pending'|'success'|'error'
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_action_log_user ON action_log ("user", session_id);
CREATE INDEX idx_action_log_type ON action_log (action_type, status);

-- ── EXAMPLE ROWS matching your diagram's manager user ──
INSERT INTO agent_state ("user", session_id, agent, key, value) VALUES
  ('manager', 'sess_001', 'supervisor', 'last_report',    '"complaints"'),
  ('manager', 'sess_001', 'supervisor', 'active_agents',  '["planner","research","reporting"]'),
  ('manager', 'sess_001', 'reporting',  'last_report_complaints',
   '{"type":"complaints","timestamp":"2025-06-01T10:00:00Z"}')
ON CONFLICT DO NOTHING;