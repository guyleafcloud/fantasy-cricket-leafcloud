'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import type { Player, Team } from '@/types';

export default function RosterPage() {
  const router = useRouter();
  const [players, setPlayers] = useState<Player[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [teamFilter, setTeamFilter] = useState('');
  const [multiplierFilter, setMultiplierFilter] = useState('all');
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addMode, setAddMode] = useState<'manual' | 'csv'>('manual');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [newPlayer, setNewPlayer] = useState({
    name: '',
    team_id: '',
    player_type: '',
    multiplier: 1.0
  });
  const [includeYouth, setIncludeYouth] = useState({
    U13: true,
    U15: true,
    U17: true
  });

  const CLUB_ID = '625f1c55-6d5b-40a9-be1d-8f7abe6fa00e'; // ACC club ID

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
      const [playersData, teamsData] = await Promise.all([
        apiClient.getPlayers(CLUB_ID),
        apiClient.getTeams(CLUB_ID)
      ]);
      setPlayers(playersData.players);
      setTeams(teamsData);
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login');
      } else {
        setError('Failed to load data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/login');
  };

  const handleEdit = (player: Player) => {
    setEditingPlayer(player);
  };

  const handleDelete = async (playerId: string) => {
    if (!confirm('Are you sure you want to delete this player?')) return;

    try {
      await apiClient.deletePlayer(playerId);
      setPlayers(players.filter(p => p.id !== playerId));
    } catch (err) {
      alert('Failed to delete player');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingPlayer) return;

    try {
      const updated = await apiClient.updatePlayer(editingPlayer.id, {
        name: editingPlayer.name,
        team_id: editingPlayer.team_id,
        player_type: editingPlayer.player_type,
        multiplier: editingPlayer.multiplier
      });

      setPlayers(players.map(p => p.id === updated.id ? updated : p));
      setEditingPlayer(null);
    } catch (err) {
      alert('Failed to update player');
    }
  };

  const handleAddPlayer = async () => {
    if (!newPlayer.name.trim()) {
      alert('Player name is required');
      return;
    }

    try {
      const response = await fetch('/api/admin/players', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newPlayer.name,
          club_id: CLUB_ID,
          team_id: newPlayer.team_id || null,
          player_type: newPlayer.player_type || null,
          multiplier: newPlayer.multiplier
        }),
      });

      if (response.ok) {
        setShowAddModal(false);
        setNewPlayer({ name: '', team_id: '', player_type: '', multiplier: 1.0 });
        await loadData(); // Reload players list
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to add player');
      }
    } catch (err) {
      alert('Failed to add player');
    }
  };

  const handleUploadCSV = async () => {
    if (!uploadFile) {
      alert('Please select a CSV file');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('club_id', CLUB_ID);

      const response = await fetch('/api/admin/players/bulk', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setUploadResult(result);
        await loadData(); // Reload players list
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to upload CSV');
      }
    } catch (err) {
      alert('Failed to upload CSV');
    }
  };

  const handleConfirmRoster = async () => {
    // Get list of selected youth teams
    const selectedYouthTeams = Object.entries(includeYouth)
      .filter(([_, isIncluded]) => isIncluded)
      .map(([team, _]) => team);

    const youthSummary = selectedYouthTeams.length > 0
      ? ` (including ${selectedYouthTeams.join(', ')})`
      : ' (no youth teams)';

    const confirmMessage = `Confirm roster with ${getActivePlayerCount()} active players${youthSummary}?\n\n⚡ Player multipliers will be automatically calculated based on previous season performance.\n\n⏱️ This may take a moment if data needs to be fetched from KNCB.`;

    if (!confirm(confirmMessage)) {
      return;
    }

    try {
      const response = await fetch('/api/admin/roster/confirm', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          youth_teams: selectedYouthTeams,
          calculate_multipliers: true
        })
      });

      if (response.ok) {
        const result = await response.json();

        let message = `✅ Roster confirmed!\n\n`;
        message += `👥 Players: ${result.active_players} active, ${result.inactive_players} inactive\n\n`;

        if (result.multipliers_calculated && result.multiplier_stats) {
          const stats = result.multiplier_stats;
          message += `⚖️ Multipliers Calculated:\n`;
          message += `   • Players with data: ${stats.players_with_data}\n`;
          message += `   • Players without data: ${stats.players_without_data} (defaulted to 1.0)\n`;
          message += `   • Median score: ${stats.median_score} points\n`;
          message += `   • Multiplier range: ${stats.min_multiplier} - ${stats.max_multiplier}\n`;
          message += `   • Players at median: ${stats.players_at_median}`;
        } else if (result.multiplier_error) {
          message += `⚠️ Multiplier calculation failed: ${result.multiplier_error}`;
        }

        alert(message);
        router.push('/admin');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to confirm roster');
      }
    } catch (err) {
      alert('Failed to confirm roster. Please try again.');
    }
  };

  // Get color class based on multiplier value
  // Lower multipliers = better players (light to dark green)
  // Higher multipliers = worse players (yellow to red)
  const getMultiplierColor = (multiplier: number): string => {
    // Lower multiplier = better player = red (hot/expensive)
    // Higher multiplier = worse player = dark green (cheap)
    if (multiplier <= 0.7) {
      return 'bg-red-600 text-white'; // Red - best players
    } else if (multiplier <= 1.0) {
      return 'bg-orange-600 text-white'; // Dark orange
    } else if (multiplier <= 1.5) {
      return 'bg-orange-400 text-white'; // Orange
    } else if (multiplier <= 2.0) {
      return 'bg-yellow-400 text-gray-900 dark:text-white'; // Yellow
    } else if (multiplier <= 2.5) {
      return 'bg-green-200 text-green-900'; // Light green
    } else if (multiplier <= 3.0) {
      return 'bg-green-400 text-white'; // Medium green
    } else if (multiplier <= 3.5) {
      return 'bg-green-600 text-white'; // Medium-dark green
    } else {
      return 'bg-green-800 text-white'; // Dark green - worst players
    }
  };

  // Get unique team names from players (only teams that have players assigned)
  const uniqueTeamNames = Array.from(
    new Set(players.map(p => p.team_name).filter(Boolean))
  ).sort();

  // Helper functions for youth team calculations
  const getYouthPlayerCount = (team: string) => {
    return players.filter(p => p.team_name === team).length;
  };

  const getSeniorPlayerCount = () => {
    const seniorTeams = ['ACC 1', 'ACC 2', 'ACC 3', 'ACC 4', 'ACC 5', 'ACC 6', 'ZAMI 1'];
    return players.filter(p => p.team_name && seniorTeams.includes(p.team_name)).length;
  };

  const getYouthCount = () => {
    let count = 0;
    if (includeYouth.U13) count += getYouthPlayerCount('U13');
    if (includeYouth.U15) count += getYouthPlayerCount('U15');
    if (includeYouth.U17) count += getYouthPlayerCount('U17');
    return count;
  };

  const getActivePlayerCount = () => {
    return getSeniorPlayerCount() + getYouthCount();
  };

  const filteredPlayers = players.filter(player => {
    if (searchTerm && !player.name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (teamFilter && player.team_name !== teamFilter) {
      return false;
    }
    if (multiplierFilter === 'best' && player.multiplier > 1.0) {
      return false;
    }
    if (multiplierFilter === 'worst' && player.multiplier < 1.0) {
      return false;
    }
    return true;
  });

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
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">ACC Roster Management</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {filteredPlayers.length} of {players.length} players
              </p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={handleConfirmRoster}
                className="px-6 py-2 bg-cricket-green text-white rounded-md text-sm font-medium hover:bg-green-800 shadow-md"
              >
                ✓ Confirm Roster
              </button>
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
                onClick={() => router.push('/admin/leagues')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Leagues
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

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="Search players..."
              className="px-4 py-2 border rounded-md"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="px-4 py-2 border rounded-md"
              value={teamFilter}
              onChange={(e) => setTeamFilter(e.target.value)}
            >
              <option value="">All Teams</option>
              {uniqueTeamNames.map(teamName => (
                <option key={teamName} value={teamName}>{teamName}</option>
              ))}
            </select>
            <select
              className="px-4 py-2 border rounded-md"
              value={multiplierFilter}
              onChange={(e) => setMultiplierFilter(e.target.value)}
            >
              <option value="all">All Multipliers</option>
              <option value="best">Best ({"<"}1.0)</option>
              <option value="worst">Worst ({">"}1.0)</option>
            </select>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800"
            >
              Add Player
            </button>
          </div>
        </div>

        {/* Youth Team Participation */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">Youth Team Participation</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Select which youth teams will participate in the upcoming season
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* U13 Toggle */}
            <label className="flex items-center space-x-3 cursor-pointer p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
              <input
                type="checkbox"
                checked={includeYouth.U13}
                onChange={(e) => setIncludeYouth({...includeYouth, U13: e.target.checked})}
                className="w-5 h-5 text-cricket-green rounded focus:ring-cricket-green"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">U13</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{getYouthPlayerCount('U13')} players</div>
              </div>
            </label>

            {/* U15 Toggle */}
            <label className="flex items-center space-x-3 cursor-pointer p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
              <input
                type="checkbox"
                checked={includeYouth.U15}
                onChange={(e) => setIncludeYouth({...includeYouth, U15: e.target.checked})}
                className="w-5 h-5 text-cricket-green rounded focus:ring-cricket-green"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">U15</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{getYouthPlayerCount('U15')} players</div>
              </div>
            </label>

            {/* U17 Toggle */}
            <label className="flex items-center space-x-3 cursor-pointer p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
              <input
                type="checkbox"
                checked={includeYouth.U17}
                onChange={(e) => setIncludeYouth({...includeYouth, U17: e.target.checked})}
                className="w-5 h-5 text-cricket-green rounded focus:ring-cricket-green"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">U17</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{getYouthPlayerCount('U17')} players</div>
              </div>
            </label>
          </div>

          {/* Summary */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-gray-900 dark:text-white">
              <strong>Active Roster:</strong> {getActivePlayerCount()} players
              <span className="text-gray-600 dark:text-gray-400">
                {' '}({getSeniorPlayerCount()} senior + {getYouthCount()} youth)
              </span>
            </p>
          </div>
        </div>

        {/* Players Table */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Team
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Multiplier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Stats
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200">
                {filteredPlayers.map((player) => (
                  <tr key={player.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {player.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {player.team_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {player.player_type || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <span className={`px-2 py-1 rounded font-semibold ${getMultiplierColor(player.multiplier)}`}>
                        {player.multiplier.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {player.stats?.matches || 0}M | {player.stats?.runs || 0}R | {player.stats?.wickets || 0}W
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(player)}
                        className="text-indigo-600 hover:text-indigo-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(player.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Edit Modal */}
      {editingPlayer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Edit Player</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border rounded-md"
                  value={editingPlayer.name}
                  onChange={(e) => setEditingPlayer({...editingPlayer, name: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Team</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={editingPlayer.team_id}
                  onChange={(e) => setEditingPlayer({...editingPlayer, team_id: e.target.value})}
                >
                  {teams.map(team => (
                    <option key={team.id} value={team.id}>{team.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Player Type</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={editingPlayer.player_type || ''}
                  onChange={(e) => setEditingPlayer({...editingPlayer, player_type: e.target.value})}
                >
                  <option value="">Select type...</option>
                  <option value="batsman">Batsman</option>
                  <option value="bowler">Bowler</option>
                  <option value="all-rounder">All-rounder</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Multiplier (0.5-5.0)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.5"
                  max="5.0"
                  className="w-full px-3 py-2 border rounded-md"
                  value={editingPlayer.multiplier}
                  onChange={(e) => setEditingPlayer({...editingPlayer, multiplier: parseFloat(e.target.value)})}
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setEditingPlayer(null)}
                className="px-4 py-2 border rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Player Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">Add Player</h3>

            {/* Mode Tabs */}
            <div className="flex border-b border-gray-200 dark:border-gray-700 mb-4">
              <button
                onClick={() => {
                  setAddMode('manual');
                  setUploadResult(null);
                }}
                className={`px-4 py-2 font-medium ${
                  addMode === 'manual'
                    ? 'border-b-2 border-cricket-green text-cricket-green'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:text-gray-300'
                }`}
              >
                Manual Entry
              </button>
              <button
                onClick={() => setAddMode('csv')}
                className={`px-4 py-2 font-medium ${
                  addMode === 'csv'
                    ? 'border-b-2 border-cricket-green text-cricket-green'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:text-gray-300'
                }`}
              >
                CSV Upload
              </button>
            </div>

            {/* Manual Entry Form */}
            {addMode === 'manual' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Player Name *
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border rounded-md"
                    value={newPlayer.name}
                    onChange={(e) => setNewPlayer({...newPlayer, name: e.target.value})}
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Team
                  </label>
                  <select
                    className="w-full px-3 py-2 border rounded-md"
                    value={newPlayer.team_id}
                    onChange={(e) => setNewPlayer({...newPlayer, team_id: e.target.value})}
                  >
                    <option value="">Select team...</option>
                    {teams.map(team => (
                      <option key={team.id} value={team.id}>{team.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Player Type
                  </label>
                  <select
                    className="w-full px-3 py-2 border rounded-md"
                    value={newPlayer.player_type}
                    onChange={(e) => setNewPlayer({...newPlayer, player_type: e.target.value})}
                  >
                    <option value="">Select type...</option>
                    <option value="batsman">Batsman</option>
                    <option value="bowler">Bowler</option>
                    <option value="all-rounder">All-rounder</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Multiplier (0.5-5.0)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.5"
                    max="5.0"
                    className="w-full px-3 py-2 border rounded-md"
                    value={newPlayer.multiplier}
                    onChange={(e) => setNewPlayer({...newPlayer, multiplier: parseFloat(e.target.value) || 1.0})}
                  />
                </div>
              </div>
            )}

            {/* CSV Upload Form */}
            {addMode === 'csv' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Upload CSV File
                  </label>
                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-md p-6">
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => {
                        setUploadFile(e.target.files?.[0] || null);
                        setUploadResult(null);
                      }}
                      className="w-full"
                    />
                  </div>
                  {uploadFile && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      Selected: {uploadFile.name}
                    </p>
                  )}
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-md">
                  <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                    📋 CSV Format Requirements
                  </h4>

                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="font-medium text-blue-800 dark:text-blue-200 mb-1">Required Columns:</p>
                      <ul className="text-blue-700 dark:text-blue-300 space-y-1 ml-4">
                        <li>• <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">name</code> - Full player name (e.g., &quot;MickBoendermaker&quot;)</li>
                        <li>• <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">team_name</code> - Team assignment (e.g., &quot;ACC 1&quot;, &quot;ACC 2&quot;)</li>
                      </ul>
                    </div>

                    <div>
                      <p className="font-medium text-blue-800 dark:text-blue-200 mb-1">Optional Columns:</p>
                      <ul className="text-blue-700 dark:text-blue-300 space-y-1 ml-4">
                        <li>• <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">player_type</code> - batsman, bowler, or all-rounder</li>
                        <li>• <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">multiplier</code> - 0.5 to 5.0 (handicap, lower = better)</li>
                        <li>• <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">is_wicket_keeper</code> - true or false</li>
                      </ul>
                    </div>

                    <div className="bg-blue-100 dark:bg-blue-900/50 p-2 rounded">
                      <p className="font-medium text-blue-900 dark:text-blue-100 mb-1">🔄 Duplicate Handling:</p>
                      <p className="text-blue-800 dark:text-blue-200 text-xs">
                        CSV is the source of truth. If a player name already exists, their team assignment will be updated to match the CSV.
                        Multipliers are only updated if explicitly provided in the CSV.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Example CSV:</p>
                  <pre className="text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 p-3 rounded border overflow-x-auto">
{`name,team_name,player_type,multiplier,is_wicket_keeper
MickBoendermaker,ACC 1,batsman,1.5,false
GurlabhSingh,ACC 5,all-rounder,1.46,true
IrfanAlim,ACC 2,bowler,2.1,false`}
                  </pre>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    💡 <strong>Tip:</strong> Team names must exactly match existing teams (case-sensitive)
                  </p>
                </div>

                {uploadResult && (
                  <div className={`p-4 rounded-md border ${
                    uploadResult.error_count > 0
                      ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700'
                      : 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700'
                  }`}>
                    <p className="font-semibold mb-2 text-gray-900 dark:text-gray-100">
                      Upload Complete!
                    </p>
                    <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                      {uploadResult.created_count > 0 && (
                        <div className="text-green-700 dark:text-green-300">
                          ✅ <strong>{uploadResult.created_count}</strong> created
                        </div>
                      )}
                      {uploadResult.updated_count > 0 && (
                        <div className="text-blue-700 dark:text-blue-300">
                          🔄 <strong>{uploadResult.updated_count}</strong> updated
                        </div>
                      )}
                      {uploadResult.error_count > 0 && (
                        <div className="text-red-700 dark:text-red-300">
                          ❌ <strong>{uploadResult.error_count}</strong> errors
                        </div>
                      )}
                    </div>
                    {uploadResult.errors && uploadResult.errors.length > 0 && (
                      <div className="mt-3 bg-white dark:bg-gray-800 p-3 rounded border border-red-300 dark:border-red-700">
                        <p className="text-sm font-medium text-red-900 dark:text-red-100 mb-2">Errors:</p>
                        <ul className="text-xs text-red-700 dark:text-red-300 space-y-1 max-h-40 overflow-y-auto">
                          {uploadResult.errors.map((error: string, idx: number) => (
                            <li key={idx} className="font-mono">• {error}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setNewPlayer({ name: '', team_id: '', player_type: '', multiplier: 1.0 });
                  setUploadFile(null);
                  setUploadResult(null);
                }}
                className="px-4 py-2 border rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Cancel
              </button>
              {addMode === 'manual' ? (
                <button
                  onClick={handleAddPlayer}
                  className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800"
                >
                  Add Player
                </button>
              ) : (
                <button
                  onClick={handleUploadCSV}
                  disabled={!uploadFile}
                  className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Upload CSV
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
