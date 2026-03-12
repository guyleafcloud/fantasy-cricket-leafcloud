# 🏆 Leaderboard & Player Performance Enhancement Plan

**Date**: 2025-12-16
**Goal**: Add detailed stats categories and comprehensive player performance breakdown to the leaderboard system

---

## 📊 Current State Analysis

### What Exists Now

**Leaderboard Page** (`frontend/app/leagues/[league_id]/leaderboard/page.tsx`):
- ✅ Team rankings with total points
- ✅ Best batsman/bowler/fielder cards
- ✅ Top 25 players by fantasy points
- ✅ Multiplier trends (handicap system display)
- ✅ Team modal showing basic roster

**Team Modal** (current limitation):
- Shows: Player name, IRL team, total points, captain/VC/WK badges
- ❌ Does NOT show: Batting stats, bowling stats, fielding stats, match history

**Available Data** (in `player_performances` table):
- ✅ Full batting breakdown (runs, balls, 4s, 6s, strike rate, dismissals)
- ✅ Full bowling breakdown (overs, wickets, maidens, economy)
- ✅ Full fielding breakdown (catches, run-outs, stumpings)
- ✅ Points breakdown (base, multiplier, captain bonus, final)
- ✅ Match-by-match history with round numbers

---

## 🎯 Enhancement Objectives

### Primary Goals
1. **Add more stat categories to leaderboard** - Make it richer and more informative
2. **Show detailed player performance** - Allow users to see exactly how each player earned points
3. **Enable team analysis** - Let users compare player contributions within a team
4. **Improve engagement** - Give users more reasons to check leaderboard frequently

### User Stories
- **As a user**, I want to see how my players performed (batting, bowling, fielding) so I can understand why they scored X points
- **As a user**, I want to see which matches my players contributed most in so I can track their form
- **As a user**, I want to compare my team's player stats with opponents' teams
- **As a user**, I want to see weekly trends to identify improving/declining players

---

## 📋 Implementation Plan

### Phase 1: Enhanced Team Modal (Priority: HIGH)
**Goal**: Replace basic team modal with detailed player performance breakdown

#### 1.1 Backend API Enhancement
**New Endpoint**: `GET /api/leagues/{league_id}/teams/{team_id}/detailed`

**Response Structure**:
```json
{
  "team_id": "uuid",
  "team_name": "Thunder Strikers",
  "owner_name": "John Doe",
  "total_points": 2456.8,
  "weekly_points": 187.3,
  "squad_size": 11,
  "players": [
    {
      "player_id": "uuid",
      "name": "M Boendermaker",
      "club_name": "ACC 1",
      "role": "BATSMAN",
      "is_captain": true,
      "is_vice_captain": false,
      "is_wicket_keeper": false,

      "total_points": 345.6,
      "matches_played": 8,
      "points_per_match": 43.2,

      "batting": {
        "runs": 456,
        "average": 57.0,
        "strike_rate": 142.5,
        "balls_faced": 320,
        "fours": 45,
        "sixes": 12,
        "fifties": 3,
        "hundreds": 1,
        "ducks": 0,
        "highest_score": 102
      },

      "bowling": {
        "wickets": 5,
        "overs": 24.0,
        "maidens": 2,
        "runs_conceded": 145,
        "economy": 6.04,
        "average": 29.0,
        "best_figures": "3/18",
        "five_wicket_hauls": 0
      },

      "fielding": {
        "catches": 6,
        "run_outs": 1,
        "stumpings": 0
      },

      "multiplier_info": {
        "starting_multiplier": 1.5,
        "current_multiplier": 1.2,
        "drift": -0.3,
        "status": "strengthening"
      },

      "recent_form": {
        "last_5_matches": [
          {
            "round": 12,
            "match_id": "7258345",
            "opponent": "vs VRA 1",
            "points": 67.8,
            "runs": 45,
            "wickets": 2,
            "catches": 1
          }
        ],
        "last_5_average": 52.3,
        "trend": "improving"
      },

      "points_breakdown": {
        "batting_points": 234.5,
        "bowling_points": 87.3,
        "fielding_points": 23.8,
        "base_total": 345.6,
        "captain_bonus": 0,
        "final_points": 345.6
      }
    }
  ]
}
```

