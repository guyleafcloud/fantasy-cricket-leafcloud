-- Migration: Add prev_season_fantasy_points to players table
-- Purpose: Store previous season fantasy points for multiplier calculation
-- Date: 2025-12-19

-- Add column for previous season fantasy points
ALTER TABLE players
ADD COLUMN IF NOT EXISTS prev_season_fantasy_points FLOAT DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN players.prev_season_fantasy_points IS 'Total fantasy points from previous season, used for calculating current season multipliers';
