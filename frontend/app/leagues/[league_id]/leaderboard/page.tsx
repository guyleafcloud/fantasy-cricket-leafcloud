'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

interface LeaderboardEntry {
  rank: number;
  team_name: string;
  owner_name: string;
  total_points: number;
  weekly_points: number;
}

export default function LeaderboardPage() {
  const params = useParams();
  const router = useRouter();
  const league_id = params.league_id as string;

  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/leagues/${league_id}/leaderboard`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch leaderboard');
        }

        const data = await response.json();
        setLeaderboard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (league_id) {
      fetchLeaderboard();
    }
  }, [league_id]);

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
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {entry.team_name}
                        </div>
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
      </div>
    </div>
  );
}
