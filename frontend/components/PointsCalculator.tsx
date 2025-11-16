'use client';

import { useState, useEffect } from 'react';

interface FantasyRules {
  batting: {
    run_tiers?: Array<{
      min: number;
      max: number;
      points_per_run: number;
    }>;
    points_per_run?: number; // Fallback for legacy rules
    strike_rate_applies_as_multiplier: boolean;
    fifty_bonus: number;
    century_bonus: number;
    duck_penalty: number;
  };
  bowling: {
    wicket_tiers?: Array<{
      min: number;
      max: number;
      points_per_wicket: number;
    }>;
    points_per_wicket?: number; // Fallback for legacy rules
    economy_rate_applies_as_multiplier: boolean;
    points_per_maiden: number;
    five_wicket_haul_bonus: number;
  };
  fielding: {
    points_per_catch: number;
    points_per_stumping: number;
    points_per_runout: number;
    wicketkeeper_catch_multiplier: number;
  };
  player_multipliers: {
    min: number;
    neutral: number;
    max: number;
  };
  leadership: {
    captain_multiplier: number;
    vice_captain_multiplier: number;
    wicketkeeper_multiplier: number;
  };
}

interface PointsCalculatorProps {
  playersList?: Array<{
    id: string;
    name: string;
    player_type: string;
  }>;
}

