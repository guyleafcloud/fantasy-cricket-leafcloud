-- Fantasy Cricket Platform - Database Initialization
-- LeafCloud Amsterdam Deployment

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create database user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cricket_admin') THEN
        CREATE USER cricket_admin WITH ENCRYPTED PASSWORD 'change_this_password';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE fantasy_cricket TO cricket_admin;
GRANT ALL ON SCHEMA public TO cricket_admin;

-- Create initial data
-- This will be populated by the application on first run

-- Log initialization
INSERT INTO system_logs (event_type, description, created_at) 
VALUES ('initialization', 'Database initialized for LeafCloud deployment', NOW())
ON CONFLICT DO NOTHING;

-- Set timezone to Amsterdam
SET timezone TO 'Europe/Amsterdam';

-- Create indexes for performance
-- These will be created by SQLAlchemy migrations