'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface Player {
  id: string;
  name: string;
  club_name: string;
  team_name: string;
  player_type: string;
  is_wicket_keeper: boolean;
  fantasy_value: number;
  multiplier?: number;
  purchase_value: number;
  is_captain: boolean;
  is_vice_captain: boolean;
  total_points: number;
}

interface AvailablePlayer {
  id: string;
  name: string;
  club_name: string;
  team_name: string;
  player_type: string;
  is_wicket_keeper: boolean;
  fantasy_value: number;
  multiplier?: number;
  stats?: any;
}

interface TeamDetails {
  id: string;
  team_name: string;
  league_id: string;
  league_name: string;
  season_name: string;
  squad_size: number;
  total_points: number;
  rank: number | null;
  is_finalized: boolean;
  budget_remaining: number;
  budget_used: number;
  transfers_used: number;
  transfers_remaining: number;
  players: Player[];
  league_rules: {
    squad_size: number;
    budget: number;
    require_from_each_team: boolean;
    max_players_per_team: number;
    min_batsmen: number;
    min_bowlers: number;
    require_wicket_keeper: boolean;
  };
}

export default function TeamDetailPage() {
  const router = useRouter();
  const params = useParams();
  const teamId = params.team_id as string;

  const [team, setTeam] = useState<TeamDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Transfer state
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [playerToTransferOut, setPlayerToTransferOut] = useState<Player | null>(null);
  const [availablePlayers, setAvailablePlayers] = useState<AvailablePlayer[]>([]);
  const [filteredAvailablePlayers, setFilteredAvailablePlayers] = useState<AvailablePlayer[]>([]);
  const [loadingAvailablePlayers, setLoadingAvailablePlayers] = useState(false);
  const [transferring, setTransferring] = useState(false);
  const [selectedPlayerIn, setSelectedPlayerIn] = useState<string | null>(null);

  // Transfer filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  // Rules panel state
  const [showRules, setShowRules] = useState(false);
  const [filterTeam, setFilterTeam] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('multiplier');

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadTeamData();
  }, [router, teamId]);

  useEffect(() => {
    filterAndSortAvailablePlayers();
  }, [availablePlayers, searchTerm, filterType, filterTeam, sortBy]);

  const loadTeamData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTeamDetails(teamId);
      setTeam(data);
    } catch (err: any) {
      setError('Failed to load team details');
      if (err.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const getPlayerTypeColor = (type: string, isWK: boolean) => {
    if (isWK) return 'bg-purple-100 text-purple-800';
    if (type === 'batsman') return 'bg-blue-100 text-blue-800';
    if (type === 'bowler') return 'bg-green-100 text-green-800';
    if (type === 'all-rounder') return 'bg-orange-100 text-orange-800';
    return 'bg-gray-100 text-gray-800 dark:text-gray-200';
  };

  const getMultiplierColor = (multiplier: number) => {
    // Multipliers range from 0.69 (best) to 5.00 (worst)
    if (multiplier < 1.5) return 'text-green-600 font-bold';
    if (multiplier < 2.5) return 'text-green-500';
    if (multiplier < 3.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filterAndSortAvailablePlayers = () => {
    let filtered = [...availablePlayers];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.team_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Type filter
    if (filterType !== 'all') {
      if (filterType === 'wicket_keeper') {
        filtered = filtered.filter(p => p.is_wicket_keeper);
      } else {
        filtered = filtered.filter(p => p.player_type === filterType);
      }
    }

    // Team filter
    if (filterTeam !== 'all') {
      filtered = filtered.filter(p => p.team_name === filterTeam);
    }

    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'multiplier') {
        return (a.multiplier || 0.5) - (b.multiplier || 0.5);
      } else if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'team') {
        return (a.team_name || '').localeCompare(b.team_name || '');
      }
      return 0;
    });

    setFilteredAvailablePlayers(filtered);
  };

  const handleInitiateTransfer = async (player: Player) => {
    setPlayerToTransferOut(player);
    setShowTransferModal(true);
    setSelectedPlayerIn(null);
    setError('');

    // Reset filters
    setSearchTerm('');
    setFilterType('all');
    setFilterTeam('all');
    setSortBy('multiplier');

    // Load available players
    try {
      setLoadingAvailablePlayers(true);
      const data = await apiClient.getAvailablePlayers(teamId);
      setAvailablePlayers(data.available_players || []);
    } catch (err: any) {
      setError('Failed to load available players');
    } finally {
      setLoadingAvailablePlayers(false);
    }
  };

  const handleConfirmTransfer = async () => {
    if (!playerToTransferOut || !selectedPlayerIn) return;

    try {
      setTransferring(true);
      setError('');

      await apiClient.transferPlayer(teamId, playerToTransferOut.id, selectedPlayerIn);

      // Reload team data
      await loadTeamData();

      // Close modal and reset state
      setShowTransferModal(false);
      setPlayerToTransferOut(null);
      setSelectedPlayerIn(null);
      setAvailablePlayers([]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Transfer failed');
    } finally {
      setTransferring(false);
    }
  };

  const handleCancelTransfer = () => {
    setShowTransferModal(false);
    setPlayerToTransferOut(null);
    setSelectedPlayerIn(null);
    setAvailablePlayers([]);
    setError('');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cricket-green"></div>
      </div>
    );
  }

  if (!team) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="text-red-600 mb-4">Team not found</div>
          <button
            onClick={() => router.push('/teams')}
            className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800"
          >
            Back to My Teams
          </button>
        </div>
      </div>
    );
  }

  const captain = team.players.find(p => p.is_captain);
  const viceCaptain = team.players.find(p => p.is_vice_captain);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{team.team_name}</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {team.league_name} • {team.season_name}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => window.open('/calculator', '_blank')}
                className="px-4 py-2 text-sm font-medium text-white bg-orange-500 rounded-md hover:bg-orange-600"
              >
                🧮 Points Calculator
              </button>
              <button
                onClick={() => setShowRules(!showRules)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                {showRules ? 'Hide' : 'Show'} Rules
              </button>
              <button
                onClick={() => router.push('/teams')}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                My Teams
              </button>
              <button
                onClick={() => router.push(`/leagues/${team.league_id}/leaderboard`)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                League Stats
              </button>
              {!team.is_finalized && (
                <button
                  onClick={() => router.push(`/teams/${teamId}/build`)}
                  className="px-4 py-2 text-sm font-medium text-white bg-cricket-green rounded-md hover:bg-green-800"
                >
                  Edit Team
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Rules Panel */}
      {showRules && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Fantasy Cricket Rules & Scoring System</h2>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Team Building Rules */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 border-b pb-2">Team Building</h3>
                <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
                  <li className="flex items-start">
                    <span className="text-cricket-green mr-2">•</span>
                    <span>Squad Size: {team.league_rules.squad_size} players</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cricket-green mr-2">•</span>
                    <span>Max {team.league_rules.max_players_per_team} players per real-life team</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cricket-green mr-2">•</span>
                    <span>Min {team.league_rules.min_batsmen} batsmen required</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cricket-green mr-2">•</span>
                    <span>Min {team.league_rules.min_bowlers} bowlers required</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cricket-green mr-2">•</span>
                    <span>Designate 1 Captain (2x points)</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cricket-green mr-2">•</span>
                    <span>Designate 1 Vice-Captain (1.5x points)</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-cricket-green mr-2">•</span>
                    <span>Designate 1 Wicket-Keeper (2x catch points)</span>
                  </li>
                </ul>
              </div>

              {/* Batting Points */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 border-b pb-2">Batting Points</h3>
                <div className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white mb-1">Tiered Run Points:</div>
                    <ul className="ml-4 space-y-1">
                      <li>• Runs 1-30: 1.0 pts/run</li>
                      <li>• Runs 31-49: 1.25 pts/run</li>
                      <li>• Runs 50-99: 1.5 pts/run</li>
                      <li>• Runs 100+: 1.75 pts/run</li>
                      <li>• <span className="font-semibold">NO boundary bonuses</span> (fours/sixes count as runs only)</li>
                    </ul>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white mb-1">Strike Rate Multiplier:</div>
                    <ul className="ml-4 space-y-1">
                      <li>• Run points × (Strike Rate / 100)</li>
                      <li>• Example: 50 runs at SR 150 = 55.25 × 1.5 = 82.9 pts</li>
                    </ul>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white mb-1">Milestones:</div>
                    <ul className="ml-4 space-y-1">
                      <li>• 50 runs: +8 points</li>
                      <li>• 100 runs: +16 points</li>
                      <li>• Duck (0 runs while out): -2 points</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Bowling & Fielding Points */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 border-b pb-2">Bowling & Fielding</h3>
                <div className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white mb-1">Tiered Wicket Points:</div>
                    <ul className="ml-4 space-y-1">
                      <li>• Wickets 1-2: 15 pts each</li>
                      <li>• Wickets 3-4: 20 pts each</li>
                      <li>• Wickets 5-10: 30 pts each</li>
                      <li>• Maiden over: 15 points</li>
                    </ul>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white mb-1">Economy Rate Multiplier:</div>
                    <ul className="ml-4 space-y-1">
                      <li>• Wicket points × (6.0 / Economy Rate)</li>
                      <li>• Example: 3 wickets at ER 4.0 = 50 × 1.5 = 75 pts</li>
                    </ul>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white mb-1">Bonuses & Fielding:</div>
                    <ul className="ml-4 space-y-1">
                      <li>• 5 wicket haul: +8 points</li>
                      <li>• Catch: +15 points (regular)</li>
                      <li>• Catch: +30 points (wicketkeeper 2x)</li>
                      <li>• Stumping: +15 points</li>
                      <li>• Run Out: +6 points</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Multiplier System */}
            <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 border-b pb-2">Player Value Multiplier System (Performance Handicap)</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-700 dark:text-gray-300">
                <div>
                  <div className="font-medium text-gray-900 dark:text-white mb-2">How Multipliers Work:</div>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span>Each player has a multiplier between <strong>0.69</strong> (best IRL players - <strong>handicapped</strong>) and <strong>5.00</strong> (weak IRL players - <strong>boosted</strong>)</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span><strong>Lower multiplier (0.69)</strong> = Better IRL player = Fantasy points <strong>reduced/handicapped</strong></span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span><strong>Higher multiplier (5.0)</strong> = Weaker IRL player = Fantasy points <strong>boosted</strong></span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span>This creates balance: star players &quot;cost more&quot; in fantasy value, making weaker players attractive picks</span>
                    </li>
                  </ul>
                </div>
                <div>
                  <div className="font-medium text-gray-900 dark:text-white mb-2">Weekly Multiplier Adjustments:</div>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span>Multipliers adjust up to <strong>15% per week</strong> based on current performance</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span>Top weekly performers get lower multipliers (handicapped more)</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span>Poor weekly performers get higher multipliers (boosted more)</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-cricket-green mr-2">•</span>
                      <span>Example: 100 base points × 0.69 = 69 fantasy points (star player handicapped)</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Additional Info */}
            <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong>Note:</strong> Batting and bowling use <strong>tiered point systems</strong> where more runs/wickets earn progressively higher points per run/wicket.
                All base points from batting, bowling, and fielding are calculated first, then multiplied by your player&apos;s multiplier.
                Captain (2×), Vice-Captain (1.5×), and Wicket-Keeper (2× catches only) bonuses are applied after the multiplier calculation.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Team Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Points</div>
            <div className="text-3xl font-bold text-cricket-green">{team.total_points.toFixed(0)}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">League Rank</div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white">
              {team.rank ? `#${team.rank}` : 'N/A'}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Squad Size</div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white">
              {team.players.length}/{team.squad_size}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Transfers Left</div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white mb-3">{team.transfers_remaining}</div>
            <a
              href="https://www.acc-cricket.nl/ballensponsoren"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block w-full px-4 py-2 text-sm font-medium text-white bg-cricket-green rounded-md hover:bg-green-800 text-center transition-colors"
            >
              Purchase Transfer
            </a>
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-2">
              Show proof of purchase to game admin
            </p>
          </div>
        </div>

        {/* Captain & Vice Captain */}
        {(captain || viceCaptain) && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Leadership</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {captain && (
                <div className="border-2 border-yellow-400 rounded-lg p-4 bg-yellow-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold bg-yellow-200 text-yellow-900 px-2 py-1 rounded">
                      CAPTAIN (2x points)
                    </span>
                    {captain.multiplier !== undefined && (
                      <span className={`text-sm font-medium ${getMultiplierColor(captain.multiplier)}`}>
                        ×{captain.multiplier.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{captain.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{captain.team_name}</p>
                  <div className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                    {captain.total_points.toFixed(0)} points
                  </div>
                </div>
              )}
              {viceCaptain && (
                <div className="border-2 border-blue-400 rounded-lg p-4 bg-blue-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold bg-blue-200 text-blue-900 px-2 py-1 rounded">
                      VICE-CAPTAIN (1.5x points)
                    </span>
                    {viceCaptain.multiplier !== undefined && (
                      <span className={`text-sm font-medium ${getMultiplierColor(viceCaptain.multiplier)}`}>
                        ×{viceCaptain.multiplier.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{viceCaptain.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{viceCaptain.team_name}</p>
                  <div className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                    {viceCaptain.total_points.toFixed(0)} points
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Squad List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Your Squad</h2>
          </div>

          {team.players.length === 0 ? (
            <div className="p-12 text-center text-gray-500 dark:text-gray-400">
              <div className="text-4xl mb-2">👥</div>
              <p>No players in this team yet</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {team.players
                .sort((a, b) => {
                  // Captain first, then vice-captain, then by points
                  if (a.is_captain) return -1;
                  if (b.is_captain) return 1;
                  if (a.is_vice_captain) return -1;
                  if (b.is_vice_captain) return 1;
                  return b.total_points - a.total_points;
                })
                .map((player) => (
                  <div
                    key={player.id}
                    className={`p-4 ${
                      player.is_captain
                        ? 'bg-yellow-50'
                        : player.is_vice_captain
                        ? 'bg-blue-50'
                        : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 flex-1">
                        {/* Multiplier */}
                        {player.multiplier !== undefined && (
                          <div className="flex-shrink-0 w-16 text-center">
                            <span className={`text-lg font-bold ${getMultiplierColor(player.multiplier)}`}>
                              {player.multiplier.toFixed(2)}
                            </span>
                          </div>
                        )}

                        {/* Player Info */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-sm font-medium text-gray-900 dark:text-white">{player.name}</h3>
                            <span
                              className={`px-2 py-0.5 text-xs font-medium rounded ${getPlayerTypeColor(
                                player.player_type,
                                player.is_wicket_keeper
                              )}`}
                            >
                              {player.is_wicket_keeper ? 'WK' : player.player_type}
                            </span>
                            {player.is_captain && (
                              <span className="px-2 py-0.5 text-xs font-bold bg-yellow-200 text-yellow-900 rounded">
                                (C)
                              </span>
                            )}
                            {player.is_vice_captain && (
                              <span className="px-2 py-0.5 text-xs font-bold bg-blue-200 text-blue-900 rounded">
                                (VC)
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{player.team_name}</p>
                        </div>

                        {/* Points */}
                        <div className="text-right">
                          <div className="text-lg font-bold text-cricket-green">
                            {player.total_points.toFixed(0)}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">points</div>
                        </div>

                        {/* Transfer Button */}
                        {team.is_finalized && team.transfers_remaining > 0 && (
                          <button
                            onClick={() => handleInitiateTransfer(player)}
                            className="ml-4 px-3 py-1.5 text-xs font-medium text-white bg-cricket-green rounded hover:bg-green-800 transition-colors"
                          >
                            Transfer
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Transfer Modal */}
      {showTransferModal && playerToTransferOut && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75">
          <div className="flex items-center justify-center min-h-screen p-4">
            {/* Modal panel - Full width on mobile, large on desktop */}
            <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
              {/* Header */}
              <div className="bg-cricket-green px-6 py-4 flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold text-white">Transfer Player</h3>
                  <p className="text-sm text-green-100">Transferring out: {playerToTransferOut.name}</p>
                </div>
                <button
                  onClick={handleCancelTransfer}
                  className="text-white hover:text-gray-200"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Error Display Inside Modal */}
              {error && (
                <div className="mx-6 mt-4 bg-red-50 border-l-4 border-red-400 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Content - Scrollable */}
              <div className="flex-1 overflow-y-auto">
                <div className="p-6">
                  {/* Available Players Section - Same as Team Builder */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                    {/* Filters - Same as Team Builder */}
                    <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Select Replacement Player</h2>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Search
                          </label>
                          <input
                            type="text"
                            placeholder="Player or team name..."
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-cricket-green text-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Player Type
                          </label>
                          <select
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-cricket-green text-sm"
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                          >
                            <option value="all">All Types</option>
                            <option value="batsman">Batsmen</option>
                            <option value="bowler">Bowlers</option>
                            <option value="all-rounder">All-rounders</option>
                            <option value="wicket_keeper">Wicket Keepers</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Filter by Team
                          </label>
                          <select
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-cricket-green text-sm"
                            value={filterTeam}
                            onChange={(e) => setFilterTeam(e.target.value)}
                          >
                            <option value="all">All Teams</option>
                            {Array.from(new Set(availablePlayers.map(p => p.team_name).filter(Boolean))).map(teamName => (
                              <option key={teamName} value={teamName}>{teamName}</option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Sort By
                          </label>
                          <select
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-cricket-green text-sm"
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                          >
                            <option value="multiplier">Multiplier (Best First)</option>
                            <option value="name">Name (A-Z)</option>
                            <option value="team">Team Name</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Player List - Same as Team Builder */}
                    <div className="divide-y divide-gray-200 max-h-[400px] overflow-y-auto">
                      {loadingAvailablePlayers ? (
                        <div className="flex justify-center py-12">
                          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cricket-green"></div>
                        </div>
                      ) : filteredAvailablePlayers.length === 0 ? (
                        <div className="p-12 text-center text-gray-500 dark:text-gray-400">
                          <div className="text-4xl mb-2">🔍</div>
                          <p>No players found matching your filters</p>
                        </div>
                      ) : (
                        filteredAvailablePlayers.map((player) => (
                          <div
                            key={player.id}
                            onClick={() => setSelectedPlayerIn(player.id)}
                            className={`p-4 cursor-pointer transition-colors ${
                              selectedPlayerIn === player.id
                                ? 'bg-green-100 border-l-4 border-l-cricket-green'
                                : 'hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-4 flex-1">
                                {/* Multiplier First - Most Prominent */}
                                {player.multiplier !== undefined && (
                                  <div className="flex-shrink-0 w-16 text-center">
                                    <span className={`text-lg font-bold ${getMultiplierColor(player.multiplier)}`}>
                                      {player.multiplier.toFixed(2)}
                                    </span>
                                  </div>
                                )}

                                {/* Player Details */}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                      {player.name}
                                    </h3>
                                    <span
                                      className={`px-2 py-0.5 text-xs font-medium rounded ${getPlayerTypeColor(
                                        player.player_type,
                                        player.is_wicket_keeper
                                      )}`}
                                    >
                                      {player.is_wicket_keeper ? 'WK' : player.player_type}
                                    </span>
                                  </div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400">
                                    <span>{player.team_name || 'Unassigned'}</span>
                                  </div>
                                </div>

                                {/* Selection indicator */}
                                {selectedPlayerIn === player.id && (
                                  <div className="flex-shrink-0">
                                    <svg className="w-6 h-6 text-cricket-green" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="bg-gray-50 dark:bg-gray-900 px-6 py-4 flex justify-end gap-3 border-t">
                <button
                  onClick={handleCancelTransfer}
                  disabled={transferring}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmTransfer}
                  disabled={!selectedPlayerIn || transferring}
                  className="px-4 py-2 text-sm font-medium text-white bg-cricket-green rounded-md hover:bg-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {transferring ? 'Processing...' : 'Confirm Transfer'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
