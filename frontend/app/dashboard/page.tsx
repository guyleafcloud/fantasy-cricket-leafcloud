'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_verified: boolean;
  created_at: string | null;
  last_login: string | null;
}

interface TeamData {
  id: string;
  team_name: string;
  league_id: string;
  league_name: string;
  season_name: string;
  club_name: string;
  total_points: number;
  rank: number | null;
  is_finalized: boolean;
  players_count: number;
  budget_remaining: number;
  budget_used: number;
  transfers_used: number;
  transfers_remaining: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [teams, setTeams] = useState<TeamData[]>([]);
  const [loading, setLoading] = useState(true);
  const [teamsLoading, setTeamsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [leagueCode, setLeagueCode] = useState('');
  const [teamName, setTeamName] = useState('');
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState('');

  useEffect(() => {
    loadUserProfile();
    loadMyTeams();
  }, []);

  const loadUserProfile = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const userData = await apiClient.getMe();
      setUser(userData);
    } catch (err: any) {
      setError('Failed to load profile');
      if (err.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadMyTeams = async () => {
    try {
      setTeamsLoading(true);
      const teamsData = await apiClient.getMyTeams();
      setTeams(teamsData);
    } catch (err: any) {
      console.error('Failed to load teams:', err);
      // Don't show error - just leave teams empty
    } finally {
      setTeamsLoading(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/login');
  };

  const handleToggleMode = async () => {
    try {
      const response = await apiClient.toggleAdminMode();
      // After toggling to admin mode, redirect to admin dashboard
      router.push('/admin');
    } catch (err: any) {
      // If toggle fails, user might not be an admin - ignore silently
      console.error('Failed to toggle mode:', err);
    }
  };

  const handleJoinWithCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setJoining(true);
    setJoinError('');

    try {
      // Join league
      const joinResponse = await apiClient.joinLeague(leagueCode.toUpperCase());

      // Create team
      const teamResponse = await apiClient.createFantasyTeam(
        joinResponse.league.id,
        teamName
      );

      // Redirect to team builder
      router.push(`/teams/${teamResponse.team.id}/build`);
    } catch (err: any) {
      setJoinError(err.response?.data?.detail || 'Failed to join league');
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-gray-600 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-red-600 dark:text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Fantasy Cricket</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Welcome back, {user?.full_name}!</p>
            </div>
            <div className="flex gap-3">
              {user?.is_admin && (
                <button
                  onClick={handleToggleMode}
                  className="px-4 py-2 text-sm font-medium text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-900 border border-purple-300 dark:border-purple-700 rounded-md hover:bg-purple-100 dark:hover:bg-purple-800"
                >
                  Switch to Admin Mode
                </button>
              )}
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => router.push('/leagues')}
              className="p-6 bg-white dark:bg-gray-800 border-2 border-cricket-green rounded-lg hover:bg-green-50 dark:hover:bg-green-900 text-left transition-colors"
            >
              <div className="text-cricket-green font-semibold mb-2">Browse Leagues</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Find and join public leagues</div>
            </button>
            <button
              onClick={() => setShowJoinModal(true)}
              className="p-6 bg-white dark:bg-gray-800 border-2 border-blue-500 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900 text-left transition-colors"
            >
              <div className="text-blue-600 font-semibold mb-2">Join with Code</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Enter a league invite code</div>
            </button>
            <button
              onClick={() => router.push('/teams')}
              className="p-6 bg-white dark:bg-gray-800 border-2 border-purple-500 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900 text-left transition-colors"
            >
              <div className="text-purple-600 font-semibold mb-2">My Teams</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">View and manage your teams</div>
            </button>
            <button
              onClick={() => router.push('/how-to-play')}
              className="p-6 bg-white dark:bg-gray-800 border-2 border-orange-500 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900 text-left transition-colors"
            >
              <div className="text-orange-600 font-semibold mb-2">📖 How to Play</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Learn scoring rules & strategy</div>
            </button>
          </div>
        </div>

        {/* My Leagues Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">My Leagues</h2>
          {teamsLoading ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                Loading your leagues...
              </div>
            </div>
          ) : teams.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                <div className="text-4xl mb-2">🏏</div>
                <p>You haven&apos;t joined any leagues yet</p>
                <p className="text-sm mt-2">Get started by browsing available leagues or joining with a code!</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {teams.map((team) => (
                <div
                  key={team.id}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow border border-gray-200 dark:border-gray-700"
                >
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-1">
                          {team.league_name}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {team.season_name}
                        </p>
                      </div>
                      {team.rank && (
                        <div className="bg-cricket-green text-white px-3 py-1 rounded-full text-sm font-medium">
                          #{team.rank}
                        </div>
                      )}
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Team:</span>
                        <span className="font-medium text-gray-900 dark:text-white">{team.team_name}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Points:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {team.total_points?.toFixed(1) || '0.0'}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Players:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {team.players_count}/11
                        </span>
                      </div>
                      {!team.is_finalized && team.players_count < 11 && (
                        <div className="text-xs text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900 px-2 py-1 rounded">
                          ⚠️ Team incomplete
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => router.push(team.is_finalized ? `/teams/${team.id}` : `/teams/${team.id}/build`)}
                        className="flex-1 px-3 py-2 text-sm bg-cricket-green text-white rounded hover:bg-green-800"
                      >
                        {team.is_finalized ? 'View Team' : 'Build Team'}
                      </button>
                      <button
                        onClick={() => router.push(`/leagues/${team.league_id}/leaderboard`)}
                        className="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                      >
                        Leaderboard
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity Section */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            {teamsLoading ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                Loading activity...
              </div>
            ) : teams.length === 0 ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                <div className="text-4xl mb-2">📊</div>
                <p>No recent activity</p>
                <p className="text-sm mt-2">Your league updates and team changes will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {teams.slice(0, 5).map((team) => (
                  <div
                    key={team.id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="text-2xl">🏏</div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {team.league_name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {team.team_name} • {team.total_points?.toFixed(1) || '0.0'} pts
                          {team.rank && ` • Rank #${team.rank}`}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => router.push(`/teams/${team.id}/build`)}
                      className="text-sm text-cricket-green hover:text-green-800"
                    >
                      View →
                    </button>
                  </div>
                ))}
                {teams.length > 5 && (
                  <p className="text-center text-sm text-gray-500 dark:text-gray-400 pt-2">
                    Showing 5 most recent teams
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Join with Code Modal */}
      {showJoinModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Join League with Code</h3>

            <form onSubmit={handleJoinWithCode}>
              <div className="space-y-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    League Code *
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-cricket-green focus:border-transparent uppercase"
                    placeholder="Enter 6-character code"
                    maxLength={6}
                    value={leagueCode}
                    onChange={(e) => setLeagueCode(e.target.value.toUpperCase())}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Ask your league admin for the join code
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Team Name *
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-cricket-green focus:border-transparent"
                    placeholder="Enter your team name"
                    value={teamName}
                    onChange={(e) => setTeamName(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Choose a unique name for your fantasy team
                  </p>
                </div>
              </div>

              {joinError && (
                <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-3">
                  <p className="text-sm text-red-700">{joinError}</p>
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowJoinModal(false);
                    setLeagueCode('');
                    setTeamName('');
                    setJoinError('');
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:bg-gray-900"
                  disabled={joining}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800 disabled:opacity-50"
                  disabled={joining}
                >
                  {joining ? 'Joining...' : 'Join & Create Team'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
