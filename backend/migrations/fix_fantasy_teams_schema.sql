-- Fix fantasy_teams schema - rename owner_id to user_id to match model
-- Generated: 2025-11-17

BEGIN;

-- Check current schema
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'fantasy_teams'
  AND column_name IN ('owner_id', 'user_id');

-- Rename owner_id to user_id if it exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'fantasy_teams' AND column_name = 'owner_id'
  ) THEN
    ALTER TABLE fantasy_teams RENAME COLUMN owner_id TO user_id;
    RAISE NOTICE 'Renamed owner_id to user_id';
  END IF;
END $$;

-- Verify the change
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'fantasy_teams'
  AND column_name = 'user_id';

COMMIT;
