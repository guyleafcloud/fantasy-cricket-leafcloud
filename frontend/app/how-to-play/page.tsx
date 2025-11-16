'use client';

export default function HowToPlay() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            How to Play
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Fantasy Cricket scoring rules and gameplay
          </p>
        </div>

        {/* Fantasy Points Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 border-b-2 border-cricket-green pb-2">
            Fantasy Points System
          </h2>

          {/* Batting Section */}
          <div className="mb-8">
            <h3 className="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
              <span className="mr-2">🏏</span> Batting
            </h3>

            {/* Tiered Run Points */}
            <div className="mb-4 p-4 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-lg">
              <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">📊 Tiered Run Points</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span>Runs 1-30</span>
                  <span className="text-green-600 dark:text-green-400 font-bold">1.0 pts per run</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Runs 31-49</span>
                  <span className="text-green-600 dark:text-green-400 font-bold">1.25 pts per run</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Runs 50-99</span>
                  <span className="text-green-600 dark:text-green-400 font-bold">1.5 pts per run</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Runs 100+</span>
                  <span className="text-green-600 dark:text-green-400 font-bold">1.75 pts per run</span>
                </div>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 italic">
                Example: 50 runs = (30×1.0) + (19×1.25) + (1×1.5) = 55.25 base points
              </p>
            </div>

            {/* Strike Rate Multiplier */}
            <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">⚡ Strike Rate Multiplier</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Run points × (Strike Rate / 100)</span>
                  <span className="text-blue-600 dark:text-blue-400 font-bold">Multiplier</span>
                </div>
                <div className="pl-4 space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span>SR 100 = 1.0x (neutral)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>SR 150 = 1.5x (50% bonus)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>SR 50 = 0.5x (50% penalty)</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 italic">
                Example: 50 runs (55.25 base) at SR 150 = 55.25 × 1.5 = 82.9 points
              </p>
            </div>

            {/* Milestones */}
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Fifty (50+ runs)</span>
                <span className="text-cricket-green font-bold">+8 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Century (100+ runs)</span>
                <span className="text-cricket-green font-bold">+16 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900/20 rounded">
                <span className="font-medium">Duck (0 runs, dismissed)</span>
                <span className="text-red-600 font-bold">-2 points</span>
              </div>
            </div>

            <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded border-l-4 border-yellow-400">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong>Note:</strong> Boundaries (fours and sixes) count as runs but do NOT give extra bonus points.
              </p>
            </div>
          </div>

          {/* Bowling Section */}
          <div className="mb-8">
            <h3 className="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
              <span className="mr-2">⚾</span> Bowling
            </h3>

            {/* Tiered Wicket Points */}
            <div className="mb-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg">
              <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">📊 Tiered Wicket Points</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span>Wickets 1-2</span>
                  <span className="text-purple-600 dark:text-purple-400 font-bold">15 pts each</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Wickets 3-4</span>
                  <span className="text-purple-600 dark:text-purple-400 font-bold">20 pts each</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Wickets 5-10</span>
                  <span className="text-purple-600 dark:text-purple-400 font-bold">30 pts each</span>
                </div>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 italic">
                Example: 5 wickets = (2×15) + (2×20) + (1×30) = 100 base points
              </p>
            </div>

            {/* Economy Rate Multiplier */}
            <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">💹 Economy Rate Multiplier</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Wicket points × (6.0 / Economy Rate)</span>
                  <span className="text-green-600 dark:text-green-400 font-bold">Multiplier</span>
                </div>
                <div className="pl-4 space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span>ER 6.0 = 1.0x (neutral)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>ER 4.0 = 1.5x (50% bonus)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>ER 8.0 = 0.75x (25% penalty)</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 italic">
                Example: 3 wickets (50 base) at ER 4.0 = 50 × 1.5 = 75 points
              </p>
            </div>

            {/* Other Bowling Points */}
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded border-2 border-purple-300">
                <span className="font-medium">Maiden over</span>
                <span className="text-purple-600 font-bold text-lg">+15 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">5 wicket haul bonus</span>
                <span className="text-cricket-green font-bold">+8 points</span>
              </div>
            </div>

            <div className="mt-4 p-3 bg-purple-100 dark:bg-purple-900/20 rounded border-l-4 border-purple-500">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong>Pro Tip:</strong> Maidens are worth the same as your first two wickets (15 pts)!
              </p>
            </div>
          </div>

          {/* Fielding Section */}
          <div className="mb-8">
            <h3 className="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
              <span className="mr-2">🥎</span> Fielding
            </h3>

            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Catch</span>
                <span className="text-cricket-green font-bold">+4 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Stumping</span>
                <span className="text-cricket-green font-bold">+6 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Run out</span>
                <span className="text-cricket-green font-bold">+6 points</span>
              </div>
            </div>

            {/* Wicketkeeper Bonus */}
            <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border-2 border-yellow-400">
              <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">🧤 Wicketkeeper Bonus</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span>Designated Wicketkeeper catches</span>
                  <span className="text-yellow-600 dark:text-yellow-400 font-bold">2x points (8 pts each)</span>
                </div>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 italic">
                Select one wicketkeeper in your fantasy team to double their catch points!
              </p>
            </div>
          </div>

        </div>

        {/* Example Calculation */}
        <div className="bg-gradient-to-r from-cricket-green to-green-600 rounded-lg shadow-lg p-8 text-white mb-8">
          <h2 className="text-3xl font-bold mb-6">📊 Example Calculation</h2>

          <div className="bg-white dark:bg-gray-800/10 backdrop-blur rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4">All-Rounder Performance</h3>

            <div className="space-y-3 mb-4">
              <div className="flex justify-between">
                <span>Batting: 45 runs (SR 125)</span>
                <span className="font-mono">45 + 5 = 50 pts</span>
              </div>
              <div className="flex justify-between">
                <span>Bowling: 3 wickets, 2 maidens (ER 3.5)</span>
                <span className="font-mono">36 + 50 + 10 = 96 pts</span>
              </div>
              <div className="flex justify-between">
                <span>Fielding: 1 catch</span>
                <span className="font-mono">4 pts</span>
              </div>
            </div>

            <div className="border-t border-white/30 pt-3 mt-3">
              <div className="flex justify-between text-2xl font-bold">
                <span>TOTAL:</span>
                <span>150 points</span>
              </div>
            </div>
          </div>
        </div>

        {/* Strategy Tips */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 border-b-2 border-cricket-green pb-2">
            💡 Strategy Tips
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h3 className="font-semibold text-green-800 dark:text-green-400 mb-2">✅ High Value</h3>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                <li>• <strong>Specialist batsmen (50+ runs)</strong> - Tiered system rewards big scores!</li>
                <li>• <strong>Aggressive batsmen</strong> - SR &gt; 150 multiplies points</li>
                <li>• <strong>Economical bowlers</strong> - ER &lt; 4.0 multiplies wicket points</li>
                <li>• <strong>Maiden bowlers</strong> - 15 pts each, stackable!</li>
                <li>• <strong>All-rounders</strong> - Points from multiple skills</li>
                <li>• <strong>Wicketkeepers</strong> - 2x catch points adds up fast</li>
              </ul>
            </div>

            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <h3 className="font-semibold text-red-800 dark:text-red-400 mb-2">⚠️ Watch Out</h3>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                <li>• <strong>Slow batsmen</strong> - SR &lt; 80 reduces points significantly</li>
                <li>• <strong>Expensive bowlers</strong> - ER &gt; 7.0 reduces wicket points</li>
                <li>• <strong>Duck risks</strong> - Opening batsmen vulnerable to -2 penalty</li>
                <li>• <strong>Low-order bowlers</strong> - Unlikely to reach tier 3 wickets (30 pts)</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-2 border-blue-300 dark:border-blue-700">
            <h3 className="font-semibold text-blue-800 dark:text-blue-400 mb-2">🎯 Team Building Strategy</h3>
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
              <strong>Specialist batsmen are valuable!</strong> The tiered system and strike rate multiplier mean a batsman scoring 80-100+ runs
              can earn 150-300 points, justifying their roster spot even if they don&apos;t bowl. This creates strategic depth:
            </p>
            <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300 ml-4">
              <li>• <strong>Balanced approach:</strong> Mix all-rounders with specialist batsmen and bowlers</li>
              <li>• <strong>High-risk, high-reward:</strong> Load up on aggressive batsmen hoping for big scores</li>
              <li>• <strong>Consistent approach:</strong> Focus on all-rounders who contribute in every match</li>
            </ul>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 border-b-2 border-cricket-green pb-2">
            ❓ Frequently Asked Questions
          </h2>

          <div className="space-y-4">
            <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Do boundaries (4s and 6s) give extra points?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                No. Boundaries count as runs (4 or 6 points) but don&apos;t give any additional bonus points.
                However, hitting boundaries quickly improves your strike rate, which CAN earn bonus points!
              </p>
            </div>

            <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Is there a minimum for strike rate and economy bonuses?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                No! Even facing 1 ball qualifies for strike rate bonuses, and bowling just 1 over qualifies
                for economy bonuses. Every ball counts!
              </p>
            </div>

            <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Can a player play in multiple teams/grades?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Yes! Players can appear in ACC 1, U17, and ZAMI in the same week. All performances are
                tracked separately and contribute to their total points.
              </p>
            </div>

            <div className="pb-4">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Why are maidens worth so much?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Maidens represent excellent pressure bowling and are hard to achieve. At 25 points each,
                they reward economical bowling mastery. A bowler with 3 maidens earns 75 points before
                any wickets!
              </p>
            </div>
          </div>
        </div>

        {/* Back Button */}
        <div className="mt-8 text-center">
          <a
            href="/"
            className="inline-block bg-cricket-green text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-600 transition"
          >
            Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
