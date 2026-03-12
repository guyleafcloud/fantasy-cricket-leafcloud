'use client';

import { useState, useEffect } from 'react';

interface LeaguePlayer {
  player_id: string;
  player_name: string;
  club_name: string;
  player_role: string;
  current_multiplier: number;
  ownership_count: number;
  ownership_percentage: number;
  total_points: number;
  matches_played: number;
  batting: {
    runs: number;
    average: number;
    strike_rate: number;
    fours: number;
    sixes: number;
    fifties: number;
    hundreds: number;
    highest_score: number;
  };
  bowling: {
    wickets: number;
    overs: number;
    economy: number | null;
    maidens: number;
    five_wicket_hauls: number;
  };
  fielding: {
    catches: number;
    run_outs: number;
    stumpings: number;
  };
}

interface LeaguePlayerStatsProps {
  leagueId: string;
}

export default function LeaguePlayerStats({ leagueId }: LeaguePlayerStatsProps) {
  const [players, setPlayers] = useState<LeaguePlayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<string>('total_points');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    fetchPlayers();
  }, [leagueId, roleFilter, sortBy]);

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('admin_token');
      const roleParam = roleFilter !== 'ALL' ? `&role=${roleFilter}` : '';
      const response = await fetch(
        `/api/leagues/${leagueId}/all-players?sort_by=${sortBy}${roleParam}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch player stats');
      }

      const data = await response.json();
      setPlayers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Filter players by search term (client-side)
  const filteredPlayers = players.filter(player =>
    player.player_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    player.club_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRoleIcon = (role: string) => {
    if (!role) return '👤';
    const upperRole = role.toUpperCase();
    if (upperRole.includes('BAT') && upperRole.includes('WK')) return '🧤🏏';
    if (upperRole.includes('BAT')) return '🏏';
    if (upperRole.includes('BOWL')) return '⚾';
    if (upperRole.includes('ALL')) return '🏏⚾';
    if (upperRole.includes('KEEP') || upperRole.includes('WK')) return '🧤';
    return '👤';
  };

  const getOwnershipColor = (percentage: number) => {
    if (percentage >= 75) return 'text-red-600 dark:text-red-400 font-bold';
    if (percentage >= 50) return 'text-orange-600 dark:text-orange-400 font-semibold';
    if (percentage >= 25) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
        League Player Statistics
      </h2>

      {/* Filters */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Search */}
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
            Search Players
          </label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Player name or club..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>

        {/* Role Filter */}
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
            Filter by Role
          </label>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="ALL">All Roles</option>
            <option value="BATSMAN">Batsmen</option>
            <option value="BOWLER">Bowlers</option>
            <option value="ALL-ROUNDER">All-Rounders</option>
            <option value="WK">Wicket-Keepers</option>
          </select>
        </div>

        {/* Sort By */}
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
            Sort By
          </label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="total_points">Total Points</option>
            <option value="runs">Most Runs</option>
            <option value="wickets">Most Wickets</option>
            <option value="ownership">Ownership %</option>
            <option value="average">Batting Average</option>
            <option value="strike_rate">Strike Rate</option>
          </select>
        </div>
      </div>

      {/* Loading / Error States */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400 mb-4">
          {error}
        </div>
      )}

      {/* Player Cards - Mobile First */}
      {!loading && !error && (
        <>
          <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
            Showing {filteredPlayers.length} player{filteredPlayers.length !== 1 ? 's' : ''}
          </div>

          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {filteredPlayers.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No players found matching your criteria
              </div>
            ) : (
              filteredPlayers.map((player) => (
                <div
                  key={player.player_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow bg-gray-50 dark:bg-gray-900"
                >
                  {/* Player Header */}
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{getRoleIcon(player.player_role)}</span>
                        <h3 className="font-semibold text-base text-gray-900 dark:text-white">
                          {player.player_name}
                        </h3>
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {player.club_name} • {player.player_role}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-xl font-bold text-blue-600 dark:text-blue-400">
                        {player.total_points}
                      </div>
                      <div className="text-xs text-gray-500">
                        {player.matches_played} matches
                      </div>
                    </div>
                  </div>

                  {/* Ownership & Multiplier */}
                  <div className="flex justify-between items-center mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
                    <div className="text-xs">
                      <span className="text-gray-600 dark:text-gray-400">Ownership: </span>
                      <span className={getOwnershipColor(player.ownership_percentage)}>
                        {player.ownership_percentage}% ({player.ownership_count} teams)
                      </span>
                    </div>
                    <div className="text-xs">
                      <span className="text-gray-600 dark:text-gray-400">Multiplier: </span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {player.current_multiplier.toFixed(2)}x
                      </span>
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    {/* Batting */}
                    {player.batting.runs > 0 && (
                      <div className="bg-white dark:bg-gray-800 p-2 rounded text-center">
                        <div className="text-green-600 dark:text-green-400 font-semibold">
                          🏏 {player.batting.runs}
                        </div>
                        <div className="text-gray-500 text-[10px]">
                          Runs @ {player.batting.strike_rate.toFixed(0)} SR
                        </div>
                      </div>
                    )}

                    {/* Bowling */}
                    {player.bowling.wickets > 0 && (
                      <div className="bg-white dark:bg-gray-800 p-2 rounded text-center">
                        <div className="text-blue-600 dark:text-blue-400 font-semibold">
                          ⚾ {player.bowling.wickets}
                        </div>
                        <div className="text-gray-500 text-[10px]">
                          Wkts @ {player.bowling.economy?.toFixed(1) || '0.0'} econ
                        </div>
                      </div>
                    )}

                    {/* Fielding */}
                    {(player.fielding.catches + player.fielding.run_outs + player.fielding.stumpings) > 0 && (
                      <div className="bg-white dark:bg-gray-800 p-2 rounded text-center">
                        <div className="text-amber-600 dark:text-amber-400 font-semibold">
                          🧤 {player.fielding.catches + player.fielding.run_outs + player.fielding.stumpings}
                        </div>
                        <div className="text-gray-500 text-[10px]">
                          C/RO/ST
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Additional Stats (collapsible on mobile) */}
                  {(player.batting.fifties > 0 || player.batting.hundreds > 0 || player.bowling.five_wicket_hauls > 0) && (
                    <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-600 dark:text-gray-400">
                      {player.batting.hundreds > 0 && <span className="mr-3">💯 {player.batting.hundreds}</span>}
                      {player.batting.fifties > 0 && <span className="mr-3">5️⃣0️⃣ {player.batting.fifties}</span>}
                      {player.bowling.five_wicket_hauls > 0 && <span>🎯 {player.bowling.five_wicket_hauls}x 5-fer</span>}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
