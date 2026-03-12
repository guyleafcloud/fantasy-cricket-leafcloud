'use client';

import { DetailedPlayerStats } from '@/types';

interface PlayerPerformanceCardProps {
  player: DetailedPlayerStats;
  selected?: boolean;
  onSelect?: (playerId: string) => void;
  showComparison?: boolean;
}

export default function PlayerPerformanceCard({
  player,
  selected = false,
  onSelect,
  showComparison = false
}: PlayerPerformanceCardProps) {

  // Helper: Get performance color based on value ranges
  const getBattingColor = (avg: number, sr: number) => {
    if (avg >= 40 && sr >= 130) return 'text-green-600 dark:text-green-400'; // Excellent
    if (avg >= 25 && sr >= 100) return 'text-blue-600 dark:text-blue-400'; // Good
    if (avg >= 15) return 'text-amber-600 dark:text-amber-400'; // Average
    return 'text-red-600 dark:text-red-400'; // Poor
  };

  const getBowlingColor = (econ: number | null, wickets: number) => {
    if (!econ) return 'text-gray-600 dark:text-gray-400';
    if (econ <= 6 && wickets >= 10) return 'text-green-600 dark:text-green-400'; // Excellent
    if (econ <= 7.5 && wickets >= 5) return 'text-blue-600 dark:text-blue-400'; // Good
    if (econ <= 9) return 'text-amber-600 dark:text-amber-400'; // Average
    return 'text-red-600 dark:text-red-400'; // Poor
  };

  const getFieldingColor = (total: number) => {
    if (total >= 10) return 'text-green-600 dark:text-green-400';
    if (total >= 5) return 'text-blue-600 dark:text-blue-400';
    if (total >= 2) return 'text-amber-600 dark:text-amber-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getMultiplierColor = (status: string) => {
    if (status === 'strengthening') return 'text-green-600 dark:text-green-400';
    if (status === 'weakening') return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'improving') return '📈';
    if (trend === 'declining') return '📉';
    return '➡️';
  };

  const getRoleIcon = (role: string) => {
    if (!role) return '👤'; // Handle null/undefined
    if (role.includes('BAT')) return '🏏';
    if (role.includes('BOWL')) return '⚾';
    if (role.includes('ALL')) return '🏏⚾';
    if (role.includes('KEEP')) return '🧤';
    return '👤';
  };

  const totalFielding = player.fielding.catches + player.fielding.run_outs + player.fielding.stumpings;
  const battingColor = getBattingColor(player.batting.average, player.batting.strike_rate);
  const bowlingColor = getBowlingColor(player.bowling.economy, player.bowling.wickets);
  const fieldingColor = getFieldingColor(totalFielding);
  const multiplierColor = getMultiplierColor(player.multiplier_info.status);

  return (
    <div
      className={`
        rounded-lg border p-4 mb-3 transition-all
        ${selected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md'
          : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-sm'
        }
        ${showComparison && onSelect ? 'cursor-pointer' : ''}
      `}
      onClick={() => showComparison && onSelect && onSelect(player.player_id)}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-lg">{getRoleIcon(player.player_role)}</span>
            <h3 className="font-semibold text-lg">{player.player_name}</h3>
            {player.is_captain && <span>👑</span>}
            {player.is_vice_captain && <span>⭐</span>}
            {player.is_wicket_keeper && <span>🧤</span>}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{player.club_name}</p>
        </div>

        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {player.total_points}
          </div>
          <div className="text-xs text-gray-500">
            {player.matches_played} matches
          </div>
        </div>
      </div>

      {/* Stats Tables - Mobile First Layout */}
      <div className="space-y-3">

        {/* Batting Stats */}
        {player.matches_played > 0 && player.batting.runs > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium">🏏 Batting</span>
              <span className={`text-xs font-semibold ${battingColor}`}>
                {player.batting.average.toFixed(1)} avg @ {player.batting.strike_rate.toFixed(1)} SR
              </span>
            </div>
            <div className="grid grid-cols-5 gap-1 text-xs">
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.batting.runs}</div>
                <div className="text-gray-500">Runs</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.batting.balls_faced}</div>
                <div className="text-gray-500">Balls</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.batting.fours}/{player.batting.sixes}</div>
                <div className="text-gray-500">4s/6s</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.batting.fifties}/{player.batting.hundreds}</div>
                <div className="text-gray-500">50s/100s</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.batting.highest_score}</div>
                <div className="text-gray-500">HS</div>
              </div>
            </div>
          </div>
        )}

        {/* Bowling Stats */}
        {player.matches_played > 0 && player.bowling.wickets > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium">⚾ Bowling</span>
              <span className={`text-xs font-semibold ${bowlingColor}`}>
                {player.bowling.wickets} wkts @ {player.bowling.economy?.toFixed(2) || '0.00'} econ
              </span>
            </div>
            <div className="grid grid-cols-4 gap-1 text-xs">
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.bowling.wickets}</div>
                <div className="text-gray-500">Wickets</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.bowling.overs.toFixed(1)}</div>
                <div className="text-gray-500">Overs</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.bowling.runs_conceded}</div>
                <div className="text-gray-500">Runs</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.bowling.maidens}</div>
                <div className="text-gray-500">Maidens</div>
              </div>
            </div>
          </div>
        )}

        {/* Fielding Stats */}
        {player.matches_played > 0 && totalFielding > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium">🧤 Fielding</span>
              <span className={`text-xs font-semibold ${fieldingColor}`}>
                {totalFielding} total
              </span>
            </div>
            <div className="grid grid-cols-3 gap-1 text-xs">
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.fielding.catches}</div>
                <div className="text-gray-500">Catches</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.fielding.run_outs}</div>
                <div className="text-gray-500">Run-outs</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-1 rounded text-center">
                <div className="font-semibold">{player.fielding.stumpings}</div>
                <div className="text-gray-500">Stumpings</div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Form & Multiplier */}
        {player.matches_played > 0 && (
          <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-gray-700 text-xs">
            <div className="flex items-center gap-2">
              <span>{getTrendIcon(player.recent_form.trend)}</span>
              <span className="text-gray-600 dark:text-gray-400">
                Form: {player.recent_form.last_n_average.toFixed(1)} pts/match
              </span>
            </div>
            <div className={`font-medium ${multiplierColor}`}>
              {player.multiplier_info.starting_multiplier.toFixed(2)}x → {player.multiplier_info.current_multiplier.toFixed(2)}x
            </div>
          </div>
        )}

        {/* Points Breakdown */}
        {player.matches_played > 0 && (
          <div className="grid grid-cols-3 gap-1 text-xs pt-2">
            <div className="text-center">
              <div className="text-gray-500">Batting</div>
              <div className="font-semibold text-green-600 dark:text-green-400">
                {player.points_breakdown.batting_points.toFixed(1)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">Bowling</div>
              <div className="font-semibold text-blue-600 dark:text-blue-400">
                {player.points_breakdown.bowling_points.toFixed(1)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-500">Fielding</div>
              <div className="font-semibold text-amber-600 dark:text-amber-400">
                {player.points_breakdown.fielding_points.toFixed(1)}
              </div>
            </div>
          </div>
        )}

        {/* No Data State */}
        {player.matches_played === 0 && (
          <div className="text-center py-2 text-sm text-gray-500">
            No performance data yet
          </div>
        )}
      </div>

      {/* Comparison Checkbox */}
      {showComparison && (
        <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onSelect && onSelect(player.player_id)}
              className="rounded"
            />
            <span>Select for comparison</span>
          </label>
        </div>
      )}
    </div>
  );
}
