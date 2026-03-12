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

        {/* Player Multiplier System - MOST IMPORTANT */}
        <div className="bg-gradient-to-br from-cricket-green/10 to-blue-600/10 dark:from-cricket-green/20 dark:to-blue-600/20 rounded-lg shadow-lg p-8 mb-8 border-2 border-cricket-green">
          <div className="flex items-center mb-6">
            <div className="bg-cricket-green text-white rounded-full w-12 h-12 flex items-center justify-center text-2xl font-bold mr-4">
              1
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Player Multiplier System ⚖️
            </h2>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 mb-4">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
              🎯 The Core Concept
            </h3>
            <p className="text-gray-700 dark:text-gray-300 mb-4 text-lg leading-relaxed">
              Every player has a <strong className="text-cricket-green">handicap multiplier</strong> based on their real-life skill level.
              Elite players have <strong className="text-red-600 dark:text-red-400">lower multipliers</strong> (e.g., 0.69x), while developing players have <strong className="text-green-600 dark:text-green-400">higher multipliers</strong> (e.g., 1.2x).
              This balances the game so that all players can contribute meaningfully to your fantasy team!
            </p>

            <div className="bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-900/30 dark:to-green-900/30 rounded-lg p-5 mb-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 text-lg">How It Works:</h4>
              <div className="space-y-3">
                <div className="flex items-start">
                  <span className="text-2xl mr-3">📊</span>
                  <div>
                    <p className="text-gray-800 dark:text-gray-200 font-medium">Base Points Calculation</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">First, calculate points from runs, wickets, catches, etc. (explained below)</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <span className="text-2xl mr-3">✖️</span>
                  <div>
                    <p className="text-gray-800 dark:text-gray-200 font-medium">Apply Player Multiplier</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Multiply base points by the player&apos;s handicap</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <span className="text-2xl mr-3">🎭</span>
                  <div>
                    <p className="text-gray-800 dark:text-gray-200 font-medium">Apply Captain/VC Bonus</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Finally, apply Captain (2x) or Vice-Captain (1.5x) multiplier if applicable</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-5">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">📐 Complete Formula:</h4>
            <div className="font-mono text-sm bg-gray-100 dark:bg-gray-900 p-4 rounded border border-gray-300 dark:border-gray-700">
              <div className="text-gray-800 dark:text-gray-200 space-y-2">
                <div><span className="text-blue-600 dark:text-blue-400">Final Points</span> = <span className="text-green-600 dark:text-green-400">Base Points</span> × <span className="text-orange-600 dark:text-orange-400">Player Multiplier</span> × <span className="text-purple-600 dark:text-purple-400">Captain Bonus</span></div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-3 border-t border-gray-300 dark:border-gray-700 pt-2">
                  Example: 100 base points × 0.69 multiplier × 2.0 (captain) = <strong className="text-cricket-green">138 final points</strong>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/30 dark:to-orange-900/30 rounded-lg p-5 mt-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">⚡ Why Lower Multipliers for Elite Players?</h4>
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
              This creates a <strong>balanced fantasy game</strong> where picking only elite players isn&apos;t automatically the winning strategy.
              Both star performers and developing players can contribute significantly to your team&apos;s success!
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="bg-red-100 dark:bg-red-900/30 p-3 rounded border border-red-300">
                <div className="font-bold text-red-800 dark:text-red-400 mb-1">🌟 Elite Player (0.69x)</div>
                <div className="text-gray-700 dark:text-gray-300">50 runs = 55 base pts × 0.69 = <strong>38 pts</strong></div>
              </div>
              <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded border border-green-300">
                <div className="font-bold text-green-800 dark:text-green-400 mb-1">🌱 Developing Player (1.2x)</div>
                <div className="text-gray-700 dark:text-gray-300">50 runs = 55 base pts × 1.2 = <strong>66 pts</strong></div>
              </div>
            </div>
          </div>
        </div>

        {/* Team Building Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <div className="bg-cricket-green text-white rounded-full w-12 h-12 flex items-center justify-center text-2xl font-bold mr-4">
              2
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Building Your Team
            </h2>
          </div>

          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">🏆 Squad Requirements</h3>
              <div className="space-y-3">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">👥</span>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Squad Size: 11 Players</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Select exactly 11 players for your fantasy team</p>
                  </div>
                </div>
                <div className="flex items-center">
                  <span className="text-2xl mr-3">⚖️</span>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Team Composition Rules</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Your league may have specific requirements (e.g., minimum batsmen, bowlers, wicketkeeper)</p>
                  </div>
                </div>
                <div className="flex items-center">
                  <span className="text-2xl mr-3">🏏</span>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Real-Life Team Diversity</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Some leagues require at least one player from each real-life team</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">👑 Captain & Vice-Captain (MANDATORY)</h3>
              <div className="space-y-3">
                <div className="flex items-start">
                  <span className="text-2xl mr-3">🎯</span>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Captain (2x Points)</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Your captain&apos;s final points are doubled. Choose wisely!</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <span className="text-2xl mr-3">🥈</span>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Vice-Captain (1.5x Points)</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Your vice-captain&apos;s final points are multiplied by 1.5</p>
                  </div>
                </div>
                <div className="bg-yellow-100 dark:bg-yellow-900/30 p-3 rounded mt-3">
                  <p className="text-sm text-gray-800 dark:text-gray-300">
                    💡 <strong>Pro Tip:</strong> Captain/VC bonuses are applied AFTER the player multiplier, so they work with any player regardless of their handicap!
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">🧤 Wicketkeeper (OPTIONAL)</h3>
              <div className="space-y-3">
                <p className="text-gray-700 dark:text-gray-300">
                  You can designate one player in your squad as your wicketkeeper. This player receives <strong>double points (30 pts instead of 15 pts)</strong> for catches.
                </p>
                <div className="bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    <strong>Note:</strong> Wicketkeeper designation is optional and separate from captain/vice-captain. You manually select which player gets the WK bonus when building your team.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">🔄 Transfers</h3>
              <div className="space-y-3">
                <p className="text-gray-700 dark:text-gray-300">
                  Each league has a set number of transfers per season (typically 4). Use them strategically to adapt your team throughout the season!
                </p>
                <div className="space-y-2">
                  <div className="flex items-start">
                    <span className="text-xl mr-2">✅</span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Transfers allow you to swap out underperforming players</p>
                  </div>
                  <div className="flex items-start">
                    <span className="text-xl mr-2">⏰</span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Once you&apos;ve used all your transfers, your squad is locked for the season</p>
                  </div>
                  <div className="flex items-start">
                    <span className="text-xl mr-2">🎁</span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Admins may grant bonus transfers for special circumstances</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Fantasy Points Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <div className="bg-cricket-green text-white rounded-full w-12 h-12 flex items-center justify-center text-2xl font-bold mr-4">
              3
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Base Points System
            </h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            These are the base points earned before multipliers are applied:
          </p>

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
              <img src="/ball.png" alt="Bowling" className="w-6 h-6 mr-2" />
              Bowling
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
              <img src="/catch.png" alt="Fielding" className="w-6 h-6 mr-2" />
              Fielding
            </h3>

            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Catch</span>
                <span className="text-cricket-green font-bold">+15 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Stumping</span>
                <span className="text-cricket-green font-bold">+15 points</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded">
                <span className="font-medium">Run out</span>
                <span className="text-cricket-green font-bold">+6 points</span>
              </div>
            </div>

            {/* Wicketkeeper Bonus */}
            <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border-2 border-yellow-400">
              <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">🧤 Wicketkeeper Bonus (Optional)</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span>Designated Wicketkeeper catches</span>
                  <span className="text-yellow-600 dark:text-yellow-400 font-bold">2x points (30 pts each)</span>
                </div>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 italic">
                If you designate a wicketkeeper when building your team, that player receives double points for catches. Stumpings always give 15 points regardless of wicketkeeper status.
              </p>
            </div>
          </div>

        </div>

        {/* Example Calculation */}
        <div className="bg-gradient-to-r from-cricket-green to-green-600 rounded-lg shadow-lg p-8 text-white mb-8">
          <h2 className="text-3xl font-bold mb-6">📊 Complete Example Calculation</h2>

          <div className="bg-white/95 dark:bg-gray-800/10 backdrop-blur rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Developing All-Rounder Performance (Player Multiplier: 1.2x, Captain)</h3>

            <div className="space-y-3 mb-4 text-gray-900 dark:text-white">
              <div className="font-semibold text-lg border-b border-gray-300 dark:border-white/30 pb-2 mb-3">
                Step 1: Calculate Base Points
              </div>

              <div className="flex justify-between">
                <span>Batting: 45 runs @ SR 125</span>
                <span className="font-mono">59.1 pts</span>
              </div>
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 pl-4">
                <span>• Tiered base: (30×1.0) + (15×1.25) = 48.75</span>
                <span></span>
              </div>
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 pl-4">
                <span>• SR multiplier: 48.75 × 1.25 = 59.1</span>
                <span></span>
              </div>
              <div className="flex justify-between">
                <span>Bowling: 3 wickets @ ER 4.0, 1 maiden</span>
                <span className="font-mono">90 pts</span>
              </div>
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 pl-4">
                <span>• Tiered wickets: (2×15) + (1×20) = 50</span>
                <span></span>
              </div>
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 pl-4">
                <span>• ER multiplier: 50 × 1.5 = 75</span>
                <span></span>
              </div>
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 pl-4">
                <span>• Maidens: 1 × 15 = 15</span>
                <span></span>
              </div>
              <div className="flex justify-between">
                <span>Fielding: 1 catch</span>
                <span className="font-mono">15 pts</span>
              </div>

              <div className="border-t border-gray-300 dark:border-white/30 pt-2 mt-2">
                <div className="flex justify-between font-semibold">
                  <span>Base Points Subtotal:</span>
                  <span className="font-mono">164 pts</span>
                </div>
              </div>

              <div className="font-semibold text-lg border-b border-gray-300 dark:border-white/30 pb-2 mt-4 mb-3">
                Step 2: Apply Player Multiplier
              </div>

              <div className="flex justify-between">
                <span>Base Points × Player Multiplier</span>
                <span className="font-mono">164 × 1.2</span>
              </div>
              <div className="border-t border-gray-300 dark:border-white/30 pt-2 mt-2">
                <div className="flex justify-between font-semibold">
                  <span>After Multiplier:</span>
                  <span className="font-mono">196.8 pts</span>
                </div>
              </div>

              <div className="font-semibold text-lg border-b border-gray-300 dark:border-white/30 pb-2 mt-4 mb-3">
                Step 3: Apply Captain Bonus
              </div>

              <div className="flex justify-between">
                <span>After Multiplier × Captain Bonus (2x)</span>
                <span className="font-mono">196.8 × 2.0</span>
              </div>
            </div>

            <div className="border-t-2 border-gray-400 dark:border-white/50 pt-4 mt-4 bg-cricket-green/10 dark:bg-cricket-green/20 rounded-lg p-3">
              <div className="flex justify-between text-2xl font-bold text-gray-900 dark:text-white">
                <span>FINAL FANTASY POINTS:</span>
                <span className="text-cricket-green dark:text-green-400">393.6 points</span>
              </div>
            </div>
          </div>
        </div>

        {/* Scoring Timeline Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 border-b-2 border-cricket-green pb-2">
            ⏰ When Do Points Count?
          </h2>

          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <span className="text-2xl mr-2">📅</span>
                Season-Long Accumulation
              </h3>
              <div className="space-y-3 text-gray-700 dark:text-gray-300">
                <p>
                  Fantasy points accumulate throughout the entire cricket season. Your team&apos;s total score is the sum of all points earned by your players across all matches.
                </p>
                <div className="bg-white dark:bg-gray-800 p-4 rounded border border-gray-200 dark:border-gray-700">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-start">
                      <span className="text-lg mr-2">1️⃣</span>
                      <p><strong>Match Completed:</strong> Points are calculated after each real-life match</p>
                    </div>
                    <div className="flex items-start">
                      <span className="text-lg mr-2">2️⃣</span>
                      <p><strong>Points Updated:</strong> Your fantasy team&apos;s total is updated automatically</p>
                    </div>
                    <div className="flex items-start">
                      <span className="text-lg mr-2">3️⃣</span>
                      <p><strong>Rankings Updated:</strong> Leaderboards are refreshed with new standings</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <span className="text-2xl mr-2">🏆</span>
                Multiple Matches Per Player
              </h3>
              <p className="text-gray-700 dark:text-gray-300 mb-3">
                A player can compete in multiple matches during a week (e.g., ACC 1, U17, and ZAMI). <strong>All performances count!</strong>
              </p>
              <div className="bg-yellow-100 dark:bg-yellow-900/30 p-4 rounded">
                <p className="text-sm text-gray-800 dark:text-gray-300">
                  💡 <strong>Example:</strong> If your player scores 50 runs in ACC 1 on Saturday and takes 3 wickets in U17 on Sunday, both performances are added to your fantasy team&apos;s total!
                </p>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <span className="text-2xl mr-2">🎯</span>
                Winning the League
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                The fantasy team with the <strong>highest total points at the end of the season</strong> wins the league! Monitor the leaderboard regularly to track your progress.
              </p>
            </div>
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

            <div className="pb-4">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Can a player play in multiple teams/grades?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Yes! Players can appear in ACC 1, U17, and ZAMI in the same week. All performances are
                tracked separately and contribute to their total points.
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
