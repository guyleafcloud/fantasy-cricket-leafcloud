'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface Season {
  id: string;
  year: string;
  name: string;
  is_active: boolean;
}

interface Club {
  id: string;
  name: string;
  full_name: string;
}

interface League {
  id: string;
  season_id: string;
  season_name: string;
  club_id: string;
  club_name: string;
  name: string;
  description?: string;
  league_code: string;
  squad_size: number;
  transfers_per_season: number;
  require_from_each_team: boolean;
  is_public: boolean;
  participants_count: number;
  max_participants: number;
  created_at: string;
}

export default function LeaguesPage() {
  const router = useRouter();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deleteLeagueId, setDeleteLeagueId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const [formData, setFormData] = useState({
    season_id: '',
    club_id: '',
    name: '',
    description: '',
    squad_size: 11,
    transfers_per_season: 4,
    require_from_each_team: true,
    is_public: true,
    max_participants: 100,
  });

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load clubs
      const clubsData = await apiClient.getClubs();
      setClubs(clubsData);

      // Set default to first club if available
      if (clubsData.length > 0 && !formData.club_id) {
        setFormData(prev => ({ ...prev, club_id: clubsData[0].id }));
      }

      // Load seasons
      const seasonsResponse = await fetch('/api/admin/seasons', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (seasonsResponse.ok) {
        const seasonsData = await seasonsResponse.json();
        setSeasons(seasonsData.seasons || []);

        // Set default to active season if available
        const activeSeason = (seasonsData.seasons || []).find((s: Season) => s.is_active);
        if (activeSeason && !formData.season_id) {
          setFormData(prev => ({ ...prev, season_id: activeSeason.id }));
        }
      }

      // Load leagues
      const leaguesResponse = await fetch('/api/admin/leagues', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (leaguesResponse.ok) {
        const leaguesData = await leaguesResponse.json();
        setLeagues(leaguesData.leagues || []);
      } else if (leaguesResponse.status === 401) {
        router.push('/login');
      }
    } catch (err: any) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLeague = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError('');

    try {
      const response = await fetch('/api/admin/leagues', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setShowCreateModal(false);
        setFormData({
          season_id: formData.season_id, // Keep season selected
          club_id: formData.club_id, // Keep club selected
          name: '',
          description: '',
          squad_size: 11,
          transfers_per_season: 4,
          require_from_each_team: true,
          is_public: true,
          max_participants: 100,
        });
        await loadData();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create league');
      }
    } catch (err: any) {
      setError('Failed to create league');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteLeague = async () => {
    if (!deleteLeagueId) return;

    setDeleting(true);
    setError('');

    try {
      await apiClient.deleteLeague(deleteLeagueId);
      setDeleteLeagueId(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete league');
    } finally {
      setDeleting(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cricket-green"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">League Management</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {leagues.length} active leagues
              </p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => router.push('/admin')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Dashboard
              </button>
              <button
                onClick={() => router.push('/admin/seasons')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Seasons
              </button>
              <button
                onClick={() => router.push('/admin/roster')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Roster
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Action Bar */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow mb-6">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800"
          >
            Create New League
          </button>
        </div>

        {/* Leagues List */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    League Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Season
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Join Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Participants
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Rules
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200">
                {leagues.map((league) => (
                  <tr key={league.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">{league.name}</div>
                      {league.description && (
                        <div className="text-sm text-gray-500 dark:text-gray-400">{league.description}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {league.season_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="px-2 py-1 bg-gray-100 text-cricket-green font-mono text-sm rounded">
                        {league.league_code}
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {league.participants_count} / {league.max_participants}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div>{league.squad_size} players</div>
                      <div>{league.transfers_per_season} transfers/season</div>
                      {league.require_from_each_team && (
                        <div className="text-xs text-cricket-green">1 from each team</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => router.push(`/admin/leagues/${league.id}`)}
                        className="text-cricket-green hover:text-green-900 mr-4"
                      >
                        Manage
                      </button>
                      <button
                        onClick={() => setDeleteLeagueId(league.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {leagues.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      No leagues created yet. Click &quot;Create New League&quot; to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Create League Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">Create New League</h3>
            <form onSubmit={handleCreateLeague}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Season *
                  </label>
                  <select
                    required
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.season_id}
                    onChange={(e) => setFormData({...formData, season_id: e.target.value})}
                  >
                    <option value="">Select a season...</option>
                    {seasons.map(season => (
                      <option key={season.id} value={season.id}>
                        {season.name} {season.is_active && '(Active)'}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Club *
                  </label>
                  <select
                    required
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.club_id}
                    onChange={(e) => setFormData({...formData, club_id: e.target.value})}
                  >
                    <option value="">Select a club...</option>
                    {clubs.map(club => (
                      <option key={club.id} value={club.id}>
                        {club.full_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    League Name *
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="ACC Premier League"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border rounded-md"
                    rows={3}
                    placeholder="Optional description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Squad Size
                  </label>
                  <input
                    type="number"
                    min="11"
                    max="15"
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.squad_size}
                    onChange={(e) => setFormData({...formData, squad_size: parseInt(e.target.value)})}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Fixed at 11 for now</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Transfers Per Season
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.transfers_per_season}
                    onChange={(e) => setFormData({...formData, transfers_per_season: parseInt(e.target.value)})}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Fixed at 4 for now</p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="require_from_each_team"
                    className="mr-2"
                    checked={formData.require_from_each_team}
                    onChange={(e) => setFormData({...formData, require_from_each_team: e.target.checked})}
                  />
                  <label htmlFor="require_from_each_team" className="text-sm text-gray-700 dark:text-gray-300">
                    Require one player from each team
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_public"
                    className="mr-2"
                    checked={formData.is_public}
                    onChange={(e) => setFormData({...formData, is_public: e.target.checked})}
                  />
                  <label htmlFor="is_public" className="text-sm text-gray-700 dark:text-gray-300">
                    Public league (anyone can join)
                  </label>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Max Participants
                  </label>
                  <input
                    type="number"
                    min="2"
                    max="1000"
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.max_participants}
                    onChange={(e) => setFormData({...formData, max_participants: parseInt(e.target.value)})}
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800 disabled:opacity-50"
                  disabled={creating}
                >
                  {creating ? 'Creating...' : 'Create League'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteLeagueId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Confirm Delete</h3>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              Are you sure you want to delete this league? This will also delete all fantasy teams in this league. This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setDeleteLeagueId(null)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteLeague}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete League'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
