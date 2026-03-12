export interface Player {
  id: string;
  name: string;
  team_id: string;
  team_name: string;
  team_level: string;
  multiplier: number;
  multiplier_updated_at: string;
  stats: PlayerStats;
  player_type?: string;
  created_at: string;
}

export interface PlayerStats {
  matches?: number;
  runs?: number;
  batting_avg?: number;
  strike_rate?: number;
  wickets?: number;
  bowling_avg?: number;
  economy?: number;
  catches?: number;
  run_outs?: number;
  fours?: number;
  sixes?: number;
  fifties?: number;
  hundreds?: number;
  five_wicket_hauls?: number;
  maidens?: number;
}

export interface Team {
  id: string;
  name: string;
  level: string;
  tier_type: string;
  value_multiplier?: number;
  points_multiplier?: number;
}

export interface Club {
  id: string;
  name: string;
  full_name: string;
  season_id: string;
}

export interface Season {
  id: string;
  year: string;
  name: string;
  is_active: boolean;
  registration_open: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
  turnstile_token?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    email: string;
    full_name: string;
    is_admin: boolean;
  };
}

export interface ApiResponse<T> {
  message?: string;
  [key: string]: any;
}

// ============================================================================
// DETAILED TEAM STATS TYPES (for enhanced leaderboard modal)
// ============================================================================

export interface PlayerBattingStats {
  runs: number;
  average: number;
  strike_rate: number;
  balls_faced: number;
  fours: number;
  sixes: number;
  fifties: number;
  hundreds: number;
  ducks: number;
  highest_score: number;
}

export interface PlayerBowlingStats {
  wickets: number;
  overs: number;
  maidens: number;
  runs_conceded: number;
  average: number | null;
  economy: number | null;
  five_wicket_hauls: number;
}

export interface PlayerFieldingStats {
  catches: number;
  run_outs: number;
  stumpings: number;
}

export interface MatchPerformance {
  match_id: string;
  points: number;
  runs: number;
  wickets: number;
}

export interface RecentForm {
  matches: MatchPerformance[];
  last_n_average: number;
  trend: 'improving' | 'declining' | 'stable';
}

export interface MultiplierInfo {
  starting_multiplier: number;
  current_multiplier: number;
  drift: number;
  status: 'strengthening' | 'weakening' | 'stable';
}

export interface PointsBreakdown {
  batting_points: number;
  bowling_points: number;
  fielding_points: number;
}

export interface DetailedPlayerStats {
  player_id: string;
  player_name: string;
  club_name: string;
  player_role: string;
  is_captain: boolean;
  is_vice_captain: boolean;
  is_wicket_keeper: boolean;
  total_points: number;
  matches_played: number;
  batting: PlayerBattingStats;
  bowling: PlayerBowlingStats;
  fielding: PlayerFieldingStats;
  multiplier_info: MultiplierInfo;
  recent_form: RecentForm;
  points_breakdown: PointsBreakdown;
}

export interface DetailedTeamStats {
  team_id: string;
  team_name: string;
  owner_name: string;
  total_points: number;
  weekly_points: number;
  squad_size: number;
  players: DetailedPlayerStats[];
}