**Backend File**: `backend/main.py` or new `backend/team_detailed_stats.py`

**SQL Query Structure**:
```sql
-- Aggregate player performance across all matches
SELECT
    p.id, p.name, p.rl_team, p.role,
    ftp.is_captain, ftp.is_vice_captain, ftp.is_wicket_keeper,
    ftp.total_points,

    -- Batting aggregates
    COUNT(pp.id) as matches_played,
    SUM(pp.runs) as total_runs,
    AVG(pp.runs) as batting_average,
    AVG(CASE WHEN pp.balls_faced > 0 THEN pp.batting_strike_rate END) as avg_strike_rate,
    SUM(pp.balls_faced) as total_balls,
    SUM(pp.fours) as total_fours,
    SUM(pp.sixes) as total_sixes,
    SUM(CASE WHEN pp.runs >= 50 AND pp.runs < 100 THEN 1 ELSE 0 END) as fifties,
    SUM(CASE WHEN pp.runs >= 100 THEN 1 ELSE 0 END) as hundreds,
    SUM(CASE WHEN pp.runs = 0 AND pp.is_out THEN 1 ELSE 0 END) as ducks,
    MAX(pp.runs) as highest_score,

    -- Bowling aggregates
    SUM(pp.wickets) as total_wickets,
    SUM(pp.overs_bowled) as total_overs,
    SUM(pp.maidens) as total_maidens,
    SUM(pp.runs_conceded) as total_runs_conceded,
    AVG(pp.bowling_economy) as avg_economy,
    SUM(CASE WHEN pp.wickets >= 5 THEN 1 ELSE 0 END) as five_wicket_hauls,

    -- Fielding aggregates
    SUM(pp.catches) as total_catches,
    SUM(pp.run_outs) as total_run_outs,
    SUM(pp.stumpings) as total_stumpings,

    -- Multiplier info
    p.starting_multiplier,
    p.multiplier as current_multiplier,

    -- Points breakdown (need to calculate)
    SUM(CASE WHEN pp.batting_strike_rate > 0 THEN pp.fantasy_points * 0.7 ELSE 0 END) as batting_points_est,
    SUM(CASE WHEN pp.wickets > 0 THEN pp.fantasy_points * 0.25 ELSE 0 END) as bowling_points_est,
    SUM(pp.catches * 15 + pp.run_outs * 6 + pp.stumpings * 15) as fielding_points_exact

FROM fantasy_team_players ftp
JOIN players p ON ftp.player_id = p.id
LEFT JOIN player_performances pp ON pp.player_id = p.id
WHERE ftp.fantasy_team_id = :team_id
GROUP BY p.id, ftp.is_captain, ftp.is_vice_captain, ftp.is_wicket_keeper, ftp.total_points
ORDER BY ftp.total_points DESC
```

**Backend Implementation**:
1. Create endpoint handler in `backend/main.py`
2. Add query function in `backend/database_queries.py` (or similar)
3. Calculate recent form (last 5 matches) as subquery
4. Return formatted JSON response

**Estimated Time**: 3-4 hours

---

#### 1.2 Frontend: Enhanced Team Modal
**Component**: Update `frontend/app/leagues/[league_id]/leaderboard/page.tsx`

**New UI Sections**:

**A. Player Card Layout** (replace simple table):
```
┌─────────────────────────────────────────────────────────────┐
│ 🏏 M BOENDERMAKER (ACC 1) - Batsman           [C] 345.6 pts │
├─────────────────────────────────────────────────────────────┤
│ BATTING                                                      │
│ 456 runs @ 57.0 avg | SR: 142.5 | 45×4s, 12×6s | 3×50s 1×💯│
│                                                              │
│ BOWLING                                                      │
│ 5 wkts @ 29.0 avg | Econ: 6.04 | 24 overs | Best: 3/18     │
│                                                              │
│ FIELDING                                                     │
│ 6 catches | 1 run out                                       │
│                                                              │
│ POINTS BREAKDOWN                                             │
│ Batting: 234.5 | Bowling: 87.3 | Fielding: 23.8             │
│ Multiplier: 1.5 → 1.2 (↓ strengthening)                    │
│                                                              │
│ RECENT FORM (Last 5 matches)                                │
│ Week 12: 67.8 pts (45 runs, 2 wkts) vs VRA 1               │
│ Week 11: 45.2 pts (28 runs, 1 wkt) vs Quick 1              │
│ ...                                                          │
│ Avg: 52.3 pts | Trend: 📈 Improving                        │
└─────────────────────────────────────────────────────────────┘
```

