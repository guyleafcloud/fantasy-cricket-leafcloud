-- Migration: Add player_performances table to track individual player stats per round
-- Created: 2025-01-17

CREATE TABLE IF NOT EXISTS player_performances (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    player_id VARCHAR(50) NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    fantasy_team_id VARCHAR(50) REFERENCES fantasy_teams(id) ON DELETE SET NULL,
    league_id VARCHAR(50) NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,

    -- Round/Match tracking
    round_number INTEGER NOT NULL,
    match_date TIMESTAMP,

    -- Batting stats
    runs INTEGER DEFAULT 0,
    balls_faced INTEGER DEFAULT 0,
    is_out BOOLEAN DEFAULT FALSE,

    -- Bowling stats
    wickets INTEGER DEFAULT 0,
    overs DOUBLE PRECISION DEFAULT 0,
    runs_conceded INTEGER DEFAULT 0,
    maidens INTEGER DEFAULT 0,

    -- Fielding stats
    catches INTEGER DEFAULT 0,
    stumpings INTEGER DEFAULT 0,
    runouts INTEGER DEFAULT 0,

    -- Fantasy points
    base_fantasy_points DOUBLE PRECISION DEFAULT 0,
    multiplier_applied DOUBLE PRECISION DEFAULT 1.0,
    captain_multiplier DOUBLE PRECISION DEFAULT 1.0,
    final_fantasy_points DOUBLE PRECISION DEFAULT 0,

    -- Metadata
    is_captain BOOLEAN DEFAULT FALSE,
    is_vice_captain BOOLEAN DEFAULT FALSE,
    is_wicket_keeper BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ensure unique performance per player per round per league
    UNIQUE(player_id, league_id, round_number)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_player_performances_player_id ON player_performances(player_id);
CREATE INDEX IF NOT EXISTS idx_player_performances_fantasy_team_id ON player_performances(fantasy_team_id);
CREATE INDEX IF NOT EXISTS idx_player_performances_league_round ON player_performances(league_id, round_number);
CREATE INDEX IF NOT EXISTS idx_player_performances_points ON player_performances(final_fantasy_points DESC);

-- Comments
COMMENT ON TABLE player_performances IS 'Stores individual player performance data for each round/match';
COMMENT ON COLUMN player_performances.round_number IS 'Week/round number in the season (1, 2, 3, ...)';
COMMENT ON COLUMN player_performances.base_fantasy_points IS 'Points before any multipliers';
COMMENT ON COLUMN player_performances.multiplier_applied IS 'Player skill multiplier (0.69-5.0)';
COMMENT ON COLUMN player_performances.captain_multiplier IS 'Captain/VC bonus (1.0, 1.5, or 2.0)';
COMMENT ON COLUMN player_performances.final_fantasy_points IS 'Final points after all multipliers';
