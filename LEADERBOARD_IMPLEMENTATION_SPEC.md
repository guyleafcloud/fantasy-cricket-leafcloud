# 🏏 Enhanced Leaderboard Implementation Specification

**Date**: 2025-12-16
**Approach**: Highlights + Small Icons + Colored Tables (NO charts/bars)
**Priority**: Mobile-First Design

---

## 📱 Visual Design Philosophy

### What We're Building
- ✅ **Highlights**: Color-coded backgrounds for key stats
- ✅ **Small Icons**: Cricket emojis and simple SVG icons
- ✅ **Colored Tables**: Side-by-side stats with conditional colors
- ❌ **NOT Using**: Bar charts, pie charts, progress bars

### Color Scheme
```css
/* Performance Indicators */
--excellent: #10b981 (green)
--good: #3b82f6 (blue)
--average: #f59e0b (amber)
--poor: #ef4444 (red)
--neutral: #6b7280 (gray)

/* Cricket-specific */
--runs-bg: #dbeafe (light blue)
--wickets-bg: #fee2e2 (light red)
--fielding-bg: #d1fae5 (light green)
--captain-gold: #fef3c7 (light yellow)
```

### Icon Set
- 🏏 Batsman
- ⚾ Bowler
- 🧤 Fielder
- 👑 Captain
- ⭐ Vice Captain
- 🧤 Wicket Keeper
- 📈 Improving form
- 📉 Declining form
- ➡️ Stable form
- 🔥 Hot streak (3+ good games)
- ❄️ Cold streak (3+ poor games)

---

## 1️⃣ BACKEND IMPLEMENTATION

### File: `backend/main.py`

**New Endpoint**: Add after existing `/api/leagues/{league_id}/teams/{team_id}` endpoint (around line 385)