export default function PointsCalculator({ playersList = [] }: PointsCalculatorProps) {
  const [selectedPlayer, setSelectedPlayer] = useState<string>('');
  const [playerName, setPlayerName] = useState<string>('');
  const [rules, setRules] = useState<FantasyRules | null>(null);

  // Batting stats
  const [runs, setRuns] = useState<number>(0);
  const [ballsFaced, setBallsFaced] = useState<number>(0);
  const [isOut, setIsOut] = useState<boolean>(false);

  // Bowling stats
  const [wickets, setWickets] = useState<number>(0);
  const [runsConceded, setRunsConceded] = useState<number>(0);
  const [overs, setOvers] = useState<number>(0);
  const [maidens, setMaidens] = useState<number>(0);

  // Fielding stats
  const [catches, setCatches] = useState<number>(0);
  const [stumpings, setStumpings] = useState<number>(0);
  const [runouts, setRunouts] = useState<number>(0);

  // Multipliers
  const [isCaptain, setIsCaptain] = useState<boolean>(false);
  const [isViceCaptain, setIsViceCaptain] = useState<boolean>(false);
  const [isWicketkeeper, setIsWicketkeeper] = useState<boolean>(false);

  // Load rules from JSON file
  useEffect(() => {
    fetch('/rules-set-1.json')
      .then(res => res.json())
      .then(data => setRules(data))
      .catch(err => console.error('Failed to load rules:', err));
  }, []);

  const calculatePoints = () => {
    if (!rules) return { breakdown: [], basePoints: 0, leadershipMultiplier: 1, finalPoints: 0 };

    let points = 0;
    const breakdown: Array<{label: string, value: number, type: string}> = [];

    // BATTING
    if (runs > 0 || ballsFaced > 0) {
      // Calculate tiered run points
      let runPoints = 0;
      if (runs > 0 && 'run_tiers' in rules.batting && Array.isArray(rules.batting.run_tiers)) {
        let runsCounted = 0;
        for (const tier of rules.batting.run_tiers) {
          if (runs >= tier.min) {
            const tierStart = Math.max(runsCounted + 1, tier.min);
            const tierEnd = Math.min(runs, tier.max);
            const runsInTier = tierEnd - tierStart + 1;

            if (runsInTier > 0) {
              runPoints += runsInTier * tier.points_per_run;
              runsCounted = tierEnd;
            }

            if (runsCounted >= runs) break;
          }
        }
        breakdown.push({ label: `Tiered runs (${runs} runs)`, value: runPoints, type: 'batting' });
      }

      // Strike rate multiplier
      if (ballsFaced > 0 && runs > 0) {
        const strikeRate = (runs / ballsFaced) * 100;
        const srMultiplier = strikeRate / 100;
        const srBonus = runPoints * (srMultiplier - 1);
        runPoints = runPoints * srMultiplier;

        breakdown.push({
          label: `SR multiplier (${strikeRate.toFixed(1)} SR = ${srMultiplier.toFixed(2)}x)`,
          value: srBonus,
          type: 'batting'
        });
      }

      points += runPoints;

      // Milestone bonuses
      if (runs >= 100) {
        points += rules.batting.century_bonus;
        breakdown.push({ label: `Century bonus`, value: rules.batting.century_bonus, type: 'batting' });
      } else if (runs >= 50) {
        points += rules.batting.fifty_bonus;
        breakdown.push({ label: `Fifty bonus`, value: rules.batting.fifty_bonus, type: 'batting' });
      }

      // Duck penalty
      if (isOut && runs === 0) {
        points += rules.batting.duck_penalty;
        breakdown.push({ label: `Duck penalty`, value: rules.batting.duck_penalty, type: 'batting' });
      }
    }

    // BOWLING
    if (wickets > 0 || overs > 0 || maidens > 0) {
      // Calculate tiered wicket points
      let wicketPoints = 0;
      if (wickets > 0 && 'wicket_tiers' in rules.bowling && Array.isArray(rules.bowling.wicket_tiers)) {
        let wicketNumber = 1;
        for (const tier of rules.bowling.wicket_tiers) {
          while (wicketNumber <= wickets && wicketNumber <= tier.max) {
            if (wicketNumber >= tier.min) {
              wicketPoints += tier.points_per_wicket;
            }
            wicketNumber++;
          }
          if (wicketNumber > wickets) break;
        }
        breakdown.push({ label: `Tiered wickets (${wickets} wickets)`, value: wicketPoints, type: 'bowling' });

        // Economy rate multiplier
        if (overs > 0) {
          const economyRate = runsConceded / overs;
          const erMultiplier = 6.0 / economyRate;
          const erBonus = wicketPoints * (erMultiplier - 1);
          wicketPoints = wicketPoints * erMultiplier;

          breakdown.push({
            label: `ER multiplier (${economyRate.toFixed(2)} ER = ${erMultiplier.toFixed(2)}x)`,
            value: erBonus,
            type: 'bowling'
          });
        }

        points += wicketPoints;
      }

      // Maidens
      if (maidens > 0) {
        const maidenPoints = maidens * rules.bowling.points_per_maiden;
        points += maidenPoints;
        breakdown.push({ label: `Maidens (${maidens} × ${rules.bowling.points_per_maiden})`, value: maidenPoints, type: 'bowling' });
      }

      // Five wicket haul
      if (wickets >= 5) {
        points += rules.bowling.five_wicket_haul_bonus;
        breakdown.push({ label: `5-wicket haul bonus`, value: rules.bowling.five_wicket_haul_bonus, type: 'bowling' });
      }
    }

    // FIELDING
    if (catches > 0) {
      let catchPoints = catches * rules.fielding.points_per_catch;

      // Apply wicketkeeper multiplier to catches
      if (isWicketkeeper) {
        const wkMultiplier = rules.fielding.wicketkeeper_catch_multiplier;
        breakdown.push({
          label: `Catches (${catches} × ${rules.fielding.points_per_catch})`,
          value: catches * rules.fielding.points_per_catch,
          type: 'fielding'
        });
        const wkBonus = catchPoints * (wkMultiplier - 1);
        breakdown.push({
          label: `Wicketkeeper catch bonus (${wkMultiplier}x)`,
          value: wkBonus,
          type: 'fielding'
        });
        catchPoints = catchPoints * wkMultiplier;
      } else {
        breakdown.push({
          label: `Catches (${catches} × ${rules.fielding.points_per_catch})`,
          value: catchPoints,
          type: 'fielding'
        });
      }

      points += catchPoints;
    }

    if (stumpings > 0) {
      const stumpingPoints = stumpings * rules.fielding.points_per_stumping;
      points += stumpingPoints;
      breakdown.push({ label: `Stumpings (${stumpings} × ${rules.fielding.points_per_stumping})`, value: stumpingPoints, type: 'fielding' });
    }

    if (runouts > 0) {
      const runoutPoints = runouts * rules.fielding.points_per_runout;
      points += runoutPoints;
      breakdown.push({ label: `Run outs (${runouts} × ${rules.fielding.points_per_runout})`, value: runoutPoints, type: 'fielding' });
    }

    // Leadership multiplier
    let leadershipMultiplier = 1.0;
    if (isCaptain) {
      leadershipMultiplier = rules.leadership.captain_multiplier;
    } else if (isViceCaptain) {
      leadershipMultiplier = rules.leadership.vice_captain_multiplier;
    }

    const finalPoints = Math.floor(points * leadershipMultiplier);

    return {
      breakdown,
      basePoints: Math.floor(points),
      leadershipMultiplier,
      finalPoints: Math.max(0, finalPoints)
    };
  };

  const result = calculatePoints();

  if (!rules) {
    return <div className="p-4 text-center">Loading rules...</div>;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Fantasy Points Calculator</h2>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-6">
          {/* Batting Stats */}
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">🏏 Batting</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Runs</label>
                <input
                  type="number"
                  min="0"
                  value={runs}
                  onChange={(e) => setRuns(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Balls Faced</label>
                <input
                  type="number"
                  min="0"
                  value={ballsFaced}
                  onChange={(e) => setBallsFaced(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isOut"
                  checked={isOut}
                  onChange={(e) => setIsOut(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="isOut" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Batsman was dismissed
                </label>
              </div>
            </div>
          </div>

          {/* Bowling Stats */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">⚾ Bowling</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Wickets</label>
                <input
                  type="number"
                  min="0"
                  value={wickets}
                  onChange={(e) => setWickets(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Overs Bowled</label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={overs}
                  onChange={(e) => setOvers(Math.max(0, parseFloat(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Runs Conceded</label>
                <input
                  type="number"
                  min="0"
                  value={runsConceded}
                  onChange={(e) => setRunsConceded(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Maidens</label>
                <input
                  type="number"
                  min="0"
                  value={maidens}
                  onChange={(e) => setMaidens(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>
          </div>

          {/* Fielding Stats */}
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">🥎 Fielding</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Catches</label>
                <input
                  type="number"
                  min="0"
                  value={catches}
                  onChange={(e) => setCatches(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Stumpings</label>
                <input
                  type="number"
                  min="0"
                  value={stumpings}
                  onChange={(e) => setStumpings(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Run Outs</label>
                <input
                  type="number"
                  min="0"
                  value={runouts}
                  onChange={(e) => setRunouts(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div className="flex items-center pt-2">
                <input
                  type="checkbox"
                  id="wicketkeeper"
                  checked={isWicketkeeper}
                  onChange={(e) => setIsWicketkeeper(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="wicketkeeper" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  🧤 Wicketkeeper ({rules.fielding.wicketkeeper_catch_multiplier}x catch points)
                </label>
              </div>
            </div>
          </div>

          {/* Leadership Multipliers */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">👑 Leadership</h3>
            <div className="space-y-2">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="captain"
                  checked={isCaptain}
                  onChange={(e) => {
                    setIsCaptain(e.target.checked);
                    if (e.target.checked) setIsViceCaptain(false);
                  }}
                  className="mr-2"
                />
                <label htmlFor="captain" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Captain ({rules.leadership.captain_multiplier}x points)
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="viceCaptain"
                  checked={isViceCaptain}
                  onChange={(e) => {
                    setIsViceCaptain(e.target.checked);
                    if (e.target.checked) setIsCaptain(false);
                  }}
                  className="mr-2"
                />
                <label htmlFor="viceCaptain" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Vice-Captain ({rules.leadership.vice_captain_multiplier}x points)
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-cricket-green to-green-600 text-white rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Total Points</h3>
            <div className="text-5xl font-bold">{result.finalPoints}</div>
            {result.leadershipMultiplier > 1 && (
              <div className="text-sm mt-2 opacity-90">
                Base: {result.basePoints} × {result.leadershipMultiplier}x = {result.finalPoints}
              </div>
            )}
          </div>

          {/* Points Breakdown */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Points Breakdown</h3>

            {result.breakdown.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Enter stats to see breakdown</p>
            ) : (
              <div className="space-y-2">
                {result.breakdown.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm">
                    <span className={`
                      ${item.type === 'batting' ? 'text-green-700 dark:text-green-400' : ''}
                      ${item.type === 'bowling' ? 'text-blue-700 dark:text-blue-400' : ''}
                      ${item.type === 'fielding' ? 'text-purple-700 dark:text-purple-400' : ''}
                    `}>
                      {item.label}
                    </span>
                    <span className={`font-semibold ${item.value >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {item.value >= 0 ? '+' : ''}{item.value.toFixed(1)}
                    </span>
                  </div>
                ))}

                {result.leadershipMultiplier > 1 && (
                  <div className="border-t pt-2 mt-2">
                    <div className="flex justify-between text-sm font-semibold">
                      <span className="text-yellow-700 dark:text-yellow-400">
                        {isCaptain ? 'Captain' : 'Vice-Captain'} Multiplier ({result.leadershipMultiplier}x)
                      </span>
                      <span className="text-yellow-700 dark:text-yellow-400">
                        ×{result.leadershipMultiplier}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-sm">
            <p className="text-gray-700 dark:text-gray-300">
              <strong>Note:</strong> This calculator uses rules from <code>rules-set-1</code> with:
            </p>
            <ul className="text-gray-700 dark:text-gray-300 list-disc list-inside mt-2 space-y-1">
              <li><strong>Tiered run points:</strong> 1-30 (1.0), 31-49 (1.25), 50-99 (1.5), 100+ (1.75 pts/run)</li>
              <li><strong>Tiered wicket points:</strong> 1-2 (15), 3-4 (20), 5-10 (30 pts each)</li>
              <li><strong>Strike Rate & Economy Rate:</strong> Applied as multipliers</li>
              <li><strong>Wicketkeeper bonus:</strong> 2x catch points</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
