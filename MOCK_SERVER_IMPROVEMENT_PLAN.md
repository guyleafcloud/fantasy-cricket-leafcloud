# Mock Server vs Real KNCB Site - Analysis & Improvement Plan

**Date**: 2025-12-16
**Status**: Analysis Complete, Ready for Implementation
**Goal**: Make mock server more realistic to improve scraper development and testing

---

## Executive Summary

The mock server currently has **two modes**:
1. **RANDOM MODE**: Generates fake data with simple HTML tables (good for quick testing)
2. **PRELOADED MODE**: Serves real 2025 KNCB HTML as 2026 data (excellent for realistic testing)

**Key Finding**: The **PRELOADED MODE already solves the realism problem** by serving actual KNCB HTML. However, there are opportunities to improve the mock server to make testing even better.

---

## Gap Analysis: Mock vs Real KNCB Site

### 1. Real KNCB Site Architecture

**URL**: `https://matchcentre.kncb.nl`

#### Technical Stack:
- **Framework**: React Single Page Application (SPA)
- **Rendering**: Client-side JavaScript (requires 3+ seconds to load)
- **CSS**: styled-components with hashed class names
- **Bundle**: Webpack with code splitting (35 chunks)
- **Analytics**: Google Analytics, FrogBox tracking

#### HTML Structure:
```html
<!doctype html>
<html lang="en">
<head>
  <link href="/static/css/35.f345fc57.chunk.css" rel="stylesheet">
  <link href="/static/css/main.ec44c9e8.chunk.css" rel="stylesheet">
</head>
<body>
  <noscript>JavaScript required message</noscript>
  <div id="root"></div>
  <script src="/static/js/35.81a4449d.chunk.js"></script>
  <script src="/static/js/main.a9d91cf8.chunk.js"></script>
</body>
</html>
```

**Data Layout**: Vertical text format (no HTML tables)
```
BATTING
R    B    4    6    SR
M BOENDERMAKER       # Line 1: Player name
b A Sehgal           # Line 2: Dismissal
11                   # Line 3: Runs
24                   # Line 4: Balls
1                    # Line 5: Fours
0                    # Line 6: Sixes
45.83                # Line 7: Strike rate
```

#### CSS Classes (Dynamic, Hashed):
- `SmartTableStyle__TableRow-sc-19dsvr3-3 cLRPCK`
- `AppStyle__AppWrapper-k0uc59-0 gnFWxU`
- `BoxStyle__Container-xydo28-0 jVEznZ`

**Cannot use CSS selectors for scraping!**

---

### 2. Mock Server (Current Implementation)

#### Mode 1: RANDOM (Default)

**HTML Generated** (simple tables):
```html
<table border="1">
  <tr><th>Batsman</th><th>Runs</th><th>Balls</th><th>4s</th><th>6s</th><th>Dismissal</th></tr>
  <tr>
    <td>Jason Smith</td>
    <td>85</td>
    <td>67</td>
    <td>12</td>
    <td>3</td>
    <td>b Kumar</td>
  </tr>
</table>
```

**Differences from Real KNCB**:
| Feature | Real KNCB | Mock Random |
|---------|-----------|-------------|
| Structure | React SPA with vertical layout | Simple HTML tables |
| CSS Classes | Hashed, dynamic | None (inline styles) |
| JavaScript | Required, 3+ sec render | Not required, instant |
| Data Format | Vertical text (7 lines/player) | Horizontal table rows |
| Realism | Production | Toy example |

#### Mode 2: PRELOADED (136 Real 2025 Scorecards)

**Data Source**:
- Real KNCB HTML fetched from 2025 season
- Stored in `backend/mock_data/scorecards_2026/`
- 136 matches across 10 ACC teams
- Mapped to 2026 season dates (April 1 - Sept 30)

**HTML Served**: **Identical to real KNCB site**
- Same React structure
- Same hashed CSS classes
- Same vertical text layout
- Same JavaScript chunks
- Same noscript message

**This is PERFECT for testing!**

---

### 3. Scraper Compatibility

The scraper (`kncb_html_scraper.py`) works with BOTH modes:

#### Scraping Strategy:
1. **Wait for React**: `await asyncio.sleep(3)` - Let React render
2. **Extract text**: `await page.inner_text('body')` - Get all text content
3. **Parse vertically**: Extract 7 lines per player (name, dismissal, stats)
4. **No CSS selectors**: Uses text pattern matching only

#### Why This Works:
- ✅ Doesn't rely on CSS classes (they're hashed anyway)
- ✅ Parses text content directly (works for both HTML and React)
- ✅ Handles vertical layout (real KNCB format)
- ✅ Filters non-player names (dismissals, metadata, team names)

