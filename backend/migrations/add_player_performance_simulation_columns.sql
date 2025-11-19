-- Migration: Add columns for fantasy team simulation tracking
-- Date: 2025-11-19
-- Purpose: Add columns needed by simulate_live_teams.py

-- Add extended fantasy points tracking columns
ALTER TABLE player_performances
  ADD COLUMN IF NOT EXISTS base_fantasy_points DOUBLE PRECISION DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS multiplier_applied DOUBLE PRECISION DEFAULT 1.0,
  ADD COLUMN IF NOT EXISTS captain_multiplier DOUBLE PRECISION DEFAULT 1.0,
  ADD COLUMN IF NOT EXISTS final_fantasy_points DOUBLE PRECISION DEFAULT 0.0;

-- Add fantasy team context columns
ALTER TABLE player_performances
  ADD COLUMN IF NOT EXISTS fantasy_team_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS league_id VARCHAR(50),
  ADD COLUMN IF NOT EXISTS round_number INTEGER;

-- Add player role columns
ALTER TABLE player_performances
  ADD COLUMN IF NOT EXISTS is_captain BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS is_vice_captain BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS is_wicket_keeper BOOLEAN DEFAULT FALSE;

-- Add foreign key constraints
ALTER TABLE player_performances
  ADD CONSTRAINT IF NOT EXISTS fk_player_performances_fantasy_team
    FOREIGN KEY (fantasy_team_id) REFERENCES fantasy_teams(id) ON DELETE SET NULL;

ALTER TABLE player_performances
  ADD CONSTRAINT IF NOT EXISTS fk_player_performances_league
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE SET NULL;

-- Add indexes for query performance
CREATE INDEX IF NOT EXISTS idx_perf_fantasy_team ON player_performances(fantasy_team_id);
CREATE INDEX IF NOT EXISTS idx_perf_league ON player_performances(league_id);
CREATE INDEX IF NOT EXISTS idx_perf_round ON player_performances(round_number);
CREATE INDEX IF NOT EXISTS idx_perf_league_round ON player_performances(league_id, round_number);

-- Update existing rows to have default values
UPDATE player_performances
SET
  base_fantasy_points = COALESCE(base_fantasy_points, fantasy_points),
  multiplier_applied = COALESCE(multiplier_applied, 1.0),
  captain_multiplier = COALESCE(captain_multiplier, 1.0),
  final_fantasy_points = COALESCE(final_fantasy_points, fantasy_points),
  is_captain = COALESCE(is_captain, FALSE),
  is_vice_captain = COALESCE(is_vice_captain, FALSE),
  is_wicket_keeper = COALESCE(is_wicket_keeper, FALSE)
WHERE base_fantasy_points IS NULL
   OR multiplier_applied IS NULL
   OR captain_multiplier IS NULL
   OR final_fantasy_points IS NULL;

COMMIT;