```python
@app.get("/api/leagues/{league_id}/teams/{team_id}/detailed")
async def get_team_detailed_stats(
    league_id: str,
    team_id: str,
    match_count: int = 3,  # Default to last 3 matches, configurable
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive team stats with detailed player performance breakdown

    Query Parameters:
    - match_count: Number of recent matches to show (default: 3, max: 10)
    """
    from sqlalchemy import text, and_, func, case
    from database_models import FantasyTeam, FantasyTeamPlayer, Player

    # Validate match_count
    match_count = max(1, min(match_count, 10))

    # Verify team exists and is in league
    team = db.query(FantasyTeam).filter(
        FantasyTeam.id == team_id,
        FantasyTeam.league_id == league_id,
        FantasyTeam.is_finalized == True
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found or not finalized")

    # Get owner info
    owner = db.query(User).filter(User.id == team.user_id).first()
    owner_name = owner.full_name if owner else "Unknown"

    # Get all players with aggregated stats from player_performances
    players_query = text("""
        WITH player_stats AS (
            SELECT
                p.id as player_id,
                p.name as player_name,
                p.rl_team as club_name,
                p.role as player_role,
                p.starting_multiplier,
                p.multiplier as current_multiplier,
                ftp.is_captain,
                ftp.is_vice_captain,
                ftp.is_wicket_keeper,
                ftp.total_points,

                -- Match count
                COUNT(pp.id) as matches_played,

                -- Batting stats
                COALESCE(SUM(pp.runs), 0) as total_runs,
                COALESCE(SUM(pp.balls_faced), 0) as total_balls,
                COALESCE(SUM(pp.fours), 0) as total_fours,
                COALESCE(SUM(pp.sixes), 0) as total_sixes,
                CASE
                    WHEN SUM(CASE WHEN pp.is_out THEN 1 ELSE 0 END) > 0
                    THEN SUM(pp.runs)::float / SUM(CASE WHEN pp.is_out THEN 1 ELSE 0 END)
                    ELSE NULL
                END as batting_average,
                CASE
                    WHEN SUM(pp.balls_faced) > 0
                    THEN (SUM(pp.runs)::float / SUM(pp.balls_faced) * 100)
                    ELSE NULL
                END as avg_strike_rate,
                MAX(pp.runs) as highest_score,
                SUM(CASE WHEN pp.runs >= 50 AND pp.runs < 100 THEN 1 ELSE 0 END) as fifties,
                SUM(CASE WHEN pp.runs >= 100 THEN 1 ELSE 0 END) as hundreds,
                SUM(CASE WHEN pp.runs = 0 AND pp.is_out THEN 1 ELSE 0 END) as ducks,

                -- Bowling stats
                COALESCE(SUM(pp.wickets), 0) as total_wickets,
                COALESCE(SUM(pp.overs_bowled), 0) as total_overs,
                COALESCE(SUM(pp.maidens), 0) as total_maidens,
                COALESCE(SUM(pp.runs_conceded), 0) as total_runs_conceded,
                CASE
                    WHEN SUM(pp.wickets) > 0
                    THEN SUM(pp.runs_conceded)::float / SUM(pp.wickets)
                    ELSE NULL
                END as bowling_average,
                CASE
                    WHEN SUM(pp.overs_bowled) > 0
                    THEN (SUM(pp.runs_conceded)::float / SUM(pp.overs_bowled))
                    ELSE NULL
                END as economy_rate,
                SUM(CASE WHEN pp.wickets >= 5 THEN 1 ELSE 0 END) as five_wicket_hauls,

                -- Fielding stats
                COALESCE(SUM(pp.catches), 0) as total_catches,
                COALESCE(SUM(pp.run_outs), 0) as total_run_outs,
                COALESCE(SUM(pp.stumpings), 0) as total_stumpings

            FROM fantasy_team_players ftp
            JOIN players p ON ftp.player_id = p.id
            LEFT JOIN player_performances pp ON pp.player_id = p.id
            WHERE ftp.fantasy_team_id = :team_id
            GROUP BY p.id, p.name, p.rl_team, p.role, p.starting_multiplier,
                     p.multiplier, ftp.is_captain, ftp.is_vice_captain,
                     ftp.is_wicket_keeper, ftp.total_points
        )
        SELECT * FROM player_stats
        ORDER BY total_points DESC
    """)

    players_result = db.execute(players_query, {"team_id": team_id}).fetchall()

    # Format players data
    players_data = []
    for row in players_result:
        player_dict = dict(row._mapping)

        # Calculate points breakdown (estimate based on stats)
        batting_points = float(player_dict['total_runs'] or 0) * 1.0  # Simplified
        bowling_points = float(player_dict['total_wickets'] or 0) * 25.0
        fielding_points = (
            float(player_dict['total_catches'] or 0) * 15.0 +
            float(player_dict['total_run_outs'] or 0) * 6.0 +
            float(player_dict['total_stumpings'] or 0) * 15.0
        )

        # Get recent matches for this player
        recent_matches_query = text("""
            SELECT
                pp.round_number,
                pp.match_id,
                pp.fantasy_points,
                pp.runs,
                pp.balls_faced,
                pp.wickets,
                pp.catches,
                pp.run_outs,
                pp.stumpings,
                pp.created_at
            FROM player_performances pp
            WHERE pp.player_id = :player_id
            ORDER BY pp.round_number DESC, pp.created_at DESC
            LIMIT :match_count
        """)

        recent_matches = db.execute(
            recent_matches_query,
            {"player_id": player_dict['player_id'], "match_count": match_count}
        ).fetchall()

        recent_form = []
        for match in recent_matches:
            match_dict = dict(match._mapping)
            recent_form.append({
                'round': match_dict['round_number'],
                'match_id': str(match_dict['match_id']),
                'points': float(match_dict['fantasy_points'] or 0),
                'runs': int(match_dict['runs'] or 0),
                'balls': int(match_dict['balls_faced'] or 0),
                'wickets': int(match_dict['wickets'] or 0),
                'catches': int(match_dict['catches'] or 0)
            })

        # Calculate form trend (last 3 vs previous 3)
        form_trend = "stable"
        if len(recent_form) >= 3:
            recent_avg = sum(m['points'] for m in recent_form[:3]) / 3
            if len(recent_form) >= 6:
                previous_avg = sum(m['points'] for m in recent_form[3:6]) / 3
                if recent_avg > previous_avg * 1.2:
                    form_trend = "improving"
                elif recent_avg < previous_avg * 0.8:
                    form_trend = "declining"

        # Calculate multiplier drift
        multiplier_drift = (
            float(player_dict['current_multiplier'] or 1.0) -
            float(player_dict['starting_multiplier'] or 1.0)
        )

        multiplier_status = "stable"
        if multiplier_drift < -0.1:
            multiplier_status = "strengthening"  # Lower multiplier = stronger player
        elif multiplier_drift > 0.1:
            multiplier_status = "weakening"  # Higher multiplier = weaker player

        players_data.append({
            'player_id': str(player_dict['player_id']),
            'name': player_dict['player_name'],
            'club_name': player_dict['club_name'] or 'Unknown',
            'role': player_dict['player_role'],
            'is_captain': bool(player_dict['is_captain']),
            'is_vice_captain': bool(player_dict['is_vice_captain']),
            'is_wicket_keeper': bool(player_dict['is_wicket_keeper']),
            'total_points': float(player_dict['total_points'] or 0),
            'matches_played': int(player_dict['matches_played'] or 0),
            'points_per_match': (
                float(player_dict['total_points'] or 0) / int(player_dict['matches_played'] or 1)
                if int(player_dict['matches_played'] or 0) > 0 else 0
            ),
            'batting': {
                'runs': int(player_dict['total_runs'] or 0),
                'average': round(float(player_dict['batting_average'] or 0), 2),
                'strike_rate': round(float(player_dict['avg_strike_rate'] or 0), 2),
                'balls_faced': int(player_dict['total_balls'] or 0),
                'fours': int(player_dict['total_fours'] or 0),
                'sixes': int(player_dict['total_sixes'] or 0),
                'fifties': int(player_dict['fifties'] or 0),
                'hundreds': int(player_dict['hundreds'] or 0),
                'ducks': int(player_dict['ducks'] or 0),
                'highest_score': int(player_dict['highest_score'] or 0)
            },
            'bowling': {
                'wickets': int(player_dict['total_wickets'] or 0),
                'overs': round(float(player_dict['total_overs'] or 0), 1),
                'maidens': int(player_dict['total_maidens'] or 0),
                'runs_conceded': int(player_dict['total_runs_conceded'] or 0),
                'average': round(float(player_dict['bowling_average'] or 0), 2) if player_dict['bowling_average'] else None,
                'economy': round(float(player_dict['economy_rate'] or 0), 2) if player_dict['economy_rate'] else None,
                'five_wicket_hauls': int(player_dict['five_wicket_hauls'] or 0)
            },
            'fielding': {
                'catches': int(player_dict['total_catches'] or 0),
                'run_outs': int(player_dict['total_run_outs'] or 0),
                'stumpings': int(player_dict['total_stumpings'] or 0)
            },
            'multiplier_info': {
                'starting_multiplier': round(float(player_dict['starting_multiplier'] or 1.0), 2),
                'current_multiplier': round(float(player_dict['current_multiplier'] or 1.0), 2),
                'drift': round(multiplier_drift, 2),
                'status': multiplier_status
            },
            'recent_form': {
                'matches': recent_form,
                'last_n_average': (
                    round(sum(m['points'] for m in recent_form) / len(recent_form), 1)
                    if recent_form else 0
                ),
                'trend': form_trend
            },
            'points_breakdown': {
                'batting_points': round(batting_points, 1),
                'bowling_points': round(bowling_points, 1),
                'fielding_points': round(fielding_points, 1)
            }
        })

    return {
        'team_id': str(team.id),
        'team_name': team.team_name,
        'owner_name': owner_name,
        'total_points': float(team.total_points or 0),
        'weekly_points': float(team.last_round_points or 0),
        'squad_size': len(players_data),
        'players': players_data
    }
```

