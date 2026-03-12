'use client';

import { useState, useEffect } from 'react';

interface TeamAnalysisData {
  most_balanced_team: {
    team_name: string;
    owner_name: string;
    balance_score: number;
    std_dev: number;
    min_player_points: number;
    max_player_points: number;
    avg_player_points: number;
    player_count: number;
  } | null;
  best_captain_pick: {
    team_name: string;
    owner_name: string;
    captain_name: string;
    captain_points: number;
    captain_contribution_pct: number;
    total_team_points: number;
  } | null;
  most_consistent_team: {
    team_name: string;
    owner_name: string;
    std_dev: number;
    avg_player_points: number;
    player_count: number;
  } | null;
}

interface TeamAnalysisProps {
  leagueId: string;
}

export default function TeamAnalysis({ leagueId }: TeamAnalysisProps) {
  const [analysis, setAnalysis] = useState<TeamAnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalysis();
  }, [leagueId]);

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('admin_token');
      const response = await fetch(
        `/api/leagues/${leagueId}/team-analysis`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch team analysis');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          {error}
        </div>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white flex items-center gap-2">
        <span>📊</span>
        <span>Team Analysis</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Most Balanced Team */}
        {analysis.most_balanced_team && (
          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-5 border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">⚖️</span>
              <h3 className="font-bold text-green-900 dark:text-green-100">Most Balanced Team</h3>
            </div>

            <div className="mb-3">
              <div className="text-lg font-bold text-green-700 dark:text-green-300">
                {analysis.most_balanced_team.team_name}
              </div>
              <div className="text-sm text-green-600 dark:text-green-400">
                by {analysis.most_balanced_team.owner_name}
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-green-700 dark:text-green-300">Balance Score:</span>
                <span className="font-semibold text-green-900 dark:text-green-100">
                  {analysis.most_balanced_team.balance_score.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700 dark:text-green-300">Point Range:</span>
                <span className="font-semibold text-green-900 dark:text-green-100">
                  {analysis.most_balanced_team.min_player_points.toFixed(0)} - {analysis.most_balanced_team.max_player_points.toFixed(0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700 dark:text-green-300">Avg per Player:</span>
                <span className="font-semibold text-green-900 dark:text-green-100">
                  {analysis.most_balanced_team.avg_player_points.toFixed(1)} pts
                </span>
              </div>
              <div className="mt-3 pt-3 border-t border-green-300 dark:border-green-700 text-xs text-green-600 dark:text-green-400">
                All {analysis.most_balanced_team.player_count} players contributing evenly
                (σ = {analysis.most_balanced_team.std_dev.toFixed(1)})
              </div>
            </div>
          </div>
        )}

        {/* Best Captain Pick */}
        {analysis.best_captain_pick && (
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-5 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">👑</span>
              <h3 className="font-bold text-blue-900 dark:text-blue-100">Best Captain Pick</h3>
            </div>

            <div className="mb-3">
              <div className="text-lg font-bold text-blue-700 dark:text-blue-300">
                {analysis.best_captain_pick.team_name}
              </div>
              <div className="text-sm text-blue-600 dark:text-blue-400">
                by {analysis.best_captain_pick.owner_name}
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="bg-blue-100 dark:bg-blue-900/40 rounded p-2 mb-2">
                <div className="font-bold text-blue-900 dark:text-blue-100">
                  {analysis.best_captain_pick.captain_name}
                </div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {analysis.best_captain_pick.captain_points.toFixed(1)} pts
                </div>
              </div>

              <div className="flex justify-between">
                <span className="text-blue-700 dark:text-blue-300">Contribution:</span>
                <span className="font-semibold text-blue-900 dark:text-blue-100">
                  {analysis.best_captain_pick.captain_contribution_pct.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-700 dark:text-blue-300">Team Total:</span>
                <span className="font-semibold text-blue-900 dark:text-blue-100">
                  {analysis.best_captain_pick.total_team_points.toFixed(1)} pts
                </span>
              </div>

              <div className="mt-3 pt-3 border-t border-blue-300 dark:border-blue-700 text-xs text-blue-600 dark:text-blue-400">
                Captain earning with 2x bonus applied
              </div>
            </div>
          </div>
        )}

        {/* Most Consistent Team */}
        {analysis.most_consistent_team && (
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-5 border border-purple-200 dark:border-purple-800">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">📈</span>
              <h3 className="font-bold text-purple-900 dark:text-purple-100">Most Consistent Team</h3>
            </div>

            <div className="mb-3">
              <div className="text-lg font-bold text-purple-700 dark:text-purple-300">
                {analysis.most_consistent_team.team_name}
              </div>
              <div className="text-sm text-purple-600 dark:text-purple-400">
                by {analysis.most_consistent_team.owner_name}
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-purple-700 dark:text-purple-300">Std Deviation:</span>
                <span className="font-semibold text-purple-900 dark:text-purple-100">
                  {analysis.most_consistent_team.std_dev.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-purple-700 dark:text-purple-300">Avg per Player:</span>
                <span className="font-semibold text-purple-900 dark:text-purple-100">
                  {analysis.most_consistent_team.avg_player_points.toFixed(1)} pts
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-purple-700 dark:text-purple-300">Squad Size:</span>
                <span className="font-semibold text-purple-900 dark:text-purple-100">
                  {analysis.most_consistent_team.player_count} players
                </span>
              </div>

              <div className="mt-3 pt-3 border-t border-purple-300 dark:border-purple-700 text-xs text-purple-600 dark:text-purple-400">
                Lowest variance in player performance
              </div>
            </div>
          </div>
        )}
      </div>

      {/* No Data State */}
      {!analysis.most_balanced_team && !analysis.best_captain_pick && !analysis.most_consistent_team && (
        <div className="text-center py-12 text-gray-500">
          Not enough data yet for team analysis
        </div>
      )}
    </div>
  );
}