#### Current Status:
- **RANDOM mode**: Works, but generates unrealistic data
- **PRELOADED mode**: ✅ **Perfect realism**, serves actual KNCB HTML
- **Production**: Will work when 2026 season starts (same parsing logic)

---

## Issues Identified

### Issue 1: RANDOM Mode HTML Structure Mismatch

**Problem**: Mock server's random mode generates simple HTML tables, but real KNCB uses React with vertical text layout.

**Impact**:
- If scraper is tested with random mode, it won't match real KNCB structure
- Developer might be misled about what to expect

**Current Mitigation**:
- PRELOADED mode exists and solves this
- Documentation clearly states random mode is for quick testing only

### Issue 2: Mock Server URL Format

**Problem**: Mock server uses simplified URL format:
```
Mock:  http://localhost:5001/match/12345/scorecard/
Real:  https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194
```

**Impact**:
- URL parsing might not match production format exactly
- Query parameters (`?period=X`) not tested

**Current Mitigation**:
- Scraper code already handles both formats (see line 523-527):
```python
if '-' in match_path:
    parts = match_path.split('-')
    match_id_str = parts[-1]  # Last part is match ID
else:
    match_id_str = match_path
```

### Issue 3: React Rendering Simulation

**Problem**: Mock server serves static HTML instantly, but real KNCB requires 3+ seconds for JavaScript to render content.

**Impact**:
- Timing bugs might not be caught in testing
- No testing of "empty page" → "content loads" transition

**Current Mitigation**:
- Scraper already includes `await asyncio.sleep(3)` for React rendering
- Works correctly for both mock and production

### Issue 4: RANDOM Mode Generates Unrealistic Player Names

**Problem**: Random mode generates names like "Jason Smith", "Tom Patel" - not realistic Dutch cricket names.

**Impact**:
- Name matching logic not tested properly
- Dutch name patterns (van der, de Jong) not covered

**Current Status**: Non-critical (PRELOADED mode has real names)

### Issue 5: No Testing for Match Centre UI Elements

**Problem**: Real KNCB site has navigation, headers, match info, result text - mock random mode only has scorecard tables.

**Impact**:
- Text parsing might accidentally capture UI elements
- "Result:", "Venue:", "Toss:" etc. not tested

**Current Mitigation**:
- Scraper has extensive filtering logic (`_is_valid_player_name()` - 100+ lines)
- Filters team names, metadata, dismissals, dates, divisions

---

## Recommendations

### Priority 1: **Use PRELOADED Mode by Default** ✅

**Action**: Change mock server to default to PRELOADED mode when data exists.

**Rationale**:
- PRELOADED mode already provides 100% realistic KNCB HTML
- 136 real matches available covering all scenarios
- Better testing experience out of the box

**Implementation**:
```python
# In mock_kncb_server.py (line 43-44)
# CURRENT:
MOCK_DATA_DIR = os.environ.get('MOCK_DATA_DIR', None)
PRELOADED_MODE = MOCK_DATA_DIR is not None and os.path.exists(MOCK_DATA_DIR)

# IMPROVED:
MOCK_DATA_DIR = os.environ.get('MOCK_DATA_DIR', './mock_data/scorecards_2026')
PRELOADED_MODE = MOCK_DATA_DIR is not None and os.path.exists(MOCK_DATA_DIR)
```

**Result**: Developers get realistic KNCB HTML automatically.

---

### Priority 2: **Improve RANDOM Mode HTML Structure** ⚠️

**Action**: Make random mode generate React-style HTML with vertical layout.

**Rationale**:
- Currently random mode generates HTML tables (not realistic)
- Should match real KNCB structure for better testing
- Useful when preloaded data isn't available

**Implementation**: Generate HTML that looks like this:
```html
<!doctype html>
<html lang="en">
<head>
  <title>Mock KNCB Match Centre</title>
  <style>
    .scorecard { padding: 20px; font-family: 'Open Sans', sans-serif; }
    .batting-section { margin: 20px 0; }
    .player-stats { display: flex; flex-direction: column; margin: 10px 0; }
    .stat { padding: 2px 0; }
  </style>
</head>
<body>
  <div id="root">
    <div class="scorecard">
      <h1>ACC 1 vs VRA 1</h1>
      <p>Result: ACC 1 won by 5 wickets</p>

      <div class="batting-section">
        <h2>BATTING</h2>
        <div class="headers">
          <div>R</div>
          <div>B</div>
          <div>4</div>
          <div>6</div>
          <div>SR</div>
        </div>

        <div class="player-stats">
          <div class="stat">M BOENDERMAKER</div>
          <div class="stat">b A Sehgal</div>
          <div class="stat">11</div>
          <div class="stat">24</div>
          <div class="stat">1</div>
          <div class="stat">0</div>
          <div class="stat">45.83</div>
        </div>

        <!-- More players... -->
      </div>

      <div class="bowling-section">
        <h2>BOWLING</h2>
        <!-- Similar vertical structure -->
      </div>
    </div>
  </div>
</body>
</html>
```

