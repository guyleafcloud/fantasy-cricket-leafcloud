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

                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-md">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">CSV Format:</p>
                  <pre className="text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 p-2 rounded border">
{`name,team_name,player_type,multiplier
John Doe,ACC 1,batsman,1.5
Jane Smith,ACC 2,bowler,2.0`}
                  </pre>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    * team_name must match existing team names<br/>
                    * player_type: batsman, bowler, or all-rounder<br/>
                    * multiplier: between 0.5 and 5.0
                  </p>
                </div>

                {uploadResult && (
                  <div className={`p-4 rounded-md ${
                    uploadResult.error_count > 0 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'
                  }`}>
                    <p className="font-medium mb-2">
                      {uploadResult.created_count} players created successfully
                      {uploadResult.error_count > 0 && ` • ${uploadResult.error_count} errors`}
                    </p>
                    {uploadResult.errors && uploadResult.errors.length > 0 && (
                      <div className="mt-2">
                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Errors:</p>
                        <ul className="text-sm text-red-600 space-y-1">
                          {uploadResult.errors.map((error: string, idx: number) => (
                            <li key={idx}>• {error}</li>
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
