'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import PointsPreview from '@/components/PointsPreview';

interface Player {
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

interface SelectedPlayer extends Player {
  is_captain: boolean;
  is_vice_captain: boolean;
  is_wicket_keeper: boolean;
  purchase_value: number;
  total_points: number;
}

interface TeamDetails {
  id: string;
  team_name: string;
  league_id: string;
  league_name: string;
  season_name: string;
  squad_size: number;
  budget_remaining: number;
  budget_used: number;
  players: SelectedPlayer[];
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

export default function TeamBuilderPage() {
  const router = useRouter();
  const params = useParams();
  const teamId = params.team_id as string;

  const [team, setTeam] = useState<TeamDetails | null>(null);
  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [filteredPlayers, setFilteredPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterTeam, setFilterTeam] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('multiplier');
  const [saving, setSaving] = useState(false);
  const [showRules, setShowRules] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadTeamData();
  }, [router, teamId]);

  useEffect(() => {
    filterAndSortPlayers();
  }, [availablePlayers, searchTerm, filterType, filterTeam, sortBy, team]);

  const loadTeamData = async () => {
    try {
      setLoading(true);
      const [teamData, playersData] = await Promise.all([
        apiClient.getTeamDetails(teamId),
        apiClient.getAvailablePlayers(teamId)
      ]);

      setTeam(teamData);
      setAvailablePlayers(playersData.available_players);
    } catch (err: any) {
      setError('Failed to load team data');
      if (err.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const getSquadAnalysis = () => {
    if (!team) return null;

    // Count players by team
    const teamCounts: Record<string, number> = {};
    team.players.forEach(player => {
      const teamName = player.team_name || 'Unknown';
      teamCounts[teamName] = (teamCounts[teamName] || 0) + 1;
    });

    // Find which teams are missing players (if require_from_each_team is enabled)
    let missingTeams: string[] = [];
    if (team.league_rules.require_from_each_team) {
      const allTeams = Array.from(new Set(availablePlayers.map(p => p.team_name).filter(Boolean)));
      missingTeams = allTeams.filter(teamName => !teamCounts[teamName] || teamCounts[teamName] === 0);
    }

    // Count players by role
    const batsmen = team.players.filter(p => p.player_type === 'batsman').length;
    const bowlers = team.players.filter(p => p.player_type === 'bowler').length;
    const allRounders = team.players.filter(p => p.player_type === 'all-rounder').length;

    // Calculate remaining spots
    const spotsRemaining = team.league_rules.squad_size - team.players.length;
    const batsmenNeeded = Math.max(0, team.league_rules.min_batsmen - batsmen);
    const bowlersNeeded = Math.max(0, team.league_rules.min_bowlers - bowlers);

    // Determine if we need to force a role filter
    let requiredRole: string | null = null;
    if (batsmenNeeded > 0 && spotsRemaining === batsmenNeeded) {
      requiredRole = 'batsman';
    } else if (bowlersNeeded > 0 && spotsRemaining === bowlersNeeded) {
      requiredRole = 'bowler';
    } else if (batsmenNeeded > 0 && bowlersNeeded > 0 && spotsRemaining === batsmenNeeded + bowlersNeeded) {
      // Need only batsmen and bowlers
      requiredRole = 'batsman-or-bowler';
    }

    return {
      teamCounts,
      batsmen,
      bowlers,
      allRounders,
      spotsRemaining,
      batsmenNeeded,
      bowlersNeeded,
      requiredRole,
      missingTeams
    };
  };

  const filterAndSortPlayers = () => {
    if (!team) return;

    let filtered = [...availablePlayers];
    const analysis = getSquadAnalysis();

    if (!analysis) return;

    // DYNAMIC FILTERING: Remove players from teams at max quota
    if (team.league_rules.max_players_per_team) {
      filtered = filtered.filter(p => {
        const teamName = p.team_name || 'Unknown';
        const currentCount = analysis.teamCounts[teamName] || 0;
        return currentCount < team.league_rules.max_players_per_team;
      });
    }

    // DYNAMIC FILTERING: Only show missing teams if spots remaining equals missing teams count
    // Example: 5 slots left, need players from 5 teams -> only show those 5 teams
    if (team.league_rules.require_from_each_team &&
        analysis.missingTeams.length > 0 &&
        analysis.spotsRemaining === analysis.missingTeams.length) {
      filtered = filtered.filter(p => {
        const teamName = p.team_name || 'Unknown';
        return analysis.missingTeams.includes(teamName);
      });
    }

    // DYNAMIC FILTERING: Force role filter if needed
    if (analysis.requiredRole === 'batsman') {
      filtered = filtered.filter(p => p.player_type === 'batsman');
    } else if (analysis.requiredRole === 'bowler') {
      filtered = filtered.filter(p => p.player_type === 'bowler');
    } else if (analysis.requiredRole === 'batsman-or-bowler') {
      filtered = filtered.filter(p => p.player_type === 'batsman' || p.player_type === 'bowler');
    }

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.team_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Type filter (only if not forced by requirements)
    if (filterType !== 'all' && !analysis.requiredRole) {
      filtered = filtered.filter(p => p.player_type === filterType);
    }

    // Team filter
    if (filterTeam !== 'all') {
      filtered = filtered.filter(p => p.team_name === filterTeam);
    }

    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'multiplier') {
        return (a.multiplier || 0.5) - (b.multiplier || 0.5); // Lower multiplier first (better players)
      } else if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'team') {
        return (a.team_name || '').localeCompare(b.team_name || '');
      }
      return 0;
    });