**Location**: Insert this after line 384 in `backend/main.py`

**Testing**: Can test with:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/leagues/LEAGUE_ID/teams/TEAM_ID/detailed?match_count=5"
```

---

## 2️⃣ FRONTEND IMPLEMENTATION

### File Structure (New Files)
```
frontend/app/leagues/[league_id]/leaderboard/
├── components/
│   ├── TeamDetailedModal.tsx        (NEW - Main modal)
│   ├── PlayerPerformanceCard.tsx    (NEW - Player card)
│   ├── PlayerComparisonModal.tsx    (NEW - Compare 2 players)
│   ├── StatRow.tsx                  (NEW - Reusable stat row)
│   └── types.ts                     (NEW - TypeScript interfaces)
└── page.tsx                          (MODIFY - Update modal trigger)
```

---

### File 1: `frontend/app/leagues/[league_id]/leaderboard/components/types.ts`

```typescript
// TypeScript Interfaces for Detailed Team Stats

export interface DetailedPlayerStats {
  player_id: string;
  name: string;
  club_name: string;
  role: 'BATSMAN' | 'BOWLER' | 'ALL_ROUNDER' | 'WICKET_KEEPER';
  is_captain: boolean;
  is_vice_captain: boolean;
  is_wicket_keeper: boolean;
  total_points: number;
  matches_played: number;
  points_per_match: number;
  batting: BattingStats;
  bowling: BowlingStats;
  fielding: FieldingStats;
  multiplier_info: MultiplierInfo;
  recent_form: RecentForm;
  points_breakdown: PointsBreakdown;
}

export interface BattingStats {
  runs: number;
  average: number;
  strike_rate: number;
  balls_faced: number;
  fours: number;
  sixes: number;
  fifties: number;
  hundreds: number;
  ducks: number;
  highest_score: number;
}

export interface BowlingStats {
  wickets: number;
  overs: number;
  maidens: number;
  runs_conceded: number;
  average: number | null;
  economy: number | null;
  five_wicket_hauls: number;
}

export interface FieldingStats {
  catches: number;
  run_outs: number;
  stumpings: number;
}

export interface MultiplierInfo {
  starting_multiplier: number;
  current_multiplier: number;
  drift: number;
  status: 'strengthening' | 'weakening' | 'stable';
}

export interface RecentForm {
  matches: MatchPerformance[];
  last_n_average: number;
  trend: 'improving' | 'declining' | 'stable';
}

export interface MatchPerformance {
  round: number;
  match_id: string;
  points: number;
  runs: number;
  balls: number;
  wickets: number;
  catches: number;
}

export interface PointsBreakdown {
  batting_points: number;
  bowling_points: number;
  fielding_points: number;
}

export interface DetailedTeamResponse {
  team_id: string;
  team_name: string;
  owner_name: string;
  total_points: number;
  weekly_points: number;
  squad_size: number;
  players: DetailedPlayerStats[];
}
```

---

### File 2: `frontend/app/leagues/[league_id]/leaderboard/components/StatRow.tsx`

```typescript
// Reusable stat row with colored indicator

interface StatRowProps {
  label: string;
  value: string | number;
  highlight?: 'excellent' | 'good' | 'average' | 'poor' | 'neutral';
  icon?: string;
}

export default function StatRow({ label, value, highlight = 'neutral', icon }: StatRowProps) {
  const colorClasses = {
    excellent: 'bg-green-50 text-green-900',
    good: 'bg-blue-50 text-blue-900',
    average: 'bg-amber-50 text-amber-900',
    poor: 'bg-red-50 text-red-900',
    neutral: 'bg-gray-50 text-gray-900'
  };

  return (
    <div className="flex justify-between items-center py-2 px-3 rounded">
      <span className="text-sm text-gray-600 flex items-center gap-1">
        {icon && <span>{icon}</span>}
        {label}
      </span>
      <span className={`text-sm font-semibold px-2 py-1 rounded ${colorClasses[highlight]}`}>
        {value}
      </span>
    </div>
  );
}
```

---

### File 3: `frontend/app/leagues/[league_id]/leaderboard/components/PlayerPerformanceCard.tsx`

```typescript
'use client';