**B. Tab System** (optional enhancement):
- **Summary** tab: Current card view with all stats
- **Match History** tab: Full match-by-match breakdown
- **Comparison** tab: Compare with league average for same role

**UI Components to Create**:
1. `<PlayerPerformanceCard>` - Main card component
2. `<StatBar>` - Visual bar chart for quick comparison
3. `<RecentFormList>` - Last 5 matches display
4. `<PointsBreakdown>` - Pie chart or stacked bar showing point sources

**TypeScript Interfaces**:
```typescript
interface DetailedPlayerStats {
  player_id: string;
  name: string;
  club_name: string;
  role: PlayerRole;
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

interface BattingStats {
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

// ... similar for bowling, fielding, etc.
```

**Estimated Time**: 5-6 hours

---

### Phase 2: Additional Leaderboard Stats (Priority: MEDIUM)

#### 2.1 Team Comparison Section
**Location**: Below existing leaderboard table

**New Section**: "Team Analysis"
- **Most Balanced Team**: Team with most even point distribution across players
- **Captain Effectiveness**: Teams ranked by captain bonus contribution
- **Best Transfer Strategy**: Team with highest points from transferred players
- **Consistency Score**: Standard deviation of weekly points (lower = more consistent)

**API Addition**: Add these metrics to existing `/api/leagues/{league_id}/leaderboard` response

**UI Design**:
```
┌──────────────────────────────────────────────────┐
│ 📊 TEAM ANALYSIS                                  │
├──────────────────────────────────────────────────┤
│ Most Balanced: Thunder Strikers                  │
│   • All 11 players scored 20+ points this week  │
│                                                   │
│ Best Captain Pick: Royal Challengers             │
│   • Captain scored 124 pts (248 after 2x bonus) │
│                                                   │
│ Most Consistent: Cricket Kings                   │
│   • Avg weekly score: 156 ± 12 pts              │
└──────────────────────────────────────────────────┘
```

**Estimated Time**: 3-4 hours

---

#### 2.2 League-Wide Player Stats Table
**New Tab/Section**: "All Players" (alongside "Leaderboard" and "Top Performers")

**Filters**:
- Role: All / Batsmen / Bowlers / All-Rounders / Wicket-Keepers
- Stat Type: Total Points / Runs / Wickets / Catches
- Ownership: All / Most Owned / Least Owned

**Columns**:
- Rank
- Player Name
- IRL Team
- Role
- Total Points
- Ownership (% of teams)
- Runs (if batsman/all-rounder)
- Wickets (if bowler/all-rounder)
- Catches
- Multiplier
- Trend

**API**: `GET /api/leagues/{league_id}/all-players?role=BATSMAN&sort=points`

**Estimated Time**: 4-5 hours

---

### Phase 3: Advanced Features (Priority: LOW)

#### 3.1 Player Profile Page
**New Route**: `/players/[player_id]`

**Content**:
- Full season statistics
- Match-by-match chart (points over time)
- Ownership info (% of teams, price trends)
- Head-to-head vs other top players
- Career highlights (best bowling, highest score, etc.)

**Estimated Time**: 6-8 hours

---

#### 3.2 Weekly Breakdown View
**Enhancement**: Add "Week-by-Week" tab to leaderboard

Shows:
- Rankings change over time (line chart)
- Each week's top scorer
- Biggest movers (up/down in rankings)

**Estimated Time**: 4-5 hours

---

#### 3.3 Live Match Tracking (Future)
When matches are in progress:
- Real-time score updates
- "Players Currently Playing" indicator
- Projected points based on live scores

**Note**: Requires real-time data feed (complex)

**Estimated Time**: 15-20 hours (low priority)

---

## 🏗️ Technical Implementation Details

### Backend Changes Required

