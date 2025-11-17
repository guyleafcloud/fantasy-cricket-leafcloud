-- Comprehensive Schema Alignment
-- Fix ALL schema mismatches found by comprehensive check
-- Generated: 2025-11-17

BEGIN;

-- ============================================================================
-- 1. PLAYER_PRICE_HISTORY - Rename columns to match model
-- ============================================================================
ALTER TABLE player_price_history RENAME COLUMN old_price TO old_value;
ALTER TABLE player_price_history RENAME COLUMN new_price TO new_value;
ALTER TABLE player_price_history RENAME COLUMN justification TO reason_details;

-- ============================================================================
-- 2. FANTASY_TEAMS - Add missing columns
-- ============================================================================
ALTER TABLE fantasy_teams ADD COLUMN IF NOT EXISTS budget_used DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE fantasy_teams ADD COLUMN IF NOT EXISTS is_finalized BOOLEAN DEFAULT FALSE;
ALTER TABLE fantasy_teams ADD COLUMN IF NOT EXISTS extra_transfers_granted INTEGER DEFAULT 0;
ALTER TABLE fantasy_teams ADD COLUMN IF NOT EXISTS rank INTEGER;
ALTER TABLE fantasy_teams ADD COLUMN IF NOT EXISTS transfers_used INTEGER DEFAULT 0;

-- Note: Keep captain_id and vice_captain_id as they're used by the database

-- ============================================================================
-- 3. FANTASY_TEAM_PLAYERS - Add missing columns
-- ============================================================================
-- Add id column first (not as primary key yet, table might have data)
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS id VARCHAR(50) DEFAULT gen_random_uuid()::text;

-- Add other columns
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS is_captain BOOLEAN DEFAULT FALSE;
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS is_vice_captain BOOLEAN DEFAULT FALSE;
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS is_wicket_keeper BOOLEAN DEFAULT FALSE;
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS position INTEGER;
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS purchase_value DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS total_points DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE fantasy_team_players ADD COLUMN IF NOT EXISTS added_at TIMESTAMP DEFAULT NOW();

-- Make id NOT NULL and PRIMARY KEY if it doesn't have one
DO $$
BEGIN
  -- First make sure all rows have an id
  UPDATE fantasy_team_players SET id = gen_random_uuid()::text WHERE id IS NULL;

  -- Make id NOT NULL
  ALTER TABLE fantasy_team_players ALTER COLUMN id SET NOT NULL;

  -- Add primary key constraint if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fantasy_team_players_pkey'
  ) THEN
    ALTER TABLE fantasy_team_players ADD CONSTRAINT fantasy_team_players_pkey PRIMARY KEY (id);
  END IF;
END $$;

-- ============================================================================
-- 4. MATCHES - Add missing columns to support model
-- ============================================================================
ALTER TABLE matches ADD COLUMN IF NOT EXISTS season_id VARCHAR(50);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS club_id VARCHAR(50);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS opponent VARCHAR(200);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS match_title VARCHAR(300);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS matchcentre_id VARCHAR(100);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS scorecard_url VARCHAR(500);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS period_id VARCHAR(100);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS result VARCHAR(50);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS match_type VARCHAR(50) DEFAULT 'league';
ALTER TABLE matches ADD COLUMN IF NOT EXISTS is_processed BOOLEAN DEFAULT FALSE;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS raw_scorecard_data JSONB;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add foreign keys if they don't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'matches_season_id_fkey'
  ) THEN
    ALTER TABLE matches ADD CONSTRAINT matches_season_id_fkey FOREIGN KEY (season_id) REFERENCES seasons(id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'matches_club_id_fkey'
  ) THEN
    ALTER TABLE matches ADD CONSTRAINT matches_club_id_fkey FOREIGN KEY (club_id) REFERENCES clubs(id);
  END IF;
END $$;

-- Note: Keep home_club_id, away_club_id, scores, wickets as they're used by database

-- ============================================================================
-- 5. PLAYER_PERFORMANCES - Add missing columns
-- ============================================================================
ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS batting_strike_rate DOUBLE PRECISION;
ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS bowling_economy DOUBLE PRECISION;
ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS dismissal_type VARCHAR(50);
ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS points_breakdown JSONB;

-- Note: Keep extra fantasy-related columns as they're used by database

COMMIT;

-- Verification queries
SELECT 'player_price_history columns:' as check_result;
SELECT column_name FROM information_schema.columns WHERE table_name = 'player_price_history' ORDER BY ordinal_position;

SELECT 'fantasy_teams columns:' as check_result;
SELECT column_name FROM information_schema.columns WHERE table_name = 'fantasy_teams' ORDER BY ordinal_position;

SELECT 'fantasy_team_players columns:' as check_result;
SELECT column_name FROM information_schema.columns WHERE table_name = 'fantasy_team_players' ORDER BY ordinal_position;

SELECT 'matches columns:' as check_result;
SELECT column_name FROM information_schema.columns WHERE table_name = 'matches' ORDER BY ordinal_position;

SELECT 'player_performances columns:' as check_result;
SELECT column_name FROM information_schema.columns WHERE table_name = 'player_performances' ORDER BY ordinal_position;
