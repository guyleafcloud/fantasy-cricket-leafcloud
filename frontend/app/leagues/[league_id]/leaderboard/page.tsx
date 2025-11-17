'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

interface LeaderboardEntry {
  rank: number;
  team_id: string;
  team_name: string;
  owner_name: string;
  total_points: number;
  weekly_points: number;
}

interface TeamPlayer {
  id: string;
  name: string;
  club_name: string;
  total_points: number;
  is_captain: boolean;
  is_vice_captain: boolean;
  is_wicket_keeper: boolean;
}

interface LeagueStats {
  best_batsman: {
    player_name: string;
    team_name: string;
    runs: number;
    average: number;
    strike_rate: number;
  } | null;
  best_bowler: {
    player_name: string;
    team_name: string;
    wickets: number;
    average: number;
    economy: number;
  } | null;
  best_fielder: {
    player_name: string;
    team_name: string;
    catches: number;
  } | null;
  best_team: {
    team_name: string;
    total_points: number;
    player_count: number;
  } | null;
  top_players: Array<{
    player_name: string;
    team_name: string;
    total_points: number;
  }>;
}

export default function LeaderboardPage() {
  const params = useParams();
  const router = useRouter();
  const league_id = params.league_id as string;

  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [stats, setStats] = useState<LeagueStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<LeaderboardEntry | null>(null);
  const [teamPlayers, setTeamPlayers] = useState<TeamPlayer[]>([]);
  const [loadingTeam, setLoadingTeam] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('admin_token');

        // Fetch both leaderboard and stats in parallel
        const [leaderboardResponse, statsResponse] = await Promise.all([
          fetch(`/api/leagues/${league_id}/leaderboard`, {
            headers: { 'Authorization': `Bearer ${token}` },
          }),
          fetch(`/api/leagues/${league_id}/stats`, {
            headers: { 'Authorization': `Bearer ${token}` },
          })
        ]);

        if (!leaderboardResponse.ok) {
          throw new Error('Failed to fetch leaderboard');
        }

        const leaderboardData = await leaderboardResponse.json();
        setLeaderboard(leaderboardData);

        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStats(statsData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (league_id) {
      fetchData();
    }
  }, [league_id]);

  const fetchTeamDetails = async (team: LeaderboardEntry) => {
    setSelectedTeam(team);
    setLoadingTeam(true);
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`/api/leagues/${league_id}/teams/${team.team_id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setTeamPlayers(data.players || []);
      }
    } catch (err) {
      console.error('Error fetching team details:', err);
    } finally {
      setLoadingTeam(false);
    }
  };

  const closeModal = () => {
    setSelectedTeam(null);
    setTeamPlayers([]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-cricket-green to-green-700 flex items-center justify-center">
        <div className="text-white text-xl">Loading leaderboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-cricket-green to-green-700 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700 dark:text-gray-300">{error}</p>
          <button
            onClick={() => router.back()}
            className="mt-4 px-4 py-2 bg-cricket-green text-white rounded-lg hover:bg-green-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cricket-green to-green-700 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">League Leaderboard</h1>
            <button
              onClick={() => router.push('/leagues')}
              className="px-4 py-2 bg-gray-200 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300"
            >
              Back to Leagues
            </button>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-cricket-green text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Rank</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Team Name</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Owner</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold">Total Points</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold">Weekly Points</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {leaderboard.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      No teams in this league yet
                    </td>
                  </tr>
                ) : (
                  leaderboard.map((entry) => (
                    <tr
                      key={entry.rank}
                      className={`hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900 ${
                        entry.rank === 1
                          ? 'bg-yellow-50'
                          : entry.rank === 2
                          ? 'bg-gray-100'
                          : entry.rank === 3
                          ? 'bg-orange-50'
                          : ''
                      }`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {entry.rank === 1 && (
                            <span className="text-2xl mr-2">🥇</span>
                          )}
                          {entry.rank === 2 && (
                            <span className="text-2xl mr-2">🥈</span>
                          )}
                          {entry.rank === 3 && (
                            <span className="text-2xl mr-2">🥉</span>
                          )}
                          <span className="text-lg font-semibold text-gray-900 dark:text-white">
                            {entry.rank}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => fetchTeamDetails(entry)}
                          className="text-sm font-medium text-cricket-green hover:text-green-700 underline cursor-pointer"
                        >
                          {entry.team_name}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-300">{entry.owner_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-lg font-bold text-cricket-green">
                          {entry.total_points.toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-sm text-gray-700 dark:text-gray-300">
                          {entry.weekly_points.toLocaleString()}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Stats Summary */}
        {leaderboard.length > 0 && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Teams</div>
              <div className="text-3xl font-bold text-cricket-green">
                {leaderboard.length}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Highest Score</div>
              <div className="text-3xl font-bold text-cricket-green">
                {Math.max(...leaderboard.map((e) => e.total_points)).toLocaleString()}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Average Score</div>
              <div className="text-3xl font-bold text-cricket-green">
                {Math.round(
                  leaderboard.reduce((sum, e) => sum + e.total_points, 0) /
                    leaderboard.length
                ).toLocaleString()}
              </div>
            </div>
          </div>
        )}

        {/* Player & Team Performance Stats */}
        {stats && (
          <>
            {/* Top Performers */}
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-white mb-4">Top Performers</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Best Batsman */}
                {stats.best_batsman && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
                    <div className="flex items-center mb-3">
                      <span className="text-3xl mr-2">🏏</span>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Best Batsman</h3>
                    </div>
                    <div className="text-xl font-bold text-cricket-green mb-2">
                      {stats.best_batsman.player_name}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {stats.best_batsman.team_name}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Runs:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{stats.best_batsman.runs}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Average:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{stats.best_batsman.average.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Strike Rate:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{stats.best_batsman.strike_rate.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Best Bowler */}
                {stats.best_bowler && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
                    <div className="flex items-center mb-3">
                      <img src="/ball.png" alt="Bowling" className="w-8 h-8 mr-2" />
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Best Bowler</h3>
                    </div>
                    <div className="text-xl font-bold text-cricket-green mb-2">
                      {stats.best_bowler.player_name}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {stats.best_bowler.team_name}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Wickets:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{stats.best_bowler.wickets}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Average:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{stats.best_bowler.average.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Economy:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{stats.best_bowler.economy.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Best Fielder */}
                {stats.best_fielder && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
                    <div className="flex items-center mb-3">
                      <span className="text-3xl mr-2">🧤</span>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Best Fielder</h3>
                    </div>
                    <div className="text-xl font-bold text-cricket-green mb-2">
                      {stats.best_fielder.player_name}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {stats.best_fielder.team_name}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Catches:</span>
                        <span className="font-semibold text-gray-900 dark:text-white">{stats.best_fielder.catches}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Best Team */}
            {stats.best_team && (
              <div className="mt-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
                  <div className="flex items-center mb-3">
                    <span className="text-3xl mr-2">🏆</span>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Best IRL Team</h3>
                  </div>
                  <div className="text-2xl font-bold text-cricket-green mb-2">
                    {stats.best_team.team_name}
                  </div>
                  <div className="flex gap-6 text-sm">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Total Points:</span>
                      <span className="ml-2 font-semibold text-gray-900 dark:text-white">{stats.best_team.total_points.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Players:</span>
                      <span className="ml-2 font-semibold text-gray-900 dark:text-white">{stats.best_team.player_count}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Top 25 Players */}
            {stats.top_players.length > 0 && (
              <div className="mt-6">
                <h2 className="text-2xl font-bold text-white mb-4">Top 25 Players by Points</h2>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-cricket-green text-white">
                        <tr>
                          <th className="px-6 py-3 text-left text-sm font-semibold">Rank</th>
                          <th className="px-6 py-3 text-left text-sm font-semibold">Player</th>
                          <th className="px-6 py-3 text-left text-sm font-semibold">IRL Team</th>
                          <th className="px-6 py-3 text-right text-sm font-semibold">Fantasy Points</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {stats.top_players.map((player, idx) => (
                          <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-lg font-semibold text-gray-900 dark:text-white">{idx + 1}</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">{player.player_name}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-700 dark:text-gray-300">{player.team_name}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right">
                              <div className="text-lg font-bold text-cricket-green">
                                {player.total_points.toLocaleString()}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Team Details Modal */}
        {selectedTeam && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={closeModal}>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="bg-cricket-green text-white px-6 py-4 flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold">{selectedTeam.team_name}</h2>
                  <p className="text-sm opacity-90">Owner: {selectedTeam.owner_name}</p>
                </div>
                <button
                  onClick={closeModal}
                  className="text-white hover:text-gray-200 text-3xl font-bold"
                >
                  ×
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                {loadingTeam ? (
                  <div className="text-center py-8">
                    <div className="text-gray-600 dark:text-gray-400">Loading team details...</div>
                  </div>
                ) : teamPlayers.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-600 dark:text-gray-400">No players found</div>
                  </div>
                ) : (
                  <>
                    {/* Team Summary */}
                    <div className="mb-6 grid grid-cols-2 gap-4">
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <div className="text-sm text-gray-600 dark:text-gray-400">Total Points</div>
                        <div className="text-2xl font-bold text-cricket-green">
                          {selectedTeam.total_points.toLocaleString()}
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <div className="text-sm text-gray-600 dark:text-gray-400">Squad Size</div>
                        <div className="text-2xl font-bold text-cricket-green">
                          {teamPlayers.length} players
                        </div>
                      </div>
                    </div>

                    {/* Players Table */}
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-100 dark:bg-gray-700">
                          <tr>
                            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Player</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">IRL Team</th>
                            <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">Points</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                          {teamPlayers.map((player) => (
                            <tr key={player.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                                    {player.name}
                                  </span>
                                  {player.is_captain && (
                                    <span className="text-xs bg-yellow-400 text-yellow-900 px-2 py-0.5 rounded font-semibold">
                                      C
                                    </span>
                                  )}
                                  {player.is_vice_captain && (
                                    <span className="text-xs bg-gray-400 text-gray-900 px-2 py-0.5 rounded font-semibold">
                                      VC
                                    </span>
                                  )}
                                  {player.is_wicket_keeper && (
                                    <span className="text-xs bg-blue-400 text-blue-900 px-2 py-0.5 rounded font-semibold">
                                      WK
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                {player.club_name}
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span className="text-lg font-bold text-cricket-green">
                                  {player.total_points.toFixed(0)}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
