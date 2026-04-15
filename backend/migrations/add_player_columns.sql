-- Migration: Add missing player columns to match code model
-- Date: 2026-04-15
-- Description: Adds columns required for multiplier calculation and roster management
--
-- CRITICAL: This migration is required for the multiplier calculator to function.
-- The code expects rl_team, role, prev_season_fantasy_points but these don't exist in production.

-- Step 1: Add new columns with appropriate defaults
ALTER TABLE players ADD COLUMN IF NOT EXISTS rl_team VARCHAR(50);
ALTER TABLE players ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'ALL_ROUNDER';
ALTER TABLE players ADD COLUMN IF NOT EXISTS prev_season_fantasy_points FLOAT;
ALTER TABLE players ADD COLUMN IF NOT EXISTS tier VARCHAR(50) DEFAULT 'HOOFDKLASSE';
ALTER TABLE players ADD COLUMN IF NOT EXISTS base_price INTEGER NOT NULL DEFAULT 100;
ALTER TABLE players ADD COLUMN IF NOT EXISTS current_price INTEGER NOT NULL DEFAULT 100;
ALTER TABLE players ADD COLUMN IF NOT EXISTS starting_multiplier FLOAT DEFAULT 1.0;
ALTER TABLE players ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Step 2: Migrate data from old columns to new columns (if old columns exist)
-- Migrate team_id to rl_team (convert FK to string team name)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'players' AND column_name = 'team_id'
    ) THEN
        UPDATE players
        SET rl_team = teams.name
        FROM teams
        WHERE players.team_id = teams.id
        AND players.rl_team IS NULL;
    END IF;
END $$;

-- Migrate player_type to role (if column exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'players' AND column_name = 'player_type'
    ) THEN
        UPDATE players
        SET role = UPPER(player_type)
        WHERE role = 'ALL_ROUNDER' -- Only update if still default
        AND player_type IS NOT NULL; -- Skip NULL values
    END IF;
END $$;

-- Step 3: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_players_rl_team ON players(rl_team);
CREATE INDEX IF NOT EXISTS idx_players_role ON players(role);
CREATE INDEX IF NOT EXISTS idx_players_is_active ON players(is_active);

-- Step 4: Verify migration
DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_name = 'players'
    AND column_name IN ('rl_team', 'role', 'prev_season_fantasy_points', 'tier',
                        'base_price', 'current_price', 'starting_multiplier');

    IF column_count < 7 THEN
        RAISE EXCEPTION 'Migration incomplete: Expected 7 new columns, found %', column_count;
    ELSE
        RAISE NOTICE 'Migration successful: All 7 columns added';
    END IF;
END $$;

-- Step 5: Display summary
SELECT
    COUNT(*) as total_players,
    COUNT(rl_team) as players_with_team,
    COUNT(DISTINCT rl_team) as unique_teams,
    COUNT(DISTINCT role) as unique_roles,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_players
FROM players;