import { DetailedPlayerStats } from './types';
import StatRow from './StatRow';

interface PlayerPerformanceCardProps {
  player: DetailedPlayerStats;
  onSelect?: () => void;
  isSelected?: boolean;
  showMatchHistory?: boolean;
  matchHistoryCount?: number;
}

export default function PlayerPerformanceCard({
  player,
  onSelect,
  isSelected = false,
  showMatchHistory = true,
  matchHistoryCount = 3
}: PlayerPerformanceCardProps) {

  // Helper to determine highlight color based on value
  const getPointsHighlight = (points: number) => {
    if (points >= 100) return 'excellent';
    if (points >= 50) return 'good';
    if (points >= 20) return 'average';
    return 'poor';
  };

  const getStrikeRateHighlight = (sr: number) => {
    if (sr >= 140) return 'excellent';
    if (sr >= 120) return 'good';
    if (sr >= 100) return 'average';
    return 'poor';
  };

  const getEconomyHighlight = (econ: number | null) => {
    if (!econ) return 'neutral';
    if (econ <= 4.0) return 'excellent';
    if (econ <= 5.5) return 'good';
    if (econ <= 7.0) return 'average';
    return 'poor';
  };

  // Get role icon
  const getRoleIcon = () => {
    switch (player.role) {
      case 'BATSMAN': return '🏏';
      case 'BOWLER': return '⚾';
      case 'ALL_ROUNDER': return '🌟';
      case 'WICKET_KEEPER': return '🧤';
      default: return '👤';
    }
  };

  // Get form trend icon
  const getFormIcon = () => {
    switch (player.recent_form.trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      default: return '➡️';
    }
  };

  // Get multiplier status icon
  const getMultiplierIcon = () => {
    switch (player.multiplier_info.status) {
      case 'strengthening': return '💪';
      case 'weakening': return '📉';
      default: return '➡️';
    }
  };

  return (
    <div
      className={`
        rounded-lg border-2 overflow-hidden mb-4
        ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}
        ${onSelect ? 'cursor-pointer hover:border-blue-300' : ''}
      `}
      onClick={onSelect}
    >
      {/* Header */}
      <div className={`
        px-4 py-3 flex justify-between items-center
        ${player.is_captain ? 'bg-yellow-100' : player.is_vice_captain ? 'bg-blue-100' : 'bg-gray-50'}
      `}>
        <div className="flex items-center gap-2">
          <span className="text-2xl">{getRoleIcon()}</span>
          <div>
            <div className="font-bold text-gray-900 flex items-center gap-2">
              {player.name}
              {player.is_captain && <span className="text-sm">👑 C</span>}
              {player.is_vice_captain && <span className="text-sm">⭐ VC</span>}
              {player.is_wicket_keeper && <span className="text-sm">🧤 WK</span>}
            </div>
            <div className="text-sm text-gray-600">{player.club_name}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">{player.total_points.toFixed(1)}</div>
          <div className="text-xs text-gray-600">pts</div>
        </div>
      </div>

      {/* Stats Grid - Mobile optimized */}
      <div className="p-4 space-y-3">

        {/* Overview Stats */}
        <div className="grid grid-cols-2 gap-2">
          <StatRow
            label="Matches"
            value={player.matches_played}
            icon="🎮"
          />
          <StatRow
            label="Avg/Match"
            value={player.points_per_match.toFixed(1)}
            highlight={getPointsHighlight(player.points_per_match)}
          />
        </div>

        {/* Batting Stats (if relevant) */}
        {player.batting.runs > 0 && (
          <div className="border-t-2 border-blue-100 pt-3">
            <div className="text-xs font-semibold text-blue-900 mb-2 bg-blue-50 px-2 py-1 rounded">
              🏏 BATTING
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Runs</span>
                <span className="font-semibold">{player.batting.runs}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg</span>
                <span className="font-semibold">{player.batting.average.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">SR</span>
                <span className={`font-semibold px-1.5 py-0.5 rounded ${
                  player.batting.strike_rate >= 120 ? 'bg-green-100 text-green-900' :
                  player.batting.strike_rate >= 100 ? 'bg-blue-100 text-blue-900' :
                  'bg-amber-100 text-amber-900'
                }`}>
                  {player.batting.strike_rate.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">HS</span>
                <span className="font-semibold">{player.batting.highest_score}</span>
              </div>
            </div>
            <div className="flex gap-4 mt-2 text-xs text-gray-600">
              {player.batting.hundreds > 0 && <span>💯 {player.batting.hundreds}</span>}
              {player.batting.fifties > 0 && <span>5️⃣0️⃣ {player.batting.fifties}</span>}
              <span>4️⃣ {player.batting.fours}</span>
              <span>6️⃣ {player.batting.sixes}</span>
              {player.batting.ducks > 0 && <span className="text-red-600">🦆 {player.batting.ducks}</span>}
            </div>
          </div>
        )}

        {/* Bowling Stats (if relevant) */}
        {player.bowling.wickets > 0 && (
          <div className="border-t-2 border-red-100 pt-3">
            <div className="text-xs font-semibold text-red-900 mb-2 bg-red-50 px-2 py-1 rounded">
              ⚾ BOWLING
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Wickets</span>
                <span className="font-semibold">{player.bowling.wickets}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Overs</span>
                <span className="font-semibold">{player.bowling.overs.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg</span>
                <span className="font-semibold">
                  {player.bowling.average ? player.bowling.average.toFixed(1) : '-'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Econ</span>
                <span className={`font-semibold px-1.5 py-0.5 rounded ${
                  player.bowling.economy && player.bowling.economy <= 5.0 ? 'bg-green-100 text-green-900' :
                  player.bowling.economy && player.bowling.economy <= 6.5 ? 'bg-blue-100 text-blue-900' :
                  'bg-amber-100 text-amber-900'
                }`}>
                  {player.bowling.economy ? player.bowling.economy.toFixed(2) : '-'}
                </span>
              </div>
            </div>
            <div className="flex gap-4 mt-2 text-xs text-gray-600">
              {player.bowling.maidens > 0 && <span>⚪ {player.bowling.maidens}M</span>}
              {player.bowling.five_wicket_hauls > 0 && <span>5️⃣W {player.bowling.five_wicket_hauls}</span>}
            </div>
          </div>
        )}

        {/* Fielding Stats (if relevant) */}
        {(player.fielding.catches + player.fielding.run_outs + player.fielding.stumpings) > 0 && (
          <div className="border-t-2 border-green-100 pt-3">
            <div className="text-xs font-semibold text-green-900 mb-2 bg-green-50 px-2 py-1 rounded">
              🧤 FIELDING
            </div>
            <div className="flex gap-4 text-sm">
              {player.fielding.catches > 0 && (
                <div>
                  <span className="text-gray-600">Catches:</span>
                  <span className="font-semibold ml-1">{player.fielding.catches}</span>
                </div>
              )}
              {player.fielding.run_outs > 0 && (
                <div>
                  <span className="text-gray-600">Run Outs:</span>
                  <span className="font-semibold ml-1">{player.fielding.run_outs}</span>
                </div>
              )}
              {player.fielding.stumpings > 0 && (
                <div>
                  <span className="text-gray-600">Stumpings:</span>
                  <span className="font-semibold ml-1">{player.fielding.stumpings}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Points Breakdown */}
        <div className="border-t-2 border-gray-100 pt-3">
          <div className="text-xs font-semibold text-gray-700 mb-2">📊 POINTS BREAKDOWN</div>
          <div className="grid grid-cols-3 gap-1 text-xs">
            <div className="bg-blue-50 p-2 rounded text-center">
              <div className="text-gray-600">Batting</div>
              <div className="font-bold text-blue-900">{player.points_breakdown.batting_points.toFixed(1)}</div>
            </div>
            <div className="bg-red-50 p-2 rounded text-center">
              <div className="text-gray-600">Bowling</div>
              <div className="font-bold text-red-900">{player.points_breakdown.bowling_points.toFixed(1)}</div>
            </div>
            <div className="bg-green-50 p-2 rounded text-center">
              <div className="text-gray-600">Fielding</div>
              <div className="font-bold text-green-900">{player.points_breakdown.fielding_points.toFixed(1)}</div>
            </div>
          </div>
        </div>

        {/* Multiplier Info */}
        <div className="border-t-2 border-gray-100 pt-3">
          <div className="text-xs font-semibold text-gray-700 mb-2">⚡ MULTIPLIER</div>
          <div className="flex justify-between items-center text-sm">
            <div>
              <span className="text-gray-600">Start:</span>
              <span className="font-semibold ml-1">{player.multiplier_info.starting_multiplier.toFixed(2)}</span>
              <span className="mx-2">→</span>
              <span className="text-gray-600">Now:</span>
              <span className="font-semibold ml-1">{player.multiplier_info.current_multiplier.toFixed(2)}</span>
            </div>
            <span className="text-lg">{getMultiplierIcon()}</span>
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {player.multiplier_info.status === 'strengthening' && '💪 Getting stronger (lower handicap)'}
            {player.multiplier_info.status === 'weakening' && '📉 Getting weaker (higher handicap)'}
            {player.multiplier_info.status === 'stable' && '➡️ Stable performance'}
          </div>
        </div>

        {/* Recent Form (configurable) */}
        {showMatchHistory && player.recent_form.matches.length > 0 && (
          <div className="border-t-2 border-gray-100 pt-3">
            <div className="text-xs font-semibold text-gray-700 mb-2 flex justify-between items-center">
              <span>🔥 RECENT FORM (Last {matchHistoryCount})</span>
              <span className="text-lg">{getFormIcon()}</span>
            </div>
            <div className="space-y-1">
              {player.recent_form.matches.slice(0, matchHistoryCount).map((match, idx) => (
                <div key={idx} className={`
                  flex justify-between items-center text-xs p-2 rounded
                  ${match.points >= 50 ? 'bg-green-50' :
                    match.points >= 20 ? 'bg-blue-50' :
                    'bg-gray-50'}
                `}>
                  <div className="flex gap-2">
                    <span className="font-semibold text-gray-700">Wk {match.round}</span>
                    {match.runs > 0 && <span>🏏 {match.runs}r</span>}
                    {match.wickets > 0 && <span>⚾ {match.wickets}w</span>}
                    {match.catches > 0 && <span>🧤 {match.catches}c</span>}
                  </div>
                  <span className="font-bold">{match.points.toFixed(1)} pts</span>
                </div>
              ))}
            </div>
            <div className="mt-2 text-xs text-gray-600">
              Avg: <span className="font-semibold">{player.recent_form.last_n_average.toFixed(1)} pts</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### File 4: `frontend/app/leagues/[league_id]/leaderboard/components/PlayerComparisonModal.tsx`

```typescript
'use client';

import { DetailedPlayerStats } from './types';

interface PlayerComparisonModalProps {
  player1: DetailedPlayerStats;
  player2: DetailedPlayerStats;
  onClose: () => void;
}

export default function PlayerComparisonModal({ player1, player2, onClose }: PlayerComparisonModalProps) {

  // Helper to compare values and return highlight class
  const getComparisonClass = (value1: number, value2: number, higherIsBetter: boolean = true) => {
    if (value1 === value2) return 'bg-gray-50';
    const isBetter = higherIsBetter ? value1 > value2 : value1 < value2;
    return isBetter ? 'bg-green-100 font-bold' : 'bg-red-50';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">Player Comparison</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Comparison Table */}
        <div className="p-4">
          {/* Player Names */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="font-bold text-gray-600">Stat</div>
            <div className="text-center">
              <div className="font-bold text-lg">{player1.name}</div>
              <div className="text-sm text-gray-600">{player1.club_name}</div>
            </div>
            <div className="text-center">
              <div className="font-bold text-lg">{player2.name}</div>
              <div className="text-sm text-gray-600">{player2.club_name}</div>
            </div>
          </div>

          {/* Overview */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-gray-700 mb-2 bg-gray-100 px-2 py-1 rounded">
              OVERVIEW
            </h3>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="text-gray-600">Total Points</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.total_points, player2.total_points)}`}>
                {player1.total_points.toFixed(1)}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.total_points, player1.total_points)}`}>
                {player2.total_points.toFixed(1)}
              </div>

              <div className="text-gray-600">Matches</div>
              <div className="text-center p-2 rounded bg-gray-50">{player1.matches_played}</div>
              <div className="text-center p-2 rounded bg-gray-50">{player2.matches_played}</div>

              <div className="text-gray-600">Avg/Match</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.points_per_match, player2.points_per_match)}`}>
                {player1.points_per_match.toFixed(1)}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.points_per_match, player1.points_per_match)}`}>
                {player2.points_per_match.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Batting */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-blue-900 mb-2 bg-blue-50 px-2 py-1 rounded">
              🏏 BATTING
            </h3>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="text-gray-600">Runs</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.batting.runs, player2.batting.runs)}`}>
                {player1.batting.runs}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.batting.runs, player1.batting.runs)}`}>
                {player2.batting.runs}
              </div>

              <div className="text-gray-600">Average</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.batting.average, player2.batting.average)}`}>
                {player1.batting.average.toFixed(1)}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.batting.average, player1.batting.average)}`}>
                {player2.batting.average.toFixed(1)}
              </div>

              <div className="text-gray-600">Strike Rate</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.batting.strike_rate, player2.batting.strike_rate)}`}>
                {player1.batting.strike_rate.toFixed(1)}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.batting.strike_rate, player1.batting.strike_rate)}`}>
                {player2.batting.strike_rate.toFixed(1)}
              </div>

              <div className="text-gray-600">Highest Score</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.batting.highest_score, player2.batting.highest_score)}`}>
                {player1.batting.highest_score}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.batting.highest_score, player1.batting.highest_score)}`}>
                {player2.batting.highest_score}
              </div>

              <div className="text-gray-600">Boundaries</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.batting.fours + player1.batting.sixes, player2.batting.fours + player2.batting.sixes)}`}>
                4s: {player1.batting.fours}, 6s: {player1.batting.sixes}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.batting.fours + player2.batting.sixes, player1.batting.fours + player1.batting.sixes)}`}>
                4s: {player2.batting.fours}, 6s: {player2.batting.sixes}
              </div>
            </div>
          </div>

          {/* Bowling */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-red-900 mb-2 bg-red-50 px-2 py-1 rounded">
              ⚾ BOWLING
            </h3>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="text-gray-600">Wickets</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.bowling.wickets, player2.bowling.wickets)}`}>
                {player1.bowling.wickets}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.bowling.wickets, player1.bowling.wickets)}`}>
                {player2.bowling.wickets}
              </div>

              <div className="text-gray-600">Economy</div>
              <div className={`text-center p-2 rounded ${
                player1.bowling.economy && player2.bowling.economy
                  ? getComparisonClass(player1.bowling.economy, player2.bowling.economy, false)
                  : 'bg-gray-50'
              }`}>
                {player1.bowling.economy?.toFixed(2) || '-'}
              </div>
              <div className={`text-center p-2 rounded ${
                player1.bowling.economy && player2.bowling.economy
                  ? getComparisonClass(player2.bowling.economy, player1.bowling.economy, false)
                  : 'bg-gray-50'
              }`}>
                {player2.bowling.economy?.toFixed(2) || '-'}
              </div>

              <div className="text-gray-600">Average</div>
              <div className={`text-center p-2 rounded ${
                player1.bowling.average && player2.bowling.average
                  ? getComparisonClass(player1.bowling.average, player2.bowling.average, false)
                  : 'bg-gray-50'
              }`}>
                {player1.bowling.average?.toFixed(1) || '-'}
              </div>
              <div className={`text-center p-2 rounded ${
                player1.bowling.average && player2.bowling.average
                  ? getComparisonClass(player2.bowling.average, player1.bowling.average, false)
                  : 'bg-gray-50'
              }`}>
                {player2.bowling.average?.toFixed(1) || '-'}
              </div>
            </div>
          </div>

          {/* Fielding */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-green-900 mb-2 bg-green-50 px-2 py-1 rounded">
              🧤 FIELDING
            </h3>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="text-gray-600">Catches</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.fielding.catches, player2.fielding.catches)}`}>
                {player1.fielding.catches}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.fielding.catches, player1.fielding.catches)}`}>
                {player2.fielding.catches}
              </div>

              <div className="text-gray-600">Run Outs</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.fielding.run_outs, player2.fielding.run_outs)}`}>
                {player1.fielding.run_outs}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.fielding.run_outs, player1.fielding.run_outs)}`}>
                {player2.fielding.run_outs}
              </div>

              {player1.fielding.stumpings > 0 || player2.fielding.stumpings > 0 ? (
                <>
                  <div className="text-gray-600">Stumpings</div>
                  <div className={`text-center p-2 rounded ${getComparisonClass(player1.fielding.stumpings, player2.fielding.stumpings)}`}>
                    {player1.fielding.stumpings}
                  </div>
                  <div className={`text-center p-2 rounded ${getComparisonClass(player2.fielding.stumpings, player1.fielding.stumpings)}`}>
                    {player2.fielding.stumpings}
                  </div>
                </>
              ) : null}
            </div>
          </div>

          {/* Form */}
          <div>
            <h3 className="text-sm font-bold text-gray-700 mb-2 bg-gray-100 px-2 py-1 rounded">
              🔥 RECENT FORM
            </h3>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="text-gray-600">Last 3 Avg</div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player1.recent_form.last_n_average, player2.recent_form.last_n_average)}`}>
                {player1.recent_form.last_n_average.toFixed(1)}
              </div>
              <div className={`text-center p-2 rounded ${getComparisonClass(player2.recent_form.last_n_average, player1.recent_form.last_n_average)}`}>
                {player2.recent_form.last_n_average.toFixed(1)}
              </div>

              <div className="text-gray-600">Trend</div>
              <div className="text-center p-2 rounded bg-gray-50">
                {player1.recent_form.trend === 'improving' ? '📈' :
                 player1.recent_form.trend === 'declining' ? '📉' : '➡️'}
              </div>
              <div className="text-center p-2 rounded bg-gray-50">
                {player2.recent_form.trend === 'improving' ? '📈' :
                 player2.recent_form.trend === 'declining' ? '📉' : '➡️'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

### File 5: `frontend/app/leagues/[league_id]/leaderboard/components/TeamDetailedModal.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { DetailedTeamResponse, DetailedPlayerStats } from './types';
import PlayerPerformanceCard from './PlayerPerformanceCard';
import PlayerComparisonModal from './PlayerComparisonModal';

interface TeamDetailedModalProps {
  league_id: string;
  team_id: string;
  onClose: () => void;
}

export default function TeamDetailedModal({ league_id, team_id, onClose }: TeamDetailedModalProps) {
  const [teamData, setTeamData] = useState<DetailedTeamResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matchHistoryCount, setMatchHistoryCount] = useState(3);
  const [selectedPlayers, setSelectedPlayers] = useState<DetailedPlayerStats[]>([]);
  const [showComparison, setShowComparison] = useState(false);

  useEffect(() => {
    fetchTeamData();
  }, [team_id, matchHistoryCount]);

  const fetchTeamData = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/leagues/${league_id}/teams/${team_id}/detailed?match_count=${matchHistoryCount}`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch team data');
      }

      const data = await response.json();
      setTeamData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerSelect = (player: DetailedPlayerStats) => {
    if (selectedPlayers.find(p => p.player_id === player.player_id)) {
      // Deselect
      setSelectedPlayers(selectedPlayers.filter(p => p.player_id !== player.player_id));
    } else {
      // Select (max 2)
      if (selectedPlayers.length < 2) {
        setSelectedPlayers([...selectedPlayers, player]);
      }
    }
  };

  const handleCompare = () => {
    if (selectedPlayers.length === 2) {
      setShowComparison(true);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading team stats...</p>
        </div>
      </div>
    );
  }

  if (error || !teamData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-6 max-w-md">
          <h3 className="text-lg font-bold text-red-600 mb-2">Error</h3>
          <p className="text-gray-700">{error || 'Failed to load team data'}</p>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header - Sticky */}
          <div className="sticky top-0 bg-gradient-to-r from-green-600 to-green-700 text-white p-4 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">{teamData.team_name}</h2>
              <p className="text-green-100">{teamData.owner_name}</p>
              <div className="flex gap-4 mt-2 text-sm">
                <span>📊 {teamData.total_points.toFixed(1)} pts</span>
                <span>📅 Week: {teamData.weekly_points.toFixed(1)} pts</span>
                <span>👥 {teamData.squad_size} players</span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-green-200 text-3xl font-light"
            >
              ×
            </button>
          </div>

          {/* Controls */}
          <div className="bg-gray-50 border-b border-gray-200 p-3 flex flex-wrap justify-between items-center gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-700">Match History:</label>
              <select
                value={matchHistoryCount}
                onChange={(e) => setMatchHistoryCount(Number(e.target.value))}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value={1}>Last 1</option>
                <option value={3}>Last 3</option>
                <option value={5}>Last 5</option>
                <option value={10}>Last 10</option>
              </select>
            </div>

            {selectedPlayers.length === 2 && (
              <button
                onClick={handleCompare}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm font-semibold"
              >
                Compare Selected Players →
              </button>
            )}

            {selectedPlayers.length > 0 && (
              <button
                onClick={() => setSelectedPlayers([])}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Clear Selection ({selectedPlayers.length})
              </button>
            )}
          </div>

          {selectedPlayers.length > 0 && selectedPlayers.length < 2 && (
            <div className="bg-blue-50 border-b border-blue-200 p-2 text-center text-sm text-blue-900">
              Select 1 more player to compare
            </div>
          )}

          {/* Player Cards - Scrollable */}
          <div className="flex-1 overflow-y-auto p-4">
            {teamData.players.map((player) => (
              <PlayerPerformanceCard
                key={player.player_id}
                player={player}
                onSelect={() => handlePlayerSelect(player)}
                isSelected={selectedPlayers.some(p => p.player_id === player.player_id)}
                showMatchHistory={true}
                matchHistoryCount={matchHistoryCount}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Comparison Modal */}
      {showComparison && selectedPlayers.length === 2 && (
        <PlayerComparisonModal
          player1={selectedPlayers[0]}
          player2={selectedPlayers[1]}
          onClose={() => setShowComparison(false)}
        />
      )}
    </>
  );
}
```

---

### File 6: Update `frontend/app/leagues/[league_id]/leaderboard/page.tsx`

**Change the modal trigger** (around line 200-250 where the simple modal currently opens):

```typescript
// REPLACE the existing simple modal with:
import TeamDetailedModal from './components/TeamDetailedModal';

// In the component:
const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);

// Update the team name click handler:
<button
  onClick={() => setSelectedTeamId(team.team_id)}
  className="text-blue-600 hover:text-blue-800 font-semibold"
>
  {team.team_name}
</button>

// Replace the modal rendering:
{selectedTeamId && (
  <TeamDetailedModal
    league_id={league_id}
    team_id={selectedTeamId}
    onClose={() => setSelectedTeamId(null)}
  />
)}
```

---

## 3️⃣ DEPLOYMENT STEPS

### Backend Deployment
```bash
# 1. SSH to production
ssh ubuntu@45.135.59.210

# 2. Navigate to backend
cd /app/fantasy-cricket-leafcloud/backend

# 3. Edit main.py and add the new endpoint after line 384
# (Use the code from Section 1 above)

# 4. Restart API container
docker restart fantasy_cricket_api

# 5. Test endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/leagues/YOUR_LEAGUE_ID/teams/YOUR_TEAM_ID/detailed?match_count=3"
```

### Frontend Deployment
```bash
# 1. Create new components directory
cd /Users/guypa/Github/fantasy-cricket-leafcloud/frontend/app/leagues/[league_id]/leaderboard
mkdir -p components

# 2. Create all component files (from Section 2)
# - types.ts
# - StatRow.tsx
# - PlayerPerformanceCard.tsx
# - PlayerComparisonModal.tsx
# - TeamDetailedModal.tsx

# 3. Update page.tsx with new modal trigger

# 4. Test locally
cd /Users/guypa/Github/fantasy-cricket-leafcloud/frontend
npm run dev

# 5. Build and deploy
npm run build
# Deploy to production (scp or git push, depending on your workflow)
```

---

## 4️⃣ TESTING CHECKLIST

- [ ] Backend endpoint returns correct data structure
- [ ] Player stats aggregate correctly from player_performances
- [ ] Recent form calculates trend properly
- [ ] Multiplier drift displays correctly
- [ ] Frontend modal opens on team click
- [ ] Player cards display all stats sections
- [ ] Batting stats show for batsmen/all-rounders
- [ ] Bowling stats show for bowlers/all-rounders
- [ ] Fielding stats show when relevant
- [ ] Match history count selector works
- [ ] Player selection (checkboxes) works
- [ ] Compare button enables with 2 players selected
- [ ] Comparison modal shows side-by-side stats
- [ ] Color coding highlights better/worse stats
- [ ] Mobile responsive (cards stack vertically)
- [ ] Captain/VC badges display correctly
- [ ] Icons and emojis render properly
- [ ] Loading state shows while fetching
- [ ] Error handling works for API failures

---

## 5️⃣ ESTIMATED IMPLEMENTATION TIME

- Backend endpoint: **2-3 hours**
- TypeScript types: **30 minutes**
- StatRow component: **30 minutes**
- PlayerPerformanceCard: **2-3 hours** (most complex)
- PlayerComparisonModal: **2 hours**
- TeamDetailedModal: **1-2 hours**
- Integration & testing: **2-3 hours**

**Total: 10-14 hours**

---

## 📝 REVIEW QUESTIONS

Before implementing, please confirm:

1. **Visual Style**: Happy with colored tables + icons instead of charts?
2. **Default Match Count**: Is 3 matches a good default?
3. **Comparison Feature**: The "select 2 players" approach work for you?
4. **Mobile Priority**: Cards stacking vertically on mobile - good?
5. **Color Scheme**: Green/Blue/Red highlights ok? Need adjustments?
6. **Any Missing Stats**: Anything else you want to see?

---

**Status**: ⏸️ Ready to implement - awaiting your approval
