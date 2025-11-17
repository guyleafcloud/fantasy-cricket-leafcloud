'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import PointsPreview from '@/components/PointsPreview';

interface Player {
  id: string;
  name: string;
  multiplier?: number;
}

function CalculatorContent() {
  const [players, setPlayers] = useState<Player[]>([]);
  const searchParams = useSearchParams();

  useEffect(() => {
    // Check if player was passed via URL params
    const playerId = searchParams.get('player_id');
    const playerName = searchParams.get('player_name');
    const multiplier = searchParams.get('multiplier');

    if (playerId && playerName) {
      // Create a player from URL params
      const player: Player = {
        id: playerId,
        name: playerName,
        multiplier: multiplier ? parseFloat(multiplier) : 1.0
      };
      setPlayers([player]);
    } else {
      // Empty players array - user can manually enter multiplier
      setPlayers([]);
    }
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            🧮 Fantasy Points Calculator
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Calculate projected fantasy points for any player performance
          </p>
        </div>

        {/* Calculator */}
        <div className="mb-8">
          <PointsPreview players={players} />
        </div>

        {/* Back Button */}
        <div className="text-center">
          <a
            href="/"
            className="inline-block bg-cricket-green text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-600 transition"
          >
            Back to Home
          </a>
        </div>

        {/* Info Section */}
        <div className="mt-12 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">How to Use</h2>
          <div className="space-y-3 text-gray-700 dark:text-gray-300">
            <p>
              <strong>1. Select a Player:</strong> Choose any player from the roster dropdown
            </p>
            <p>
              <strong>2. Adjust Multiplier:</strong> Modify the player multiplier (0.69-5.00) to see how it affects points
            </p>
            <p>
              <strong>3. Enter Stats:</strong> Input batting, bowling, and fielding statistics
            </p>
            <p>
              <strong>4. Set Role:</strong> Choose Captain (2x), Vice Captain (1.5x), Wicketkeeper (2x catches), or None
            </p>
            <p>
              <strong>5. View Results:</strong> See the projected fantasy points calculated in real-time
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CalculatorPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🧮</div>
          <p className="text-gray-600 dark:text-gray-400">Loading calculator...</p>
        </div>
      </div>
    }>
      <CalculatorContent />
    </Suspense>
  );
}
