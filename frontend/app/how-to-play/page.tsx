'use client';

export default function HowToPlay() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            How to Play
          </h1>
          <p className="text-xl text-gray-600">
            Fantasy Cricket scoring rules and gameplay
          </p>
        </div>

        {/* Fantasy Points Section */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 border-b-2 border-cricket-green pb-2">
            Fantasy Points System
          </h2>

          {/* Batting Section */}
          <div className="mb-8">
            <h3 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">🏏</span> Batting
            </h3>

            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">Every run scored</span>
                <span className="text-cricket-green font-bold">+1 point</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">Fifty (50+ runs)</span>
                <span className="text-cricket-green font-bold">+8 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">Century (100+ runs)</span>
                <span className="text-cricket-green font-bold">+16 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-red-50 rounded">
                <span className="font-medium">Duck (0 runs, dismissed)</span>
                <span className="text-red-600 font-bold">-2 points</span>
              </div>
            </div>

            {/* Strike Rate Bonuses */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-gray-800 mb-3">⚡ Strike Rate Bonuses</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Strike Rate ≥ 150</span>
                  <span className="text-blue-600 font-bold">+10 points</span>
                </div>
                <div className="flex justify-between">
                  <span>Strike Rate ≥ 100</span>
                  <span className="text-blue-600 font-bold">+5 points</span>
                </div>
                <div className="flex justify-between">
                  <span>Strike Rate &lt; 50</span>
                  <span className="text-red-600 font-bold">-5 points</span>
                </div>
              </div>
              <p className="text-xs text-gray-600 mt-2 italic">
                * No minimum balls required - even 1 ball qualifies
              </p>
            </div>

            <div className="mt-4 p-3 bg-yellow-50 rounded border-l-4 border-yellow-400">
              <p className="text-sm text-gray-700">
                <strong>Note:</strong> Boundaries (fours and sixes) count as runs but do NOT give extra bonus points.
              </p>
            </div>
          </div>

          {/* Bowling Section */}
          <div className="mb-8">
            <h3 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">⚾</span> Bowling
            </h3>

            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">Every wicket taken</span>
                <span className="text-cricket-green font-bold">+12 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-purple-50 rounded border-2 border-purple-300">
                <span className="font-medium">Maiden over</span>
                <span className="text-purple-600 font-bold text-lg">+25 points 🔥</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">5 wicket haul</span>
                <span className="text-cricket-green font-bold">+8 points</span>
              </div>
            </div>

            {/* Economy Rate Bonuses */}
            <div className="mt-6 p-4 bg-green-50 rounded-lg">
              <h4 className="font-semibold text-gray-800 mb-3">💹 Economy Rate Bonuses</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Economy Rate &lt; 4.0</span>
                  <span className="text-green-600 font-bold">+10 points</span>
                </div>
                <div className="flex justify-between">
                  <span>Economy Rate &lt; 5.0</span>
                  <span className="text-green-600 font-bold">+5 points</span>
                </div>
                <div className="flex justify-between">
                  <span>Economy Rate &gt; 7.0</span>
                  <span className="text-red-600 font-bold">-5 points</span>
                </div>
              </div>
              <p className="text-xs text-gray-600 mt-2 italic">
                * No minimum overs required - even 1 over qualifies
              </p>
            </div>

            <div className="mt-4 p-3 bg-purple-100 rounded border-l-4 border-purple-500">
              <p className="text-sm text-gray-700">
                <strong>Pro Tip:</strong> Maidens are EXTREMELY valuable! A single maiden over is worth more than 2 wickets!
              </p>
            </div>
          </div>

          {/* Fielding Section */}
          <div className="mb-8">
            <h3 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">🥎</span> Fielding
            </h3>

            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">Catch</span>
                <span className="text-cricket-green font-bold">+4 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">Stumping</span>
                <span className="text-cricket-green font-bold">+6 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">Run out</span>
                <span className="text-cricket-green font-bold">+6 points</span>
              </div>
            </div>
          </div>

          {/* Tier Multipliers Section */}
          <div className="mb-8">
            <h3 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">🏆</span> Tier Multipliers
            </h3>

            <p className="text-gray-600 mb-4">
              All fantasy points are multiplied based on the match tier:
            </p>

            <div className="space-y-2">
              <div className="flex justify-between items-center p-3 bg-yellow-50 rounded border-l-4 border-yellow-500">
                <div>
                  <span className="font-semibold">Tier 1</span>
                  <span className="text-sm text-gray-600 ml-2">(Topklasse, Hoofdklasse)</span>
                </div>
                <span className="text-yellow-600 font-bold">×1.2</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded border-l-4 border-gray-400">
                <div>
                  <span className="font-semibold">Tier 2</span>
                  <span className="text-sm text-gray-600 ml-2">(Eerste, Tweede Klasse)</span>
                </div>
                <span className="text-gray-600 font-bold">×1.0</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded border-l-4 border-gray-300">
                <div>
                  <span className="font-semibold">Tier 3</span>
                  <span className="text-sm text-gray-600 ml-2">(Derde, Vierde Klasse)</span>
                </div>
                <span className="text-gray-600 font-bold">×0.8</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded border-l-4 border-blue-400">
                <div>
                  <span className="font-semibold">Youth</span>
                  <span className="text-sm text-gray-600 ml-2">(U13, U15, U17)</span>
                </div>
                <span className="text-blue-600 font-bold">×0.6</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-pink-50 rounded border-l-4 border-pink-400">
                <div>
                  <span className="font-semibold">Ladies</span>
                  <span className="text-sm text-gray-600 ml-2">(Vrouwen)</span>
                </div>
                <span className="text-pink-600 font-bold">×0.9</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-orange-50 rounded border-l-4 border-orange-400">
                <div>
                  <span className="font-semibold">Social</span>
                  <span className="text-sm text-gray-600 ml-2">(ZAMI, ZOMI)</span>
                </div>
                <span className="text-orange-600 font-bold">×0.4</span>
              </div>
            </div>
          </div>
        </div>

        {/* Example Calculation */}
        <div className="bg-gradient-to-r from-cricket-green to-green-600 rounded-lg shadow-lg p-8 text-white mb-8">
          <h2 className="text-3xl font-bold mb-6">📊 Example Calculation</h2>

          <div className="bg-white/10 backdrop-blur rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4">All-Rounder Performance (Tier 2)</h3>

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
              <div className="flex justify-between text-lg font-bold">
                <span>Subtotal:</span>
                <span>150 points</span>
              </div>
              <div className="flex justify-between text-lg">
                <span>Tier 2 Multiplier (×1.0):</span>
                <span>×1.0</span>
              </div>
              <div className="flex justify-between text-2xl font-bold mt-2 pt-2 border-t border-white/30">
                <span>TOTAL:</span>
                <span>150 points</span>
              </div>
            </div>
          </div>
        </div>

        {/* Strategy Tips */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 border-b-2 border-cricket-green pb-2">
            💡 Strategy Tips
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-4 bg-green-50 rounded-lg">
              <h3 className="font-semibold text-green-800 mb-2">✅ High Value</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• <strong>Maiden bowlers</strong> - 25 pts each!</li>
                <li>• <strong>Economical bowlers</strong> - ER &lt; 4.0</li>
                <li>• <strong>Aggressive batsmen</strong> - SR &gt; 150</li>
                <li>• <strong>All-rounders</strong> - Points from multiple skills</li>
                <li>• <strong>Tier 1 players</strong> - 1.2× multiplier</li>
              </ul>
            </div>

            <div className="p-4 bg-red-50 rounded-lg">
              <h3 className="font-semibold text-red-800 mb-2">⚠️ Watch Out</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• <strong>Slow batsmen</strong> - SR &lt; 50 penalty</li>
                <li>• <strong>Expensive bowlers</strong> - ER &gt; 7.0 penalty</li>
                <li>• <strong>Duck risks</strong> - Opening batsmen</li>
                <li>• <strong>Social league</strong> - Only 0.4× multiplier</li>
              </ul>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 border-b-2 border-cricket-green pb-2">
            ❓ Frequently Asked Questions
          </h2>

          <div className="space-y-4">
            <div className="border-b border-gray-200 pb-4">
              <h3 className="font-semibold text-gray-800 mb-2">
                Do boundaries (4s and 6s) give extra points?
              </h3>
              <p className="text-gray-600">
                No. Boundaries count as runs (4 or 6 points) but don't give any additional bonus points.
                However, hitting boundaries quickly improves your strike rate, which CAN earn bonus points!
              </p>
            </div>

            <div className="border-b border-gray-200 pb-4">
              <h3 className="font-semibold text-gray-800 mb-2">
                Is there a minimum for strike rate and economy bonuses?
              </h3>
              <p className="text-gray-600">
                No! Even facing 1 ball qualifies for strike rate bonuses, and bowling just 1 over qualifies
                for economy bonuses. Every ball counts!
              </p>
            </div>

            <div className="border-b border-gray-200 pb-4">
              <h3 className="font-semibold text-gray-800 mb-2">
                Can a player play in multiple teams/grades?
              </h3>
              <p className="text-gray-600">
                Yes! Players can appear in ACC 1, U17, and ZAMI in the same week. All performances are
                tracked separately and contribute to their total points.
              </p>
            </div>

            <div className="pb-4">
              <h3 className="font-semibold text-gray-800 mb-2">
                Why are maidens worth so much?
              </h3>
              <p className="text-gray-600">
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
