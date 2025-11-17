import axios, { AxiosInstance } from 'axios';
import type { Player, Team, Club, Season, LoginRequest, LoginResponse } from '@/types';

// Use relative URLs - Next.js rewrites will proxy to the correct API
const API_BASE_URL = '';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include token
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('admin_token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('admin_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('admin_token');
    }
  }

  // Auth endpoints
  async register(data: { email: string; password: string; full_name: string; turnstile_token: string }): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/api/auth/register', data);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async login(credentials: LoginRequest & { turnstile_token: string }): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/api/auth/login', credentials);
    this.setToken(response.data.access_token);
    return response.data;
  }

  logout() {
    this.clearToken();
  }

  async getMe(): Promise<any> {
    const response = await this.client.get('/api/auth/me');
    return response.data;
  }

  // Admin endpoints
  async getClubs(): Promise<Club[]> {
    const response = await this.client.get('/api/admin/clubs');
    return response.data.clubs || [];
  }

  async getPlayers(clubId: string, filters?: {
    team_name?: string;
    min_multiplier?: number;
    max_multiplier?: number;
  }): Promise<{ club_id: string; total_players: number; players: Player[] }> {
    const params = new URLSearchParams();
    if (filters?.team_name) params.append('team_name', filters.team_name);
    if (filters?.min_multiplier) params.append('min_multiplier', filters.min_multiplier.toString());
    if (filters?.max_multiplier) params.append('max_multiplier', filters.max_multiplier.toString());

    const response = await this.client.get(`/api/admin/clubs/${clubId}/players?${params}`);
    return response.data;
  }

  async updatePlayer(playerId: string, updates: {
    name?: string;
    team_id?: string;
    player_type?: string;
    multiplier?: number;
    stats?: any;
  }): Promise<Player> {
    const response = await this.client.put(`/api/admin/players/${playerId}`, updates);
    return response.data.player;
  }

  async addPlayer(clubId: string, player: {
    name: string;
    team_id: string;
    player_type?: string;
    multiplier: number;
    stats?: any;
  }): Promise<Player> {
    const response = await this.client.post(`/api/admin/clubs/${clubId}/players`, player);
    return response.data.player;
  }

  async deletePlayer(playerId: string): Promise<void> {
    await this.client.delete(`/api/admin/players/${playerId}`);
  }

  async getTeams(clubId: string): Promise<Team[]> {
    const response = await this.client.get(`/api/admin/clubs/${clubId}/teams`);
    return response.data.teams || [];
  }

  async getSeasons(): Promise<Season[]> {
    const response = await this.client.get('/api/admin/seasons');
    return response.data.seasons || [];
  }

  // User management endpoints
  async getUsers(): Promise<any[]> {
    const response = await this.client.get('/api/admin/users');
    return response.data.users || [];
  }

  async promoteUser(userId: string): Promise<any> {
    const response = await this.client.post(`/api/admin/users/${userId}/promote`);
    return response.data;
  }

  async demoteUser(userId: string): Promise<any> {
    const response = await this.client.post(`/api/admin/users/${userId}/demote`);
    return response.data;
  }

  async resetUserPassword(userId: string, newPassword: string): Promise<any> {
    const response = await this.client.post(`/api/admin/users/${userId}/reset-password`, {
      new_password: newPassword
    });
    return response.data;
  }

  async toggleAdminMode(): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/api/auth/toggle-mode');
    this.setToken(response.data.access_token);
    return response.data;
  }

  // User-facing league endpoints
  async browsePublicLeagues(): Promise<any[]> {
    const response = await this.client.get('/api/user/leagues/public');
    return response.data.leagues || [];
  }

  async joinLeague(leagueCode: string): Promise<any> {
    const response = await this.client.post('/api/user/leagues/join', {
      league_code: leagueCode
    });
    return response.data;
  }

  // User-facing team endpoints
  async createFantasyTeam(leagueId: string, teamName: string): Promise<any> {
    const response = await this.client.post('/api/user/teams', {
      league_id: leagueId,
      team_name: teamName
    });
    return response.data;
  }

  async getMyTeams(): Promise<any[]> {
    const response = await this.client.get('/api/user/teams');
    return response.data.teams || [];
  }

  async getTeamDetails(teamId: string): Promise<any> {
    const response = await this.client.get(`/api/user/teams/${teamId}`);
    return response.data;
  }

  async getAvailablePlayers(teamId: string): Promise<any> {
    const response = await this.client.get(`/api/user/teams/${teamId}/available-players`);
    return response.data;
  }

  async addPlayerToTeam(teamId: string, playerId: string, isCaptain: boolean = false, isViceCaptain: boolean = false, isWicketKeeper: boolean = false): Promise<any> {
    const response = await this.client.post(`/api/user/teams/${teamId}/players`, {
      player_id: playerId,
      is_captain: isCaptain,
      is_vice_captain: isViceCaptain,
      is_wicket_keeper: isWicketKeeper
    });
    return response.data;
  }

  async removePlayerFromTeam(teamId: string, playerId: string): Promise<any> {
    const response = await this.client.delete(`/api/user/teams/${teamId}/players/${playerId}`);
    return response.data;
  }

  async finalizeTeam(teamId: string): Promise<any> {
    const response = await this.client.post(`/api/user/teams/${teamId}/finalize`);
    return response.data;
  }

  async transferPlayer(teamId: string, playerOutId: string, playerInId: string): Promise<any> {
    const response = await this.client.post(`/api/user/teams/${teamId}/transfer`, {
      player_out_id: playerOutId,
      player_in_id: playerInId
    });
    return response.data;
  }

  // Admin delete operations
  async deleteUser(userId: string): Promise<any> {
    const response = await this.client.delete(`/api/admin/users/${userId}`);
    return response.data;
  }

  async deleteTeam(teamId: string): Promise<any> {
    const response = await this.client.delete(`/api/admin/teams/${teamId}`);
    return response.data;
  }

  async deleteLeague(leagueId: string): Promise<any> {
    const response = await this.client.delete(`/api/admin/leagues/${leagueId}`);
    return response.data;
  }
}

export const apiClient = new ApiClient();
