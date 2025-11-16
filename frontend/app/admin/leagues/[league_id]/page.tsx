'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface FantasyTeam {
  id: string;
  team_name: string;
  user_id: string;
  total_points: number;
  rank: number | null;
  transfers_used: number;
  transfers_remaining: number;
  extra_transfers_granted: number;
  is_finalized: boolean;
}

interface LeagueDetails {
  id: string;
  season_id: string;
  season_name: string;
  name: string;
  description?: string;
  league_code: string;
  squad_size: number;
  transfers_per_season: number;
  require_from_each_team: boolean;
  is_public: boolean;
  max_participants: number;
  participants_count: number;
  teams: FantasyTeam[];
  created_at: string;
  min_batsmen?: number;
  min_bowlers?: number;
  require_wicket_keeper?: boolean;
  max_players_per_team?: number;
}

export default function LeagueDetailPage() {
  const router = useRouter();
  const params = useParams();
  const leagueId = params?.league_id as string;

  const [league, setLeague] = useState<LeagueDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditRulesModal, setShowEditRulesModal] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    squad_size: 11,
    transfers_per_season: 4,
    require_from_each_team: true,
    is_public: true,
    max_participants: 100,
    min_batsmen: 3,
    min_bowlers: 3,
    require_wicket_keeper: true,
    max_players_per_team: 3,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      router.push('/login');
      return;
    }
    if (leagueId) {
      loadLeagueDetails();
    }
  }, [router, leagueId]);

  const loadLeagueDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/leagues/${leagueId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setLeague(data);
        // Populate edit form with current league data
        setEditForm({
          name: data.name,
          description: data.description || '',
          squad_size: data.squad_size,
          transfers_per_season: data.transfers_per_season,
          require_from_each_team: data.require_from_each_team,
          is_public: data.is_public,
          max_participants: data.max_participants,
          min_batsmen: data.min_batsmen || 3,
          min_bowlers: data.min_bowlers || 3,
          require_wicket_keeper: data.require_wicket_keeper !== undefined ? data.require_wicket_keeper : true,
          max_players_per_team: data.max_players_per_team || 3,
        });
      } else if (response.status === 401) {
        router.push('/login');
      } else if (response.status === 404) {
        setError('League not found');
      } else {
        setError('Failed to load league details');
      }
    } catch (err: any) {
      setError('Failed to load league details');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/login');
  };

  const handleGrantTransfer = async (teamId: string) => {
    if (!confirm('Grant 1 additional transfer to this team?')) return;

    try {
      const response = await fetch(
        `/api/admin/leagues/${leagueId}/teams/${teamId}/grant-transfer`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ extra_transfers: 1 }),
        }
      );

      if (response.ok) {
        await loadLeagueDetails(); // Reload to show updated transfer counts
      } else {
        alert('Failed to grant transfer');
      }
    } catch (err) {
      alert('Failed to grant transfer');
    }
  };

  const handleSaveRules = async () => {
    try {
      setSaving(true);
      const response = await fetch(
        `/api/admin/leagues/${leagueId}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(editForm),
        }
      );

      if (response.ok) {
        await loadLeagueDetails(); // Reload to show updated rules
        setShowEditRulesModal(false);
        alert('League rules updated successfully');
      } else {
        alert('Failed to update league rules');
      }
    } catch (err) {
      alert('Failed to update league rules');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cricket-green"></div>
      </div>
    );
  }

  if (error || !league) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <header className="bg-white dark:bg-gray-800 shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">League Details</h1>
              <button
                onClick={() => router.push('/admin/leagues')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Back to Leagues
              </button>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-red-700">{error || 'League not found'}</p>
          </div>
        </main>
      </div>
    );
  }

  // Sort teams by rank (nulls last) then by points descending
  const sortedTeams = [...league.teams].sort((a, b) => {
    if (a.rank === null && b.rank === null) return b.total_points - a.total_points;
    if (a.rank === null) return 1;
    if (b.rank === null) return -1;
    return a.rank - b.rank;
  });

  // Calculate stats
  const totalPoints = league.teams.reduce((sum, t) => sum + t.total_points, 0);
  const avgPoints = league.teams.length > 0 ? totalPoints / league.teams.length : 0;
  const totalTransfersUsed = league.teams.reduce((sum, t) => sum + t.transfers_used, 0);
  const finalizedTeams = league.teams.filter(t => t.is_finalized).length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{league.name}</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {league.season_name} • Join Code: <code className="px-2 py-1 bg-gray-100 text-cricket-green font-mono text-sm rounded">{league.league_code}</code>
              </p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowEditRulesModal(true)}
                className="px-4 py-2 bg-cricket-green text-white rounded-md text-sm font-medium hover:bg-cricket-green-dark"
              >
                Edit League Rules
              </button>
              <button
                onClick={() => router.push('/admin')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Dashboard
              </button>
              <button
                onClick={() => router.push('/admin/leagues')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                All Leagues
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
        {/* League Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Participants</div>
            <div className="mt-2 text-3xl font-bold text-cricket-green">
              {league.participants_count} / {league.max_participants}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Points</div>
            <div className="mt-2 text-3xl font-bold text-cricket-green">
              {avgPoints.toFixed(1)}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Finalized Teams</div>
            <div className="mt-2 text-3xl font-bold text-cricket-green">
              {finalizedTeams} / {league.participants_count}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Transfers</div>
            <div className="mt-2 text-3xl font-bold text-cricket-green">
              {totalTransfersUsed}
            </div>
          </div>
        </div>

        {/* League Rules */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">League Rules</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Squad Size:</span>
              <span className="ml-2 text-gray-600 dark:text-gray-400">{league.squad_size} players</span>
            </div>
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Transfers:</span>
              <span className="ml-2 text-gray-600 dark:text-gray-400">{league.transfers_per_season} per season</span>
            </div>
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Team Requirement:</span>
              <span className="ml-2 text-gray-600 dark:text-gray-400">
                {league.require_from_each_team ? '1 player from each team' : 'No restrictions'}
              </span>
            </div>
          </div>
          {league.description && (
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">{league.description}</p>
          )}
        </div>

        {/* Leaderboard */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Leaderboard</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Team Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Points
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Transfers
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200">
                {sortedTeams.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      No teams have joined this league yet
                    </td>
                  </tr>
                ) : (
                  sortedTeams.map((team, index) => (
                    <tr key={team.id} className={index < 3 ? 'bg-green-50' : 'hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900'}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {index === 0 && (
                            <span className="text-2xl mr-2">🥇</span>
                          )}
                          {index === 1 && (
                            <span className="text-2xl mr-2">🥈</span>
                          )}
                          {index === 2 && (
                            <span className="text-2xl mr-2">🥉</span>
                          )}
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {team.rank || '-'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">{team.team_name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">{team.user_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-lg font-semibold text-cricket-green">
                          {team.total_points.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {team.is_finalized ? (
                          <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            Finalized
                          </span>
                        ) : (
                          <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                            Draft
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        <div>{team.transfers_used} used</div>
                        <div className="text-xs text-gray-400">
                          {team.transfers_remaining} remaining
                        </div>
                        {team.extra_transfers_granted > 0 && (
                          <div className="text-xs text-cricket-green">
                            +{team.extra_transfers_granted} granted
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleGrantTransfer(team.id)}
                          className="text-cricket-green hover:text-green-900"
                        >
                          Grant Transfer
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Edit League Rules Modal */}
      {showEditRulesModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="flex justify-between items-center pb-3 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Edit League Rules</h3>
              <button
                onClick={() => setShowEditRulesModal(false)}
                className="text-gray-400 hover:text-gray-500 dark:text-gray-400"
              >
                <span className="text-2xl">&times;</span>
              </button>
            </div>

            <div className="mt-4 space-y-4">
              {/* League Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">League Name</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                />
              </div>

              {/* Squad Size */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Squad Size</label>
                <input
                  type="number"
                  value={editForm.squad_size}
                  onChange={(e) => setEditForm({ ...editForm, squad_size: parseInt(e.target.value) })}
                  min={1}
                  max={15}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                />
              </div>

              {/* Transfers Per Season */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Transfers Per Season</label>
                <input
                  type="number"
                  value={editForm.transfers_per_season}
                  onChange={(e) => setEditForm({ ...editForm, transfers_per_season: parseInt(e.target.value) })}
                  min={0}
                  max={20}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                />
              </div>

              {/* Max Participants */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Max Participants</label>
                <input
                  type="number"
                  value={editForm.max_participants}
                  onChange={(e) => setEditForm({ ...editForm, max_participants: parseInt(e.target.value) })}
                  min={2}
                  max={500}
                  className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                />
              </div>

              {/* Team Composition Rules */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Team Composition Rules</h4>

                <div className="grid grid-cols-2 gap-4">
                  {/* Min Batsmen */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Min Batsmen</label>
                    <input
                      type="number"
                      value={editForm.min_batsmen}
                      onChange={(e) => setEditForm({ ...editForm, min_batsmen: parseInt(e.target.value) })}
                      min={0}
                      max={11}
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                    />
                  </div>

                  {/* Min Bowlers */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Min Bowlers</label>
                    <input
                      type="number"
                      value={editForm.min_bowlers}
                      onChange={(e) => setEditForm({ ...editForm, min_bowlers: parseInt(e.target.value) })}
                      min={0}
                      max={11}
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                    />
                  </div>

                  {/* Max Players Per Team */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Max Players Per Real Team
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Max players from same ACC team</p>
                    <input
                      type="number"
                      value={editForm.max_players_per_team}
                      onChange={(e) => setEditForm({ ...editForm, max_players_per_team: parseInt(e.target.value) })}
                      min={1}
                      max={11}
                      className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-cricket-green focus:ring-cricket-green sm:text-sm px-3 py-2 border"
                    />
                  </div>
                </div>

                {/* Require Wicket-Keeper */}
                <div className="flex items-center mt-3">
                  <input
                    type="checkbox"
                    id="require_wicket_keeper"
                    checked={editForm.require_wicket_keeper}
                    onChange={(e) => setEditForm({ ...editForm, require_wicket_keeper: e.target.checked })}
                    className="h-4 w-4 text-cricket-green focus:ring-cricket-green border-gray-300 dark:border-gray-600 rounded"
                  />
                  <label htmlFor="require_wicket_keeper" className="ml-2 block text-sm text-gray-900 dark:text-white">
                    Require at least 1 wicket-keeper
                  </label>
                </div>
              </div>

              {/* Require From Each Team */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="require_from_each_team"
                  checked={editForm.require_from_each_team}
                  onChange={(e) => setEditForm({ ...editForm, require_from_each_team: e.target.checked })}
                  className="h-4 w-4 text-cricket-green focus:ring-cricket-green border-gray-300 dark:border-gray-600 rounded"
                />
                <label htmlFor="require_from_each_team" className="ml-2 block text-sm text-gray-900 dark:text-white">
                  Require 1 player from each team
                </label>
              </div>

              {/* Is Public */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_public"
                  checked={editForm.is_public}
                  onChange={(e) => setEditForm({ ...editForm, is_public: e.target.checked })}
                  className="h-4 w-4 text-cricket-green focus:ring-cricket-green border-gray-300 dark:border-gray-600 rounded"
                />
                <label htmlFor="is_public" className="ml-2 block text-sm text-gray-900 dark:text-white">
                  Public league (visible to all users)
                </label>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setShowEditRulesModal(false)}
                disabled={saving}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRules}
                disabled={saving}
                className="px-4 py-2 bg-cricket-green text-white rounded-md text-sm font-medium hover:bg-cricket-green-dark disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
