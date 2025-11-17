-- Rename fantasy_teams.name to team_name to match model
-- Generated: 2025-11-17

BEGIN;

-- Rename name to team_name
ALTER TABLE fantasy_teams RENAME COLUMN name TO team_name;

-- Verify the change
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'fantasy_teams'
  AND column_name = 'team_name';

COMMIT;
