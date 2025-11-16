'use client';

import { useState, useEffect } from 'react';

interface Player {
  id: string;
  name: string;
  multiplier?: number;
}

interface PointsPreviewProps {
  players: Player[];
}

export default function PointsPreview({ players }: PointsPreviewProps) {
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [playerMultiplier, setPlayerMultiplier] = useState<number>(1.0);
  const [runs, setRuns] = useState<number>(0);
  const [balls, setBalls] = useState<number>(0);
  const [wickets, setWickets] = useState<number>(0);
  const [overs, setOvers] = useState<number>(0);
  const [runsConceded, setRunsConceded] = useState<number>(0);
  const [maidens, setMaidens] = useState<number>(0);
  const [catches, setCatches] = useState<number>(0);
  const [role, setRole] = useState<'none' | 'captain' | 'vice_captain' | 'wicketkeeper'>('none');
  const [rules, setRules] = useState<any>(null);

  useEffect(() => {
    // Load rules from public JSON
    fetch('/rules-set-1.json')
      .then(res => res.json())
      .then(data => setRules(data))
      .catch(err => console.error('Failed to load rules:', err));
  }, []);

  // Load player from URL params if present
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const playerId = params.get('player_id');
      const multiplier = params.get('multiplier');

      if (playerId && players.length > 0) {
        const player = players.find(p => p.id === playerId);
        if (player) {
          setSelectedPlayer(player);
          setPlayerMultiplier(multiplier ? parseFloat(multiplier) : player.multiplier || 1.0);
        }
      }
    }
  }, [players]);

  const calculatePoints = () => {
    if (!rules) return 0;

    let totalPoints = 0;

    // BATTING
    if (runs > 0 || balls > 0) {
      // Calculate tiered run points
      let runPoints = 0;
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

      // Apply strike rate multiplier
      if (balls > 0 && runs > 0) {
        const strikeRate = (runs / balls) * 100;
        const srMultiplier = strikeRate / 100;
        runPoints = runPoints * srMultiplier;
      }

      totalPoints += runPoints;

      // Milestone bonuses
      if (runs >= 100) {
        totalPoints += rules.batting.century_bonus;
      } else if (runs >= 50) {
        totalPoints += rules.batting.fifty_bonus;
      }
    }

    // BOWLING
    if (wickets > 0 || overs > 0) {
      // Calculate tiered wicket points
      let wicketPoints = 0;
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

      // Apply economy rate multiplier
      if (overs > 0 && wickets > 0) {
        const economyRate = runsConceded / overs;
        if (economyRate > 0) {
          const erMultiplier = 6.0 / economyRate;
          wicketPoints = wicketPoints * erMultiplier;
        }
      }

      totalPoints += wicketPoints;

      // Maidens
      totalPoints += maidens * rules.bowling.points_per_maiden;

      // Five wicket haul
      if (wickets >= 5) {
        totalPoints += rules.bowling.five_wicket_haul_bonus;
      }
    }

    // FIELDING
    let catchPoints = catches * rules.fielding.points_per_catch;

    // Apply wicketkeeper multiplier
    if (role === 'wicketkeeper' && catches > 0) {
      catchPoints = catchPoints * rules.fielding.wicketkeeper_catch_multiplier;
    }

    totalPoints += catchPoints;

    // Apply player multiplier (from state, not from player object)
    totalPoints = totalPoints * playerMultiplier;

    // Apply leadership multiplier
    if (role === 'captain') {
      totalPoints = totalPoints * rules.leadership.captain_multiplier;
    } else if (role === 'vice_captain') {
      totalPoints = totalPoints * rules.leadership.vice_captain_multiplier;
    }

    return Math.round(totalPoints * 10) / 10;
  };

  const resetCalculator = () => {
    setRuns(0);
    setBalls(0);
    setWickets(0);
    setOvers(0);
    setRunsConceded(0);
    setMaidens(0);
    setCatches(0);
    setRole('none');
    // Don't reset player multiplier when resetting stats
  };

  if (!rules) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Points Preview Calculator</h3>
        <p className="text-gray-600 dark:text-gray-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">🧮 Points Preview Calculator</h3>

      {/* Player Selection - Only show if we have players */}
      {players.length > 0 && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Select Player (Optional)</label>
          <select
            value={selectedPlayer?.id || ''}
            onChange={(e) => {
              const player = players.find(p => p.id === e.target.value);
              setSelectedPlayer(player || null);
              setPlayerMultiplier(player?.multiplier || 1.0);
              resetCalculator();
            }}
            className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="">Manual Entry</option>
            {players.map(player => (
              <option key={player.id} value={player.id}>
                {player.name} (×{player.multiplier?.toFixed(2) || '1.00'})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Always show calculator now */}
      <>
          {/* Player Multiplier Field */}
          <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border-2 border-gray-300 dark:border-gray-600">
            <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">⚙️ Player Multiplier</h4>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                Multiplier (0.69 - 5.00)
              </label>
              <input
                type="number"
                min="0.69"
                max="5.0"
                step="0.01"
                value={playerMultiplier}
                onChange={(e) => setPlayerMultiplier(Math.max(0.69, Math.min(5.0, parseFloat(e.target.value) || 1.0)))}
                className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Lower = better IRL player (handicapped), Higher = weaker IRL player (boosted)
              </p>
            </div>
          </div>

          {/* Batting Section */}
          <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">🏏 Batting</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Runs</label>
                <input
                  type="number"
                  min="0"
                  value={runs}
                  onChange={(e) => setRuns(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Balls</label>
                <input
                  type="number"
                  min="0"
                  value={balls}
                  onChange={(e) => setBalls(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>
          </div>

          {/* Bowling Section */}
          <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <img src="/ball.png" alt="Bowling" className="inline w-5 h-5" />
              Bowling
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Wickets</label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={wickets}
                  onChange={(e) => setWickets(Math.max(0, Math.min(10, parseInt(e.target.value) || 0)))}
                  className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Overs</label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={overs}
                  onChange={(e) => setOvers(Math.max(0, parseFloat(e.target.value) || 0))}
                  className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Runs Conceded</label>
                <input
                  type="number"
                  min="0"
                  value={runsConceded}
                  onChange={(e) => setRunsConceded(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Maidens</label>
                <input
                  type="number"
                  min="0"
                  value={maidens}
                  onChange={(e) => setMaidens(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>
          </div>

          {/* Fielding Section */}
          <div className="mb-4 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <img src="/catch.png" alt="Fielding" className="inline w-5 h-5" />
              Fielding
            </h4>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Catches</label>
              <input
                type="number"
                min="0"
                value={catches}
                onChange={(e) => setCatches(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          </div>

          {/* Role Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Fantasy Team Role</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setRole('none')}
                className={`px-3 py-2 text-sm rounded-md border ${
                  role === 'none'
                    ? 'bg-gray-600 text-white border-gray-600'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
                }`}
              >
                None (1.0x)
              </button>
              <button
                onClick={() => setRole('captain')}
                className={`px-3 py-2 text-sm rounded-md border ${
                  role === 'captain'
                    ? 'bg-cricket-green text-white border-cricket-green'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
                }`}
              >
                Captain (2.0x)
              </button>
              <button
                onClick={() => setRole('vice_captain')}
                className={`px-3 py-2 text-sm rounded-md border ${
                  role === 'vice_captain'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
                }`}
              >
                Vice Captain (1.5x)
              </button>
              <button
                onClick={() => setRole('wicketkeeper')}
                className={`px-3 py-2 text-sm rounded-md border ${
                  role === 'wicketkeeper'
                    ? 'bg-yellow-600 text-white border-yellow-600'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
                }`}
              >
                Wicketkeeper (2x catches)
              </button>
            </div>
          </div>

          {/* Result */}
          <div className="mt-4 p-4 bg-gradient-to-r from-cricket-green to-green-600 rounded-lg">
            <div className="text-center">
              <div className="text-sm text-white/90 mb-1">Projected Fantasy Points</div>
              <div className="text-4xl font-bold text-white">{calculatePoints()}</div>
              <div className="text-xs text-white/80 mt-2">
                Player Multiplier: ×{playerMultiplier.toFixed(2)}
                {role === 'captain' && ' • Captain: ×2.0'}
                {role === 'vice_captain' && ' • Vice Captain: ×1.5'}
                {role === 'wicketkeeper' && ' • WK: 2x catches'}
              </div>
            </div>
          </div>

          {/* Reset Button */}
          <button
            onClick={resetCalculator}
            className="mt-3 w-full px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Reset Calculator
          </button>
        </>
    </div>
  );
}