**File Structure**:
```
backend/
├── main.py (add new endpoints)
├── team_detailed_stats.py (NEW - player performance aggregation)
├── league_analytics.py (NEW - team comparison metrics)
└── database_queries.py (update with new queries)
```

**Database Queries**:
1. Player aggregated stats query (as shown above)
2. Recent form query (last 5 matches per player)
3. Points breakdown calculation
4. Team comparison metrics

**Caching**:
- Cache detailed stats for 5 minutes (matches weekly update schedule)
- Use Redis key: `team_detailed:{league_id}:{team_id}`

---

### Frontend Changes Required

**File Structure**:
```
frontend/app/leagues/[league_id]/
├── leaderboard/
│   ├── page.tsx (update with enhanced modal)
│   ├── components/
│   │   ├── TeamDetailedModal.tsx (NEW - enhanced modal)
│   │   ├── PlayerPerformanceCard.tsx (NEW)
│   │   ├── StatBar.tsx (NEW)
│   │   ├── RecentFormList.tsx (NEW)
│   │   └── PointsBreakdown.tsx (NEW)
│   └── types.ts (NEW - TypeScript interfaces)
└── all-players/
    └── page.tsx (NEW - Phase 2.2)
```

**Component Hierarchy**:
```
LeaderboardPage
├── LeaderboardTable (existing)
├── TeamDetailedModal (NEW - replaces simple modal)
│   └── PlayerPerformanceCard[] (NEW)
│       ├── StatBar (NEW)
│       ├── RecentFormList (NEW)
│       └── PointsBreakdown (NEW)
└── TeamAnalysisSection (NEW - Phase 2.1)
```

---

## ⏱️ Time Estimates

### Phase 1 (High Priority): Enhanced Team Modal
- Backend API: 3-4 hours
- Frontend UI: 5-6 hours
- Testing: 2 hours
- **Total: 10-12 hours**

### Phase 2 (Medium Priority): Additional Stats
- Team Analysis Section: 3-4 hours
- All Players Table: 4-5 hours
- Testing: 2 hours
- **Total: 9-11 hours**

### Phase 3 (Low Priority): Advanced Features
- Player Profile Page: 6-8 hours
- Weekly Breakdown: 4-5 hours
- Testing: 2 hours
- **Total: 12-15 hours**

**TOTAL PROJECT TIME: 31-38 hours**

---

## 🎯 Recommended Approach

### Start with Phase 1
**Why**: Biggest impact, uses existing data, solves main user pain point

**Deliverable**: Users can click any team and see detailed breakdown of how each player earned their points

### Then Phase 2.1
**Why**: Adds engagement without major new infrastructure

**Deliverable**: Interesting team comparison metrics that encourage discussion

### Phase 2.2 and Beyond
**Consider based on**:
- User feedback on Phase 1
- Beta tester requests
- Time before 2026 season

---

## 📝 Open Questions for User

Before starting implementation, please confirm:

1. **Priority**: Is Phase 1 (Enhanced Team Modal) the right place to start?

2. **UI Preference**: For the player performance cards, do you prefer:
   - A: Dense information (more stats, compact layout)
   - B: Visual focus (charts, graphs, less text)
   - C: Hybrid (stats with small visual indicators)

3. **Match History**: Should we show:
   - Last 5 matches only (cleaner)
   - All matches with pagination (comprehensive)
   - Configurable (user can choose)

4. **Performance Comparison**: Should player stats show:
   - Just the player's numbers
   - Player vs team average
   - Player vs league average for same role
   - All of the above

5. **Mobile Considerations**: Should we:
   - Build desktop first, mobile later
   - Ensure responsive from the start (adds 20% time)
   - Create separate mobile view

---

## 🚀 Next Steps

1. **Review this plan** and confirm priorities
2. **Answer open questions** above
3. **Start Phase 1 implementation**:
   - Backend API endpoint first
   - Test with sample data
   - Frontend component with mock data
   - Connect frontend to API
   - Polish UI and add animations
4. **Beta test** with small group
5. **Iterate** based on feedback
6. **Deploy** to production

---

**Status**: ⏸️ Awaiting user confirmation to proceed with Phase 1 implementation
