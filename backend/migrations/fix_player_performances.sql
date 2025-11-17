-- Migration: Fix player_performances table to match code expectations
-- Date: 2025-11-17
-- Issue: Table missing critical columns for fantasy points tracking

-- Add missing columns for fantasy points breakdown
ALTER TABLE player_performances
  ADD COLUMN IF NOT EXISTS fantasy_team_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS league_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS round_number INTEGER,
  ADD COLUMN IF NOT EXISTS match_date TIMESTAMP,
  ADD COLUMN IF NOT EXISTS base_fantasy_points DOUBLE PRECISION DEFAULT 0,
  ADD COLUMN IF NOT EXISTS multiplier_applied DOUBLE PRECISION DEFAULT 1.0,
  ADD COLUMN IF NOT EXISTS captain_multiplier DOUBLE PRECISION DEFAULT 1.0,
  ADD COLUMN IF NOT EXISTS final_fantasy_points DOUBLE PRECISION DEFAULT 0,
  ADD COLUMN IF NOT EXISTS is_captain BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS is_vice_captain BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS is_wicket_keeper BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Add foreign key constraints
ALTER TABLE player_performances
  DROP CONSTRAINT IF EXISTS fk_player_performances_fantasy_team,
  ADD CONSTRAINT fk_player_performances_fantasy_team
    FOREIGN KEY (fantasy_team_id) REFERENCES fantasy_teams(id) ON DELETE SET NULL;

ALTER TABLE player_performances
  DROP CONSTRAINT IF EXISTS fk_player_performances_league,
  ADD CONSTRAINT fk_player_performances_league
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_performances_fantasy_team_id
  ON player_performances(fantasy_team_id);

CREATE INDEX IF NOT EXISTS idx_player_performances_league_round
  ON player_performances(league_id, round_number);

CREATE INDEX IF NOT EXISTS idx_player_performances_final_points
  ON player_performances(final_fantasy_points DESC);

-- Add unique constraint for player per round per league
-- First drop any conflicting constraints
ALTER TABLE player_performances
  DROP CONSTRAINT IF EXISTS player_performances_player_id_league_id_round_number_key;

-- Then add the new one (only if league_id and round_number are not null)
CREATE UNIQUE INDEX IF NOT EXISTS idx_player_perf_unique
  ON player_performances(player_id, league_id, round_number)
  WHERE league_id IS NOT NULL AND round_number IS NOT NULL;

-- Update final_fantasy_points for existing records (calculate from base fantasy_points * 1.0)
UPDATE player_performances
SET final_fantasy_points = COALESCE(fantasy_points, 0)
WHERE final_fantasy_points = 0 AND fantasy_points IS NOT NULL;

-- Comments
COMMENT ON COLUMN player_performances.base_fantasy_points IS 'Points before any multipliers (from performance only)';
COMMENT ON COLUMN player_performances.multiplier_applied IS 'Player skill multiplier (0.69-5.0 range)';
COMMENT ON COLUMN player_performances.captain_multiplier IS 'Captain/VC bonus (1.0, 1.5, or 2.0)';
COMMENT ON COLUMN player_performances.final_fantasy_points IS 'Final points: base × player_multiplier × captain_multiplier';
COMMENT ON COLUMN player_performances.is_captain IS 'True if player was captain for this performance';
COMMENT ON COLUMN player_performances.is_vice_captain IS 'True if player was vice captain for this performance';
COMMENT ON COLUMN player_performances.is_wicket_keeper IS 'True if player had wicketkeeper role (2x catch bonus)';
COMMENT ON COLUMN player_performances.round_number IS 'Week/round number in the season (1, 2, 3, ...)';