    setFilteredPlayers(filtered);
  };

  const handleAddPlayer = async (player: Player) => {
    if (!team) return;

    try {
      setSaving(true);
      await apiClient.addPlayerToTeam(teamId, player.id, false, false);
      await loadTeamData();
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add player');
    } finally {
      setSaving(false);
    }
  };

  const handleRemovePlayer = async (playerId: string) => {
    try {
      setSaving(true);
      await apiClient.removePlayerFromTeam(teamId, playerId);
      await loadTeamData();
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove player');
    } finally {
      setSaving(false);
    }
  };

  const handleFinalizeTeam = async () => {
    if (!team) return;

    if (team.players.length !== team.league_rules.squad_size) {
      setError(`You need exactly ${team.league_rules.squad_size} players to finalize your team`);
      return;
    }

    if (window.confirm('Are you sure you want to finalize your team? You won\'t be able to make changes after this!')) {
      try {
        setSaving(true);
        await apiClient.finalizeTeam(teamId);
        router.push('/teams');
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to finalize team');
      } finally {
        setSaving(false);
      }
    }
  };

  const getPlayerTypeColor = (type: string) => {
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

  const handleSetCaptain = async (playerId: string) => {
    if (!team) return;

    // Find if there's already a captain
    const currentCaptain = team.players.find(p => p.is_captain);
    if (currentCaptain && currentCaptain.id === playerId) {
      return; // Already captain
    }

    try {
      setSaving(true);
      // If there's a current captain, we need to remove them first by re-adding without captain flag
      if (currentCaptain) {
        await apiClient.removePlayerFromTeam(teamId, currentCaptain.id);
        await apiClient.addPlayerToTeam(teamId, currentCaptain.id, false, currentCaptain.is_vice_captain, currentCaptain.is_wicket_keeper);
      }

      // Now set the new captain
      const player = team.players.find(p => p.id === playerId);
      if (player) {
        await apiClient.removePlayerFromTeam(teamId, playerId);
        await apiClient.addPlayerToTeam(teamId, playerId, true, player.is_vice_captain, player.is_wicket_keeper);
      }

      await loadTeamData();
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to set captain');
    } finally {
      setSaving(false);
    }
  };

  const handleSetViceCaptain = async (playerId: string) => {
    if (!team) return;

    // Find if there's already a vice captain
    const currentViceCaptain = team.players.find(p => p.is_vice_captain);
    if (currentViceCaptain && currentViceCaptain.id === playerId) {
      return; // Already vice captain
    }

    try {
      setSaving(true);
      // If there's a current vice captain, remove them first
      if (currentViceCaptain) {
        await apiClient.removePlayerFromTeam(teamId, currentViceCaptain.id);
        await apiClient.addPlayerToTeam(teamId, currentViceCaptain.id, currentViceCaptain.is_captain, false, currentViceCaptain.is_wicket_keeper);
      }

      // Now set the new vice captain
      const player = team.players.find(p => p.id === playerId);
      if (player) {
        await apiClient.removePlayerFromTeam(teamId, playerId);
        await apiClient.addPlayerToTeam(teamId, playerId, player.is_captain, true, player.is_wicket_keeper);
      }

      await loadTeamData();
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to set vice captain');
    } finally {
      setSaving(false);
    }
  };

  const handleSetWicketKeeper = async (playerId: string) => {
    if (!team) return;

    // Find if there's already a wicket-keeper
    const currentWicketKeeper = team.players.find(p => p.is_wicket_keeper);
    if (currentWicketKeeper && currentWicketKeeper.id === playerId) {
      return; // Already wicket-keeper
    }

    try {
      setSaving(true);
      // If there's a current wicket-keeper, remove them first
      if (currentWicketKeeper) {
        await apiClient.removePlayerFromTeam(teamId, currentWicketKeeper.id);
        await apiClient.addPlayerToTeam(teamId, currentWicketKeeper.id, currentWicketKeeper.is_captain, currentWicketKeeper.is_vice_captain, false);
      }

      // Now set the new wicket-keeper
      const player = team.players.find(p => p.id === playerId);
      if (player) {
        await apiClient.removePlayerFromTeam(teamId, playerId);
        await apiClient.addPlayerToTeam(teamId, playerId, player.is_captain, player.is_vice_captain, true);
      }

      await loadTeamData();
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to set wicket-keeper');
    } finally {
      setSaving(false);
    }
  };

  const uniqueTeams = Array.from(new Set(availablePlayers.map(p => p.team_name).filter(Boolean)));

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
        <div className="text-red-600">Team not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-10">
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
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                {showRules ? 'Hide' : 'Show'} Rules
              </button>
              <button
                onClick={() => router.push(`/leagues/${team.league_id}/leaderboard`)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                League Stats
              </button>
              <button
                onClick={() => router.push('/teams')}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Back to Teams
              </button>
              <button
                onClick={handleFinalizeTeam}
                disabled={saving || team.players.length !== team.league_rules.squad_size}
                className="px-4 py-2 text-sm font-medium text-white bg-cricket-green rounded-md hover:bg-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Finalize Team
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Rules Panel */}
      {showRules && (
        <div className="bg-blue-50 border-b border-blue-200">
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
                      <li>• Example: 50 runs at SR 150 = 55.25 × 1.515 = 83.7 pts</li>
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
                      <li>• Catch: +4 points (regular)</li>
                      <li>• Catch: +8 points (wicketkeeper 2x)</li>
                      <li>• Stumping: +6 points</li>
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
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong>Note:</strong> Batting and bowling use <strong>tiered point systems</strong> where more runs/wickets earn progressively higher points per run/wicket.
                All base points from batting, bowling, and fielding are calculated first, then multiplied by your player&apos;s multiplier.
                Captain (2×), Vice-Captain (1.5×), and Wicket-Keeper (2× catches only) bonuses are applied after the multiplier calculation.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Squad Progress Bar */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Squad Progress</div>
              <div className={`text-2xl font-bold ${
                team.players.length === team.league_rules.squad_size
                  ? 'text-cricket-green'
                  : 'text-gray-900 dark:text-white'
              }`}>
                {team.players.length} / {team.league_rules.squad_size} Players
              </div>
            </div>
            <div className="w-1/2">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-cricket-green h-4 rounded-full transition-all"
                  style={{
                    width: `${(team.players.length / team.league_rules.squad_size) * 100}%`
                  }}
                ></div>
              </div>
            </div>
          </div>

          {/* Role Requirements Indicator */}
          {(() => {
            const analysis = getSquadAnalysis();
            if (!analysis) return null;

            const showRequirements = analysis.batsmenNeeded > 0 || analysis.bowlersNeeded > 0;

            return (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Batsmen */}
                <div className={`p-3 rounded-lg border-2 ${
                  analysis.batsmenNeeded > 0
                    ? 'bg-blue-50 border-blue-400'
                    : 'bg-gray-50 dark:bg-gray-900 border-gray-300 dark:border-gray-600'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300">Batsmen</div>
                    <div className={`text-lg font-bold ${
                      analysis.batsmenNeeded > 0
                        ? 'text-blue-600'
                        : 'text-green-600'
                    }`}>
                      {analysis.batsmen} / {team.league_rules.min_batsmen}
                    </div>
                  </div>
                  {analysis.batsmenNeeded > 0 && (
                    <div className="text-xs text-blue-600 font-medium mt-1">
                      Need {analysis.batsmenNeeded} more
                    </div>
                  )}
                </div>

                {/* Bowlers */}
                <div className={`p-3 rounded-lg border-2 ${
                  analysis.bowlersNeeded > 0
                    ? 'bg-green-50 border-green-400'
                    : 'bg-gray-50 dark:bg-gray-900 border-gray-300 dark:border-gray-600'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300">Bowlers</div>
                    <div className={`text-lg font-bold ${
                      analysis.bowlersNeeded > 0
                        ? 'text-green-600'
                        : 'text-green-600'
                    }`}>
                      {analysis.bowlers} / {team.league_rules.min_bowlers}
                    </div>
                  </div>
                  {analysis.bowlersNeeded > 0 && (
                    <div className="text-xs text-green-600 font-medium mt-1">
                      Need {analysis.bowlersNeeded} more
                    </div>
                  )}
                </div>

                {/* All-Rounders */}
                <div className="p-3 rounded-lg border-2 bg-gray-50 dark:bg-gray-900 border-gray-300 dark:border-gray-600">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300">All-Rounders</div>
                    <div className="text-lg font-bold text-gray-700 dark:text-gray-300">
                      {analysis.allRounders}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    No minimum required
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Active Filtering Notice */}
          {(() => {
            const analysis = getSquadAnalysis();
            if (!analysis) return null;

            if (analysis.requiredRole === 'batsman') {
              return (
                <div className="mt-3 p-3 bg-blue-100 border-l-4 border-blue-500 rounded">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-blue-800">
                      Only showing batsmen - you need {analysis.batsmenNeeded} more to meet minimum requirements
                    </span>
                  </div>
                </div>
              );
            } else if (analysis.requiredRole === 'bowler') {
              return (
                <div className="mt-3 p-3 bg-green-100 border-l-4 border-green-500 rounded">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-green-800">
                      Only showing bowlers - you need {analysis.bowlersNeeded} more to meet minimum requirements
                    </span>
                  </div>
                </div>
              );
            } else if (analysis.requiredRole === 'batsman-or-bowler') {
              return (
                <div className="mt-3 p-3 bg-orange-100 border-l-4 border-orange-500 rounded">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-orange-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-orange-800">
                      Only showing batsmen and bowlers - you need {analysis.batsmenNeeded} batsmen and {analysis.bowlersNeeded} bowlers
                    </span>
                  </div>
                </div>
              );
            }

            return null;
          })()}

          {/* Missing Teams Notice */}
          {(() => {
            const analysis = getSquadAnalysis();
            if (!analysis || !team) return null;

            if (team.league_rules.require_from_each_team && analysis.missingTeams.length > 0) {
              // Check if we're in strict mode (must pick from specific teams only)
              const strictMode = analysis.spotsRemaining === analysis.missingTeams.length;

              return (
                <div className={`mt-3 p-3 border-l-4 rounded ${
                  strictMode
                    ? 'bg-red-100 dark:bg-red-900/30 border-red-500'
                    : 'bg-yellow-100 dark:bg-yellow-900/30 border-yellow-500'
                }`}>
                  <div className="flex items-center">
                    <svg className={`w-5 h-5 mr-2 ${
                      strictMode ? 'text-red-600 dark:text-red-400' : 'text-yellow-600 dark:text-yellow-400'
                    }`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className={`text-sm font-medium ${
                      strictMode ? 'text-red-800 dark:text-red-300' : 'text-yellow-800 dark:text-yellow-300'
                    }`}>
                      {strictMode ? (
                        <>
                          ⚠️ ONLY showing players from: {analysis.missingTeams.join(', ')} ({analysis.spotsRemaining} slots = {analysis.missingTeams.length} missing teams)
                        </>
                      ) : (
                        <>
                          You need a player from team: {analysis.missingTeams.join(', ')}
                        </>
                      )}
                    </span>
                  </div>
                </div>
              );
            }

            return null;
          })()}
        </div>
      </div>

      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Selected Squad */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Your Squad</h2>

              {team.players.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <div className="text-4xl mb-2">👥</div>
                  <p className="text-sm">Start adding players to your squad</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {team.players.map((player) => (
                    <div
                      key={player.id}
                      className={`p-3 rounded-md ${
                        player.is_captain
                          ? 'bg-yellow-100 border-2 border-yellow-400'
                          : player.is_vice_captain
                          ? 'bg-blue-100 border-2 border-blue-400'
                          : 'bg-gray-50 dark:bg-gray-900'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {player.name}
                            </div>
                            <span
                              className={`px-2 py-0.5 text-xs font-medium rounded ${getPlayerTypeColor(
                                player.player_type
                              )}`}
                            >
                              {player.player_type}
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
                          <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                            <span>{player.team_name || 'Unknown'}</span>
                            {player.multiplier !== undefined && (
                              <span className={getMultiplierColor(player.multiplier)}>
                                ×{player.multiplier.toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemovePlayer(player.id)}
                          disabled={saving}
                          className="ml-2 text-red-600 hover:text-red-800 disabled:opacity-50"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>

                      {/* Captain/Vice-Captain/Wicket-Keeper Selection Buttons */}
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleSetCaptain(player.id)}
                          disabled={saving || player.is_captain}
                          className={`flex-1 px-2 py-1 text-xs font-medium rounded transition-colors ${
                            player.is_captain
                              ? 'bg-yellow-300 text-yellow-900 cursor-default'
                              : 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100 border border-yellow-300'
                          } disabled:opacity-50`}
                        >
                          {player.is_captain ? 'Captain' : 'Make Captain'}
                        </button>
                        <button
                          onClick={() => handleSetViceCaptain(player.id)}
                          disabled={saving || player.is_vice_captain}
                          className={`flex-1 px-2 py-1 text-xs font-medium rounded transition-colors ${
                            player.is_vice_captain
                              ? 'bg-blue-300 text-blue-900 cursor-default'
                              : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-300'
                          } disabled:opacity-50`}
                        >
                          {player.is_vice_captain ? 'Vice Captain' : 'Make Vice Captain'}
                        </button>
                        <button
                          onClick={() => handleSetWicketKeeper(player.id)}
                          disabled={saving || player.is_wicket_keeper}
                          className={`flex-1 px-2 py-1 text-xs font-medium rounded transition-colors ${
                            player.is_wicket_keeper
                              ? 'bg-purple-300 text-purple-900 cursor-default'
                              : 'bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-300'
                          } disabled:opacity-50`}
                        >
                          {player.is_wicket_keeper ? 'Wicket-Keeper' : 'Make WK'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Points Preview Calculator */}
            <div className="mt-6">
              <PointsPreview players={availablePlayers} />
            </div>
          </div>

          {/* Available Players */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              {/* Filters */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Available Players</h2>

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
                      {(() => {
                        const analysis = getSquadAnalysis();
                        const requiredRole = analysis?.requiredRole;

                        return (
                          <>
                            <option
                              value="batsman"
                              disabled={requiredRole === 'bowler'}
                            >
                              Batsmen {requiredRole === 'batsman' ? '(REQUIRED)' : requiredRole === 'bowler' ? '(UNAVAILABLE)' : ''}
                            </option>
                            <option
                              value="bowler"
                              disabled={requiredRole === 'batsman'}
                            >
                              Bowlers {requiredRole === 'bowler' ? '(REQUIRED)' : requiredRole === 'batsman' ? '(UNAVAILABLE)' : ''}
                            </option>
                            <option
                              value="all-rounder"
                              disabled={requiredRole === 'batsman' || requiredRole === 'bowler' || requiredRole === 'batsman-or-bowler'}
                            >
                              All-rounders {(requiredRole === 'batsman' || requiredRole === 'bowler' || requiredRole === 'batsman-or-bowler') ? '(UNAVAILABLE)' : ''}
                            </option>
                          </>
                        );
                      })()}
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
                      {uniqueTeams.map(teamName => {
                        const analysis = getSquadAnalysis();
                        const currentCount = analysis?.teamCounts[teamName] || 0;
                        const atMax = team && currentCount >= team.league_rules.max_players_per_team;

                        // Disable if at max OR if we're in "must pick from missing teams only" mode
                        const mustPickMissingOnly = analysis &&
                          team?.league_rules.require_from_each_team &&
                          analysis.missingTeams.length > 0 &&
                          analysis.spotsRemaining === analysis.missingTeams.length;

                        const isDisabled = atMax || (mustPickMissingOnly && !analysis.missingTeams.includes(teamName));

                        let label = teamName;
                        if (atMax) {
                          label += ` (${currentCount}/${team.league_rules.max_players_per_team} - MAX)`;
                        } else if (mustPickMissingOnly && analysis.missingTeams.includes(teamName)) {
                          label += ` (REQUIRED)`;
                        } else if (mustPickMissingOnly) {
                          label += ` (UNAVAILABLE)`;
                        } else {
                          label += ` (${currentCount}/${team.league_rules.max_players_per_team})`;
                        }

                        return (
                          <option
                            key={teamName}
                            value={teamName}
                            disabled={isDisabled || undefined}
                          >
                            {label}
                          </option>
                        );
                      })}
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

              {/* Player List */}
              <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
                {filteredPlayers.length === 0 ? (
                  <div className="p-12 text-center text-gray-500 dark:text-gray-400">
                    <div className="text-4xl mb-2">🔍</div>
                    <p>No players found matching your filters</p>
                  </div>
                ) : (
                  filteredPlayers.map((player) => (
                    <div
                      key={player.id}
                      className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900 transition-colors"
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
                                  player.player_type
                                )}`}
                              >
                                {player.player_type}
                              </span>
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              <span>{player.team_name || 'Unassigned'}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 ml-4">
                          <button
                            onClick={() => handleAddPlayer(player)}
                            disabled={saving}
                            className="px-4 py-2 text-sm font-medium text-white bg-cricket-green rounded-md hover:bg-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Add
                          </button>
                          <button
                            onClick={() => {
                              const url = `/calculator?player_id=${encodeURIComponent(player.id)}&player_name=${encodeURIComponent(player.name)}&multiplier=${player.multiplier || 1.0}`;
                              window.open(url, '_blank');
                            }}
                            className="px-3 py-2 text-sm font-medium text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border border-blue-300 dark:border-blue-700 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/50"
                            title="Load into Calculator"
                          >
                            🧮
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
