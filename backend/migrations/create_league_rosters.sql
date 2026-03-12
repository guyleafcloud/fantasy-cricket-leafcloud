-- Migration: Create league_rosters table
-- Purpose: Enable league-specific player rosters
-- Date: 2025-12-19

-- Create league_rosters junction table
CREATE TABLE IF NOT EXISTS league_rosters (
    id VARCHAR(50) PRIMARY KEY,
    league_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    included_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_league_roster_league FOREIGN KEY (league_id)
        REFERENCES leagues(id) ON DELETE CASCADE,
    CONSTRAINT fk_league_roster_player FOREIGN KEY (player_id)
        REFERENCES players(id) ON DELETE CASCADE,
    CONSTRAINT unique_league_player UNIQUE (league_id, player_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_league_roster_league ON league_rosters(league_id);
CREATE INDEX IF NOT EXISTS idx_league_roster_player ON league_rosters(player_id);

-- Add comments for documentation
COMMENT ON TABLE league_rosters IS 'Junction table linking leagues to their available players';
COMMENT ON COLUMN league_rosters.league_id IS 'Foreign key to leagues table';
COMMENT ON COLUMN league_rosters.player_id IS 'Foreign key to players table';
COMMENT ON COLUMN league_rosters.included_at IS 'When player was added to league roster';
