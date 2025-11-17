-- Drop old league columns that conflict with new schema
-- Generated: 2025-11-17

BEGIN;

-- Drop old columns that are no longer used
ALTER TABLE leagues DROP COLUMN IF EXISTS code CASCADE;
ALTER TABLE leagues DROP COLUMN IF EXISTS creator_id CASCADE;
ALTER TABLE leagues DROP COLUMN IF EXISTS max_members CASCADE;
ALTER TABLE leagues DROP COLUMN IF EXISTS is_private CASCADE;
ALTER TABLE leagues DROP COLUMN IF EXISTS season_start CASCADE;
ALTER TABLE leagues DROP COLUMN IF EXISTS season_end CASCADE;

-- Verify remaining schema
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'leagues'
ORDER BY ordinal_position;

COMMIT;
