'use client';

import { DetailedPlayerStats } from '@/types';

interface PlayerComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  player1: DetailedPlayerStats | null;
  player2: DetailedPlayerStats | null;
}

export default function PlayerComparisonModal({
  isOpen,
  onClose,
  player1,
  player2
}: PlayerComparisonModalProps) {

  if (!isOpen || !player1 || !player2) return null;

  // Helper to get better/worse/equal indicator
  const getComparison = (val1: number, val2: number, higherIsBetter: boolean = true) => {
    if (val1 === val2) return '=';
    const isP1Better = higherIsBetter ? val1 > val2 : val1 < val2;
    return isP1Better ? '🟢' : '🔴';
  };

  const ComparisonRow = ({
    label,
    val1,
    val2,
    higherIsBetter = true,
    formatter = (v: number) => v.toFixed(1)
  }: {
    label: string;
    val1: number;
    val2: number;
    higherIsBetter?: boolean;
    formatter?: (v: number) => string;
  }) => (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      <td className="py-2 text-center">
        {getComparison(val1, val2, higherIsBetter)}
      </td>
      <td className="py-2 font-semibold text-right">{formatter(val1)}</td>
      <td className="py-2 px-4 text-gray-600 dark:text-gray-400">{label}</td>
      <td className="py-2 font-semibold text-left">{formatter(val2)}</td>
      <td className="py-2 text-center">
        {getComparison(val2, val1, higherIsBetter)}
      </td>
    </tr>
  );

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">

        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-2xl font-bold">Player Comparison</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Player Headers */}
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h3 className="font-bold text-lg">{player1.player_name}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{player1.club_name}</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-2">
                {player1.total_points}
              </p>
              <p className="text-xs text-gray-500">{player1.matches_played} matches</p>
            </div>

            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h3 className="font-bold text-lg">{player2.player_name}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{player2.club_name}</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
                {player2.total_points}
              </p>
              <p className="text-xs text-gray-500">{player2.matches_played} matches</p>
            </div>
          </div>
        </div>

        {/* Comparison Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">

            {/* Overall Stats */}
            <div>
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <span>📊</span>
                <span>Overall Performance</span>
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <ComparisonRow
                    label="Total Points"
                    val1={player1.total_points}
                    val2={player2.total_points}
                  />
                  <ComparisonRow
                    label="Matches Played"
                    val1={player1.matches_played}
                    val2={player2.matches_played}
                  />
                  <ComparisonRow
                    label="Avg Points/Match"
                    val1={player1.matches_played > 0 ? player1.total_points / player1.matches_played : 0}
                    val2={player2.matches_played > 0 ? player2.total_points / player2.matches_played : 0}
                  />
                  <ComparisonRow
                    label="Recent Form (last 3)"
                    val1={player1.recent_form.last_n_average}
                    val2={player2.recent_form.last_n_average}
                  />
                </tbody>
              </table>
            </div>

            {/* Batting Stats */}
            <div>
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <span>🏏</span>
                <span>Batting</span>
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <ComparisonRow
                    label="Runs"
                    val1={player1.batting.runs}
                    val2={player2.batting.runs}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Average"
                    val1={player1.batting.average}
                    val2={player2.batting.average}
                  />
                  <ComparisonRow
                    label="Strike Rate"
                    val1={player1.batting.strike_rate}
                    val2={player2.batting.strike_rate}
                  />
                  <ComparisonRow
                    label="Fours"
                    val1={player1.batting.fours}
                    val2={player2.batting.fours}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Sixes"
                    val1={player1.batting.sixes}
                    val2={player2.batting.sixes}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Fifties"
                    val1={player1.batting.fifties}
                    val2={player2.batting.fifties}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Hundreds"
                    val1={player1.batting.hundreds}
                    val2={player2.batting.hundreds}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Highest Score"
                    val1={player1.batting.highest_score}
                    val2={player2.batting.highest_score}
                    formatter={(v) => v.toString()}
                  />
                </tbody>
              </table>
            </div>

            {/* Bowling Stats */}
            <div>
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <span>⚾</span>
                <span>Bowling</span>
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <ComparisonRow
                    label="Wickets"
                    val1={player1.bowling.wickets}
                    val2={player2.bowling.wickets}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Overs"
                    val1={player1.bowling.overs}
                    val2={player2.bowling.overs}
                  />
                  <ComparisonRow
                    label="Economy"
                    val1={player1.bowling.economy || 0}
                    val2={player2.bowling.economy || 0}
                    higherIsBetter={false}
                  />
                  <ComparisonRow
                    label="Average"
                    val1={player1.bowling.average || 0}
                    val2={player2.bowling.average || 0}
                    higherIsBetter={false}
                  />
                  <ComparisonRow
                    label="Maidens"
                    val1={player1.bowling.maidens}
                    val2={player2.bowling.maidens}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="5-Wicket Hauls"
                    val1={player1.bowling.five_wicket_hauls}
                    val2={player2.bowling.five_wicket_hauls}
                    formatter={(v) => v.toString()}
                  />
                </tbody>
              </table>
            </div>

            {/* Fielding Stats */}
            <div>
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <span>🧤</span>
                <span>Fielding</span>
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <ComparisonRow
                    label="Catches"
                    val1={player1.fielding.catches}
                    val2={player2.fielding.catches}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Run-outs"
                    val1={player1.fielding.run_outs}
                    val2={player2.fielding.run_outs}
                    formatter={(v) => v.toString()}
                  />
                  <ComparisonRow
                    label="Stumpings"
                    val1={player1.fielding.stumpings}
                    val2={player2.fielding.stumpings}
                    formatter={(v) => v.toString()}
                  />
                </tbody>
              </table>
            </div>

            {/* Points Breakdown */}
            <div>
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <span>📈</span>
                <span>Points Breakdown</span>
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <ComparisonRow
                    label="Batting Points"
                    val1={player1.points_breakdown.batting_points}
                    val2={player2.points_breakdown.batting_points}
                  />
                  <ComparisonRow
                    label="Bowling Points"
                    val1={player1.points_breakdown.bowling_points}
                    val2={player2.points_breakdown.bowling_points}
                  />
                  <ComparisonRow
                    label="Fielding Points"
                    val1={player1.points_breakdown.fielding_points}
                    val2={player2.points_breakdown.fielding_points}
                  />
                </tbody>
              </table>
            </div>

            {/* Multiplier Info */}
            <div>
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <span>⚡</span>
                <span>Multiplier Status</span>
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <ComparisonRow
                    label="Current Multiplier"
                    val1={player1.multiplier_info.current_multiplier}
                    val2={player2.multiplier_info.current_multiplier}
                    formatter={(v) => `${v.toFixed(2)}x`}
                  />
                  <ComparisonRow
                    label="Multiplier Drift"
                    val1={player1.multiplier_info.drift}
                    val2={player2.multiplier_info.drift}
                    formatter={(v) => (v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2))}
                  />
                </tbody>
              </table>
            </div>

          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