**Changes Needed**:
1. Replace `generate_scorecard_html()` function (lines 569-630)
2. Use vertical layout instead of tables
3. Add metadata text (Result, Venue, etc.) to test filtering logic
4. Include section markers (BATTING, BOWLING, FIELDING)

**Estimated Effort**: 2-3 hours

---

### Priority 3: **Add React Rendering Delay to Mock** 💡

**Action**: Add optional delay before returning HTML to simulate React rendering time.

**Implementation**:
```python
@app.route('/match/<path:match_path>/scorecard/', methods=['GET'])
async def get_scorecard_html(match_path):
    """Simulate React rendering delay"""

    # Optional: Simulate React loading time
    if os.environ.get('SIMULATE_REACT_DELAY', 'false').lower() == 'true':
        await asyncio.sleep(2)  # Simulate 2-second React render

    # ... rest of the function
```

**Rationale**:
- Tests scraper's wait logic (`await asyncio.sleep(3)`)
- Ensures timing bugs are caught before production
- Optional: Only enabled when needed

**Estimated Effort**: 30 minutes

---

### Priority 4: **Add URL Format Validation** 🔍

**Action**: Make mock server enforce real KNCB URL format.

**Implementation**:
```python
@app.route('/match/<path:match_path>/scorecard/', methods=['GET'])
def get_scorecard_html(match_path):
    """Enforce proper URL format"""

    # Validate format: entity_id-match_id
    if '-' not in match_path:
        logger.warning(f"⚠️  URL format should be 'entity_id-match_id', got: {match_path}")
        # Still work for backwards compatibility

    # Extract match_id
    if '-' in match_path:
        entity_id, match_id_str = match_path.rsplit('-', 1)
        if entity_id != str(ENTITY_ID):
            logger.warning(f"⚠️  Entity ID mismatch: got {entity_id}, expected {ENTITY_ID}")
    else:
        match_id_str = match_path

    # ... rest of the function
```

**Rationale**:
- Catches URL format issues early
- Matches production URL structure exactly
- Helps with debugging

**Estimated Effort**: 1 hour

---

### Priority 5: **Improve Random Mode Player Names** 🎭

**Action**: Generate realistic Dutch/Indian cricket names.

**Implementation**:
```python
# Replace FIRST_NAMES and LAST_NAMES (lines 178-188) with:

DUTCH_FIRST_NAMES = [
    "Pieter", "Jan", "Willem", "Lars", "Bas", "Thijs", "Daan", "Tim",
    "Sander", "Ruben", "Max", "Bram", "Jesse", "Jasper", "Luuk"
]

DUTCH_LAST_NAMES = [
    "de Jong", "van Dijk", "Jansen", "Bakker", "Visser", "de Vries",
    "van den Berg", "Mulder", "Smit", "van Leeuwen", "van der Meer"
]

INDIAN_FIRST_NAMES = [
    "Arjun", "Vikram", "Rohan", "Amit", "Rahul", "Sanjay", "Ajay",
    "Aditya", "Kiran", "Nikhil", "Vivek", "Suresh", "Raj", "Ankit"
]

INDIAN_LAST_NAMES = [
    "Patel", "Kumar", "Singh", "Shah", "Sharma", "Gupta", "Reddy",
    "Nair", "Iyer", "Chopra", "Mehta", "Rao", "Shetty", "Desai"
]

def generate_player_name():
    """Generate realistic Dutch or Indian cricket player name"""
    # 60% Dutch, 40% Indian (reflects ACC demographics)
    if random.random() < 0.6:
        return f"{random.choice(DUTCH_FIRST_NAMES)} {random.choice(DUTCH_LAST_NAMES)}"
    else:
        return f"{random.choice(INDIAN_FIRST_NAMES)} {random.choice(INDIAN_LAST_NAMES)}"
```

**Rationale**:
- Tests name matching with real ACC player name patterns
- Covers Dutch multi-part names (van der, de, van den)
- Matches actual Amsterdam cricket demographics

**Estimated Effort**: 30 minutes

---

### Priority 6: **Add Mock API Endpoints** 🚀

**Action**: Add working API endpoints that mock server currently lacks.

