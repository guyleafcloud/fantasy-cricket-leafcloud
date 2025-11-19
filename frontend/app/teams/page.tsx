'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface Team {
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

export default function MyTeamsPage() {
  const router = useRouter();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadTeams();
  }, [router]);

  const loadTeams = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getMyTeams();
      setTeams(data);
    } catch (err: any) {
      setError('Failed to load teams');
      if (err.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cricket-green"></div>
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
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">My Teams</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {teams.length} {teams.length === 1 ? 'team' : 'teams'}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Dashboard
              </button>
              <button
                onClick={() => router.push('/leagues')}
                className="px-4 py-2 text-sm font-medium text-white bg-cricket-green rounded-md hover:bg-green-800"
              >
                Join League
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {teams.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <div className="text-4xl mb-4">🏏</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No teams yet</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              Join a league to create your first fantasy cricket team!
            </p>
            <button
              onClick={() => router.push('/leagues')}
              className="px-6 py-3 bg-cricket-green text-white rounded-md hover:bg-green-800 font-medium"
            >
              Browse Leagues
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teams.map((team) => (
              <div
                key={team.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow overflow-hidden cursor-pointer"
                onClick={() => {
                  if (team.is_finalized) {
                    // View team details (could create a detail page)
                    router.push(`/teams/${team.id}`);
                  } else {
                    // Continue building team
                    router.push(`/teams/${team.id}/build`);
                  }
                }}
              >
                <div className="p-6">
                  {/* Team Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                        {team.team_name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {team.league_name}
                      </p>
                      <p className="text-xs text-gray-400">
                        {team.season_name} • {team.club_name}
                      </p>
                    </div>
                    {team.is_finalized ? (
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                        Building
                      </span>
                    )}
                  </div>

                  {/* Stats */}
                  {team.is_finalized ? (
                    <div className="space-y-3 mb-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Rank:</span>
                        <span className="text-lg font-bold text-cricket-green">
                          {team.rank ? `#${team.rank}` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Total Points:</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">
                          {team.total_points.toFixed(0)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Transfers Left:</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {team.transfers_remaining}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3 mb-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Squad:</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {team.players_count} / 11 players
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-cricket-green h-2 rounded-full"
                          style={{
                            width: `${(team.players_count / 11) * 100}%`
                          }}
                        ></div>
                      </div>
                    </div>
                  )}

                  {/* Action Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (team.is_finalized) {
                        router.push(`/teams/${team.id}`);
                      } else {
                        router.push(`/teams/${team.id}/build`);
                      }
                    }}
                    className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                      team.is_finalized
                        ? 'bg-gray-100 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                        : 'bg-cricket-green text-white hover:bg-green-800'
                    }`}
                  >
                    {team.is_finalized ? 'View Team' : 'Continue Building'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
