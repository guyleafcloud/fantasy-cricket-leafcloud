'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface League {
  id: string;
  name: string;
  description?: string;
  season_name: string;
  club_name: string;
  league_code: string;
  participants_count: number;
  max_participants: number;
  is_full: boolean;
  squad_size: number;
  transfers_per_season: number;
}

export default function BrowseLeaguesPage() {
  const router = useRouter();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null);
  const [teamName, setTeamName] = useState('');
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadLeagues();
  }, [router]);

  const loadLeagues = async () => {
    try {
      setLoading(true);
      const data = await apiClient.browsePublicLeagues();
      setLeagues(data);
    } catch (err: any) {
      setError('Failed to load leagues');
      if (err.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleJoinClick = (league: League) => {
    setSelectedLeague(league);
    setShowJoinModal(true);
    setTeamName('');
  };

  const handleJoinLeague = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeague) return;

    setJoining(true);
    setError('');

    try {
      // First join the league
      await apiClient.joinLeague(selectedLeague.league_code);

      // Then create a team
      const teamResponse = await apiClient.createFantasyTeam(
        selectedLeague.id,
        teamName
      );

      // Redirect to team builder
      router.push(`/teams/${teamResponse.team.id}/build`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join league');
    } finally {
      setJoining(false);
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
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Browse Leagues</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Join a league and start building your team</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Dashboard
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

        {leagues.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
            <div className="text-4xl mb-4">🏏</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No leagues available</h3>
            <p className="text-gray-500 dark:text-gray-400">Check back later or ask an admin to create a league!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {leagues.map((league) => (
              <div
                key={league.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow overflow-hidden"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                        {league.name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {league.season_name} • {league.club_name}
                      </p>
                    </div>
                    {league.is_full && (
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 dark:text-gray-400 rounded">
                        FULL
                      </span>
                    )}
                  </div>

                  {league.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                      {league.description}
                    </p>
                  )}

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Participants:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {league.participants_count} / {league.max_participants}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Squad Size:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {league.squad_size} players
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Transfers:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {league.transfers_per_season}/season
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleJoinClick(league)}
                    disabled={league.is_full}
                    className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                      league.is_full
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-cricket-green text-white hover:bg-green-800'
                    }`}
                  >
                    {league.is_full ? 'League Full' : 'Join League'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Join League Modal */}
      {showJoinModal && selectedLeague && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Join {selectedLeague.name}</h3>

            <form onSubmit={handleJoinLeague}>
              <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  You&apos;re about to join <strong>{selectedLeague.name}</strong> in the{' '}
                  {selectedLeague.season_name} season.
                </p>

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

              {error && (
                <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowJoinModal(false);
                    setSelectedLeague(null);
                    setError('');
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
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