**Current Status**:
- ✅ Grades: `/rv/{entity_id}/grades/` - Works
- ✅ Matches: `/rv/{entity_id}/matches/` - Works
- ✅ Scorecard JSON: `/rv/match/{match_id}/` - Works
- ✅ Scorecard HTML: `/match/{entity_id}-{match_id}/scorecard/` - Works

**Missing Endpoints** (from real KNCB API):
- `/rv/personseason/{person_id}/` - Player season stats
- `/rv/person/{person_id}/` - Player profile
- `/rv/{entity_id}/standings/` - League standings
- `/rv/{entity_id}/clubs/` - List of clubs

**Implementation**: Add these endpoints with mock data generation.

**Rationale**:
- Future-proof for potential API access
- Useful if KNCB unblocks player endpoints
- Better API testing coverage

**Estimated Effort**: 3-4 hours

---

### Priority 7: **Add Mock Server Documentation** 📚

**Action**: Create `MOCK_SERVER_GUIDE.md` explaining both modes.

**Contents**:
1. What is the mock server
2. How to run it (random vs preloaded mode)
3. URL formats and endpoints
4. How to add more test data
5. Troubleshooting guide

**Estimated Effort**: 1-2 hours

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Change default to PRELOADED mode
2. ✅ Add React rendering delay option
3. ✅ Improve player name generation

### Phase 2: Core Improvements (3-4 hours)
4. ⚠️ Rewrite random mode HTML structure to match real KNCB
5. 🔍 Add URL format validation

### Phase 3: Enhancement (4-5 hours)
6. 🚀 Add missing API endpoints
7. 📚 Write comprehensive documentation

---

## Testing Plan

After implementing improvements:

### Test 1: PRELOADED Mode
```bash
cd backend
export MOCK_DATA_DIR="./mock_data/scorecards_2026"
python3 mock_kncb_server.py
```

**Verify**:
- ✅ Server starts in PRELOADED mode
- ✅ `/health` shows 136 matches loaded
- ✅ Scorecard HTML matches real KNCB structure
- ✅ Scraper successfully extracts player stats

### Test 2: RANDOM Mode (Improved)
```bash
cd backend
export MOCK_DATA_DIR=""  # Disable preloaded
python3 mock_kncb_server.py
```

**Verify**:
- ✅ Server starts in RANDOM mode
- ✅ Generated HTML has vertical layout (not tables)
- ✅ Player names are realistic (Dutch/Indian)
- ✅ Scraper successfully parses vertical format

### Test 3: Scraper Integration
```bash
# Point scraper to mock server
export SCRAPER_MODE=mock
python3 kncb_html_scraper.py
```

**Verify**:
- ✅ Scraper connects to mock server
- ✅ Successfully scrapes multiple matches
- ✅ Player stats extracted correctly
- ✅ Fantasy points calculated properly

---

## Risk Assessment

### Low Risk ✅
- **Default to PRELOADED mode**: No breaking changes, improves UX
- **Player name improvements**: Cosmetic, doesn't affect functionality
- **Documentation**: Zero code risk

### Medium Risk ⚠️
- **Random mode HTML rewrite**: Requires testing but well-scoped
- **URL validation**: Could break backwards compatibility (add warnings only)
- **React delay simulation**: Could slow down tests if always enabled

### High Risk ❌
- **None identified**

---

## Success Metrics

After implementing improvements:

1. **Realism**: Mock server RANDOM mode matches real KNCB structure (vertical layout, React-style HTML)
2. **Coverage**: Scraper test suite covers all edge cases (Dutch names, metadata filtering, vertical parsing)
3. **Developer Experience**: New developers can test scraper immediately with realistic data
4. **Documentation**: Complete guide exists for both mock modes
5. **No Surprises**: Scraper works identically on mock and production

---

## Conclusion

**Current Status**: Mock server already has PRELOADED mode with 136 real KNCB scorecards - this is excellent!

**Main Gap**: RANDOM mode generates unrealistic HTML (tables instead of vertical React layout)

**Recommendation**:
1. **Immediate**: Switch default to PRELOADED mode (5 min change)
2. **Short-term**: Improve RANDOM mode HTML structure (3-4 hours)
3. **Long-term**: Add missing API endpoints and documentation (4-5 hours)

**Total Effort**: ~8-10 hours for full improvement plan

**Priority**: Medium urgency. Current setup works well, but improvements would help future development and onboarding.

---

## Next Steps

1. Review this plan and confirm priorities
2. Implement Phase 1 (quick wins) if approved
3. Test with scraper to verify improvements
4. Document changes in SCRAPER_USAGE_GUIDE.md
5. Update TESTING_COMPLETE_SUMMARY.md with new test scenarios

---

**Status**: ✅ Analysis complete, ready for your review and approval to proceed.
