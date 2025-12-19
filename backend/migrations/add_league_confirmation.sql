-- Migration: Add League Confirmation & Status Management
-- Purpose: Enable league lifecycle (draft → active → locked → completed)
-- Date: 2025-12-19

-- Add league status and frozen rules fields
ALTER TABLE leagues
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft',
ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS frozen_squad_size INTEGER,
ADD COLUMN IF NOT EXISTS frozen_transfers_per_season INTEGER,
ADD COLUMN IF NOT EXISTS frozen_min_batsmen INTEGER,
ADD COLUMN IF NOT EXISTS frozen_min_bowlers INTEGER,
ADD COLUMN IF NOT EXISTS frozen_require_wicket_keeper BOOLEAN,
ADD COLUMN IF NOT EXISTS frozen_max_players_per_team INTEGER,
ADD COLUMN IF NOT EXISTS frozen_require_from_each_team BOOLEAN,
ADD COLUMN IF NOT EXISTS multipliers_snapshot JSON,
ADD COLUMN IF NOT EXISTS multipliers_frozen_at TIMESTAMP;

-- Add team finalization timestamp
ALTER TABLE fantasy_teams
ADD COLUMN IF NOT EXISTS finalized_at TIMESTAMP;

-- Update existing leagues to 'active' status (backward compatibility)
UPDATE leagues
SET status = 'active'
WHERE status IS NULL OR status = '';

-- Add index on league status for filtering
CREATE INDEX IF NOT EXISTS idx_league_status ON leagues(status);

-- Add comments for documentation
COMMENT ON COLUMN leagues.status IS 'League lifecycle status: draft (setup), active (accepting teams), locked (season started), completed (ended)';
COMMENT ON COLUMN leagues.confirmed_at IS 'When admin confirmed league and froze rules';
COMMENT ON COLUMN leagues.frozen_squad_size IS 'Frozen copy of squad_size at confirmation (prevents mid-season changes)';
COMMENT ON COLUMN leagues.multipliers_snapshot IS 'JSON snapshot of player multipliers at confirmation {player_id: multiplier}';
COMMENT ON COLUMN fantasy_teams.finalized_at IS 'When user finalized their team (locked in for season)';
