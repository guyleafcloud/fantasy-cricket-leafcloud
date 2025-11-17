-- Fix leagues table schema to match League model
-- Generated: 2025-11-17

BEGIN;

-- Add missing columns
ALTER TABLE leagues
  ADD COLUMN IF NOT EXISTS season_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS club_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS description TEXT,
  ADD COLUMN IF NOT EXISTS league_code VARCHAR(20),
  ADD COLUMN IF NOT EXISTS squad_size INTEGER DEFAULT 11,
  ADD COLUMN IF NOT EXISTS budget DOUBLE PRECISION DEFAULT 500.0,
  ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'EUR',
  ADD COLUMN IF NOT EXISTS transfers_per_season INTEGER DEFAULT 4,
  ADD COLUMN IF NOT EXISTS min_players_per_team INTEGER DEFAULT 1,
  ADD COLUMN IF NOT EXISTS max_players_per_team INTEGER DEFAULT 2,
  ADD COLUMN IF NOT EXISTS require_from_each_team BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS min_batsmen INTEGER DEFAULT 3,
  ADD COLUMN IF NOT EXISTS min_bowlers INTEGER DEFAULT 3,
  ADD COLUMN IF NOT EXISTS require_wicket_keeper BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS max_participants INTEGER DEFAULT 100,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS created_by VARCHAR(50);

-- Copy data from old columns to new columns
UPDATE leagues
SET
  league_code = code,
  created_by = creator_id,
  max_participants = COALESCE(max_members, 100),
  is_public = NOT COALESCE(is_private, FALSE),
  updated_at = created_at
WHERE league_code IS NULL;

-- Make league_code unique if not already
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'leagues_league_code_key'
  ) THEN
    ALTER TABLE leagues ADD CONSTRAINT leagues_league_code_key UNIQUE (league_code);
  END IF;
END $$;

-- Add foreign key constraints
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'leagues_season_id_fkey'
  ) THEN
    ALTER TABLE leagues
    ADD CONSTRAINT leagues_season_id_fkey
    FOREIGN KEY (season_id) REFERENCES seasons(id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'leagues_club_id_fkey'
  ) THEN
    ALTER TABLE leagues
    ADD CONSTRAINT leagues_club_id_fkey
    FOREIGN KEY (club_id) REFERENCES clubs(id);
  END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_league_season ON leagues(season_id);
CREATE INDEX IF NOT EXISTS idx_league_club ON leagues(club_id);
CREATE INDEX IF NOT EXISTS idx_league_code ON leagues(league_code);

COMMIT;

-- Display results
SELECT
  id,
  name,
  league_code,
  season_id,
  club_id,
  created_by,
  max_participants,
  is_public
FROM leagues;
