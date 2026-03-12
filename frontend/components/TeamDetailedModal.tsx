'use client';

import { useState, useEffect } from 'react';
import { DetailedTeamStats, DetailedPlayerStats } from '@/types';
import PlayerPerformanceCard from './PlayerPerformanceCard';
import PlayerComparisonModal from './PlayerComparisonModal';

interface TeamDetailedModalProps {
  isOpen: boolean;
  onClose: () => void;
  teamId: string;
  leagueId: string;
}

export default function TeamDetailedModal({
  isOpen,
  onClose,
  teamId,
  leagueId
}: TeamDetailedModalProps) {
  const [teamData, setTeamData] = useState<DetailedTeamStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchCount, setMatchCount] = useState(3);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState(false);

  useEffect(() => {
    if (isOpen && teamId && leagueId && teamId.length > 0) {
      fetchTeamDetails();
    }
  }, [isOpen, teamId, leagueId, matchCount]);

  const fetchTeamDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('admin_token');
      const response = await fetch(
        `/api/leagues/${leagueId}/teams/${teamId}/detailed?match_count=${matchCount}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch team details');
      }

      const data = await response.json();
      setTeamData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerSelect = (playerId: string) => {
    setSelectedPlayers(prev => {
      if (prev.includes(playerId)) {
        return prev.filter(id => id !== playerId);
      }
      if (prev.length >= 2) {
        return [prev[1], playerId]; // Replace oldest selection
      }
      return [...prev, playerId];
    });
  };

  const handleCompare = () => {
    if (selectedPlayers.length === 2) {
      setShowComparison(true);
    }
  };

  const getPlayerById = (playerId: string): DetailedPlayerStats | null => {
    return teamData?.players.find(p => p.player_id === playerId) || null;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">

        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-1">
              {teamData?.team_name || 'Loading...'}
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Owner: {teamData?.owner_name || '...'}
            </p>
            <div className="flex gap-4 mt-2 text-sm">
              <span className="font-semibold text-blue-600 dark:text-blue-400">
                Total: {teamData?.total_points.toFixed(1) || '0'} pts
              </span>
              <span className="text-gray-600 dark:text-gray-400">
                Weekly: {teamData?.weekly_points.toFixed(1) || '0'} pts
              </span>
              <span className="text-gray-600 dark:text-gray-400">
                Squad: {teamData?.squad_size || 0} players
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Controls */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex flex-wrap gap-4 items-center">
          {/* Match History Control */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Show last</label>
            <select
              value={matchCount}
              onChange={(e) => setMatchCount(Number(e.target.value))}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700"
            >
              <option value={1}>1 match</option>
              <option value={3}>3 matches</option>
              <option value={5}>5 matches</option>
              <option value={10}>10 matches</option>
            </select>
          </div>

          {/* Comparison Mode Toggle */}
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={comparisonMode}
                onChange={(e) => {
                  setComparisonMode(e.target.checked);
                  if (!e.target.checked) {
                    setSelectedPlayers([]);
                  }
                }}
                className="rounded"
              />
              <span>Comparison Mode</span>
            </label>
          </div>

          {/* Compare Button */}
          {comparisonMode && (
            <button
              onClick={handleCompare}
              disabled={selectedPlayers.length !== 2}
              className={`px-4 py-1 rounded-md text-sm font-medium ${
                selectedPlayers.length === 2
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Compare ({selectedPlayers.length}/2)
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          {!loading && !error && teamData && (
            <div className="space-y-4">
              {teamData.players.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No players in this team
                </div>
              ) : (
                teamData.players.map((player: DetailedPlayerStats) => (
                  <PlayerPerformanceCard
                    key={player.player_id}
                    player={player}
                    selected={selectedPlayers.includes(player.player_id)}
                    onSelect={handlePlayerSelect}
                    showComparison={comparisonMode}
                  />
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            Close
          </button>
        </div>
      </div>

      {/* Player Comparison Modal */}
      <PlayerComparisonModal
        isOpen={showComparison}
        onClose={() => setShowComparison(false)}
        player1={getPlayerById(selectedPlayers[0])}
        player2={getPlayerById(selectedPlayers[1])}
      />
    </div>
  );
}
