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
