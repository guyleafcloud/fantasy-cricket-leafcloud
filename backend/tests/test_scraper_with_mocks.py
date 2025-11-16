#!/usr/bin/env python3
"""
Comprehensive Scraper Tests with Mocked Responses
==================================================
Tests the scraper logic without hitting the live matchcentre site.

Uses:
- Fixture files for API/HTML responses
- Mocked Playwright browser/page interactions
- Validates scorecard finding, parsing, and fantasy points calculation
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kncb_html_scraper import KNCBMatchCentreScraper


# =============================================================================
# FIXTURES
# =============================================================================

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory"""
    return FIXTURES_DIR


@pytest.fixture
def grades_response(fixtures_dir):
    """Load grades API response fixture"""
    with open(fixtures_dir / 'grades_response.json', 'r') as f:
        return json.load(f)


@pytest.fixture
def matches_response(fixtures_dir):
    """Load matches API response fixture"""
    with open(fixtures_dir / 'matches_response.json', 'r') as f:
        return json.load(f)


@pytest.fixture
def scorecard_api_response(fixtures_dir):
    """Load scorecard API response fixture"""
    with open(fixtures_dir / 'scorecard_api_response.json', 'r') as f:
        return json.load(f)


@pytest.fixture
def scorecard_html(fixtures_dir):
    """Load HTML scorecard fixture"""
    with open(fixtures_dir / 'scorecard_html.html', 'r') as f:
        return f.read()


@pytest.fixture
def scraper():
    """Create scraper instance"""
    return KNCBMatchCentreScraper()


# =============================================================================
# MOCK HELPERS
# =============================================================================

def create_mock_page(response_data, response_type='json', status=200):
    """
    Create a mocked Playwright page object

    Args:
        response_data: The data to return (dict for JSON, str for HTML)
        response_type: 'json' or 'html'
        status: HTTP status code
    """
    mock_page = AsyncMock()
    mock_response = MagicMock()
    mock_response.status = status

    # Mock goto
    mock_page.goto = AsyncMock(return_value=mock_response)

    # Mock evaluate for getting page content
    if response_type == 'json':
        mock_page.evaluate = AsyncMock(return_value=json.dumps(response_data))
    else:
        # For HTML parsing, return structured data
        mock_page.evaluate = AsyncMock(return_value=response_data)

    return mock_page


def create_mock_browser(mock_page):
    """Create a mocked browser with a page"""
    mock_browser = AsyncMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()
    return mock_browser


# =============================================================================
# TEST: Tier Detection
# =============================================================================

def test_tier_determination(scraper):
    """Test that grade names are correctly mapped to tiers"""

    test_cases = [
        ('Topklasse', 'tier1'),
        ('Hoofdklasse', 'tier1'),
        ('Eerste Klasse', 'tier2'),
        ('Tweede Klasse', 'tier2'),
        ('Derde Klasse', 'tier3'),
        ('Vierde Klasse', 'tier3'),
        ('ZaMi League', 'social'),
        ('ZoMi League', 'social'),
        ('U17 Competition', 'youth'),
        ('Vrouwen Topklasse', 'tier1'),  # topklasse takes precedence
        ('Vrouwen', 'ladies'),  # pure women's grade
        ('Unknown Grade', 'tier2'),  # default
    ]

    for grade_name, expected_tier in test_cases:
        result = scraper._determine_tier(grade_name)
        assert result == expected_tier, f"Failed for {grade_name}: expected {expected_tier}, got {result}"

    print("✅ Tier determination tests passed!")


# =============================================================================
# TEST: Fantasy Points Calculation
# =============================================================================

def test_fantasy_points_calculation(scraper):
    """Test fantasy points calculation with various scenarios (NEW RULES)"""

    # Test case 1: Century with good SR
    performance1 = {
        'tier': 'tier1',
        'batting': {'runs': 105, 'balls_faced': 80, 'fours': 10, 'sixes': 3},  # SR = 131.25
        'bowling': {},
        'fielding': {}
    }
    points1 = scraper._calculate_fantasy_points(performance1)
    # NEW RULES: 105 runs + 16 (century) + 5 (SR >= 100) = 126 * 1.2 (tier1) = 151
    # NO boundary bonuses!
    expected1 = int((105 + 16 + 5) * 1.2)
    assert points1 == expected1, f"Century test failed: expected {expected1}, got {points1}"

    # Test case 2: Fifty with SR bonus
    performance2 = {
        'tier': 'tier2',
        'batting': {'runs': 52, 'balls_faced': 45, 'fours': 6, 'sixes': 1},  # SR = 115.56
        'bowling': {},
        'fielding': {}
    }
    points2 = scraper._calculate_fantasy_points(performance2)
    # NEW RULES: 52 runs + 8 (fifty) + 5 (SR >= 100) = 65 * 1.0 (tier2) = 65
    expected2 = int((52 + 8 + 5) * 1.0)
    assert points2 == expected2, f"Fifty test failed: expected {expected2}, got {points2}"

    # Test case 3: Duck penalty
    performance3 = {
        'tier': 'tier2',
        'batting': {'runs': 0, 'balls_faced': 5, 'fours': 0, 'sixes': 0},  # SR = 0
        'bowling': {},
        'fielding': {}
    }
    points3 = scraper._calculate_fantasy_points(performance3)
    # 0 runs + (-2) duck penalty + (-5) SR penalty = -7 but capped at 0
    expected3 = 0
    assert points3 == expected3, f"Duck test failed: expected {expected3}, got {points3}"

    # Test case 4: Five wicket haul with maidens and economy
    performance4 = {
        'tier': 'tier1',
        'batting': {},
        'bowling': {'wickets': 5, 'runs_conceded': 28, 'overs': 10.0, 'maidens': 3},  # ER = 2.8
        'fielding': {}
    }
    points4 = scraper._calculate_fantasy_points(performance4)
    # NEW RULES: 60 (5 wickets) + 75 (3 maidens x 25) + 8 (5wh bonus) + 10 (ER < 4.0) = 153 * 1.2 = 183
    expected4 = int((60 + 75 + 8 + 10) * 1.2)
    assert points4 == expected4, f"Five-wicket haul test failed: expected {expected4}, got {points4}"

    # Test case 5: All-rounder with fielding
    performance5 = {
        'tier': 'tier2',
        'batting': {'runs': 35, 'balls_faced': 28, 'fours': 3, 'sixes': 1},  # SR = 125
        'bowling': {'wickets': 2, 'runs_conceded': 25, 'overs': 8.0, 'maidens': 1},  # ER = 3.125
        'fielding': {'catches': 2, 'stumpings': 0, 'runouts': 0}
    }
    points5 = scraper._calculate_fantasy_points(performance5)
    # NEW RULES:
    # Batting: 35 + 5 (SR >= 100) = 40
    # Bowling: 24 + 25 (1 maiden x 25) + 10 (ER < 4.0) = 59
    # Fielding: 8
    # Total: 107 * 1.0 = 107
    expected5 = int((35 + 5 + 24 + 25 + 10 + 8) * 1.0)
    assert points5 == expected5, f"All-rounder test failed: expected {expected5}, got {points5}"

    print("✅ Fantasy points calculation tests passed!")


# =============================================================================
# TEST: Getting Recent Matches (Mocked)
# =============================================================================

@pytest.mark.asyncio
async def test_get_recent_matches_for_club(scraper, grades_response, matches_response):
    """Test fetching recent matches with mocked API responses"""

    with patch.object(scraper, 'create_browser') as mock_create_browser:
        # Create one page that responds differently based on URL
        mock_page = AsyncMock()
        mock_response = MagicMock()
        mock_response.status = 200

        # Track URL calls
        urls_called = []

        async def goto_side_effect(url, **kwargs):
            urls_called.append(url)
            return mock_response

        async def evaluate_side_effect(script):
            # Return different responses based on what URL was last called
            if urls_called:
                last_url = urls_called[-1]
                if '/grades/' in last_url:
                    return json.dumps(grades_response)
                elif '/matches/' in last_url:
                    return json.dumps(matches_response)
            return '{}'

        mock_page.goto = AsyncMock(side_effect=goto_side_effect)
        mock_page.evaluate = AsyncMock(side_effect=evaluate_side_effect)

        # Mock browser
        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        mock_create_browser.return_value = mock_browser

        # Test
        matches = await scraper.get_recent_matches_for_club('ACC', days_back=30)

        # Assertions
        # Note: Will find multiple matches since mock returns same data for all grades
        assert len(matches) >= 2, f"Expected at least 2 ACC matches, got {len(matches)}"

        # Check first match details
        match1 = matches[0]
        assert match1['match_id'] == 7254567
        assert 'ACC Amsterdam' in match1['home_club_name']
        assert match1['tier'] in ['tier1', 'tier2', 'tier3']
        assert 'grade_name' in match1

        print(f"✅ Found {len(matches)} matches for ACC")
        print(f"   Match 1: {match1['home_club_name']} vs {match1['away_club_name']}")
        print("✅ Get recent matches test passed!")


# =============================================================================
# TEST: Scraping Match Scorecard (API)
# =============================================================================

@pytest.mark.asyncio
async def test_scrape_match_scorecard_api(scraper, scorecard_api_response):
    """Test scraping scorecard using mocked API response"""

    with patch.object(scraper, 'create_browser') as mock_create_browser:
        # Create mock page that returns scorecard JSON
        mock_page = create_mock_page(scorecard_api_response, 'json', status=200)
        mock_browser = create_mock_browser(mock_page)
        mock_create_browser.return_value = mock_browser

        # Test
        scorecard = await scraper.scrape_match_scorecard(7254567)

        # Assertions
        assert scorecard is not None, "Scorecard should not be None"
        assert 'innings' in scorecard, "Scorecard should have innings"
        assert len(scorecard['innings']) == 2, "Should have 2 innings"

        # Check first innings
        innings1 = scorecard['innings'][0]
        assert 'batting' in innings1
        assert 'bowling' in innings1
        assert len(innings1['batting']) > 0, "Should have batting data"
        assert len(innings1['bowling']) > 0, "Should have bowling data"

        # Check a specific batter
        first_batter = innings1['batting'][0]
        assert first_batter['person_name'] == 'John Smith'
        assert first_batter['runs'] == 85
        assert first_batter['fours'] == 8
        assert first_batter['sixes'] == 3

        print("✅ Scorecard API scraping test passed!")
        print(f"   Found {len(innings1['batting'])} batters in innings 1")
        print(f"   Found {len(innings1['bowling'])} bowlers in innings 1")


# =============================================================================
# TEST: Extracting Player Stats
# =============================================================================

def test_extract_player_stats(scraper, scorecard_api_response):
    """Test extracting individual player stats from scorecard"""

    players = scraper.extract_player_stats(
        scorecard_api_response,
        club_name='ACC Amsterdam',
        tier='tier1'
    )

    # Should extract all unique players from both innings
    assert len(players) > 0, "Should extract player stats"

    # Find John Smith (batter and fielder)
    john_smith = next((p for p in players if p['player_name'] == 'John Smith'), None)
    assert john_smith is not None, "Should find John Smith"
    assert john_smith['batting']['runs'] == 85
    assert john_smith['batting']['fours'] == 8
    assert john_smith['batting']['sixes'] == 3
    assert john_smith['fielding']['catches'] == 3
    assert john_smith['fantasy_points'] > 0, "Should have fantasy points"

    # Find Mike Wilson (batter and bowler)
    mike_wilson = next((p for p in players if p['player_name'] == 'Mike Wilson'), None)
    assert mike_wilson is not None, "Should find Mike Wilson"
    assert mike_wilson['batting']['runs'] == 34
    assert mike_wilson['bowling']['wickets'] == 4
    assert mike_wilson['bowling']['maidens'] == 3
    assert mike_wilson['fantasy_points'] > 0

    # Find Chris Taylor (duck + bowling)
    chris_taylor = next((p for p in players if p['player_name'] == 'Chris Taylor'), None)
    assert chris_taylor is not None, "Should find Chris Taylor"
    assert chris_taylor['batting']['runs'] == 0
    assert chris_taylor['batting']['balls_faced'] == 2
    assert chris_taylor['bowling']['wickets'] == 2

    print(f"✅ Player extraction test passed!")
    print(f"   Extracted {len(players)} players")
    print(f"   John Smith: {john_smith['fantasy_points']} points")
    print(f"   Mike Wilson: {mike_wilson['fantasy_points']} points")


# =============================================================================
# TEST: HTML Fallback Parsing
# =============================================================================

@pytest.mark.asyncio
async def test_scrape_scorecard_html_fallback(scraper, scorecard_html):
    """Test HTML fallback when API fails"""

    with patch.object(scraper, 'create_browser') as mock_create_browser:
        # First call returns 404, triggering HTML fallback
        mock_page = AsyncMock()
        mock_response = MagicMock()
        mock_response.status = 404
        mock_page.goto = AsyncMock(return_value=mock_response)

        # Mock HTML evaluation to return parsed structure
        # (In real scenario, this would parse the actual HTML)
        html_parsed_data = {
            'innings': [
                {
                    'batting': [
                        {'player_name': 'John Smith', 'dismissal': 'c Jones b Williams', 'runs': 85}
                    ],
                    'bowling': [
                        {'player_name': 'Peter Williams', 'figures': '3/42'}
                    ]
                }
            ]
        }
        mock_page.evaluate = AsyncMock(return_value=html_parsed_data)

        mock_browser = create_mock_browser(mock_page)
        mock_create_browser.return_value = mock_browser

        # Test
        scorecard = await scraper.scrape_match_scorecard(7254567)

        # Assertions
        assert scorecard is not None
        assert 'innings' in scorecard
        assert len(scorecard['innings']) > 0

        print("✅ HTML fallback test passed!")


# =============================================================================
# TEST: Full Integration Flow (Mocked)
# =============================================================================

@pytest.mark.asyncio
async def test_full_scrape_flow(scraper, grades_response, matches_response, scorecard_api_response):
    """Test the full scraping workflow with all mocks"""

    # This test is complex because it involves multiple browser instances
    # For weekly update: one browser for getting matches, one per match for scorecards

    call_sequence = []

    async def create_browser_side_effect():
        """Mock browser factory that returns appropriate mocks based on call sequence"""
        call_num = len(call_sequence)
        call_sequence.append(call_num)

        mock_page = AsyncMock()
        mock_response = MagicMock()
        mock_response.status = 200

        urls_called = []

        async def goto_side_effect(url, **kwargs):
            urls_called.append(url)
            return mock_response

        async def evaluate_side_effect(script):
            if urls_called:
                last_url = urls_called[-1]
                # First browser call: getting matches
                if call_num == 0:
                    if '/grades/' in last_url:
                        return json.dumps(grades_response)
                    elif '/matches/' in last_url:
                        return json.dumps(matches_response)
                # Subsequent calls: getting scorecards
                else:
                    if '/match/' in last_url:
                        return json.dumps(scorecard_api_response)
            return '{}'

        mock_page.goto = AsyncMock(side_effect=goto_side_effect)
        mock_page.evaluate = AsyncMock(side_effect=evaluate_side_effect)

        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()

        return mock_browser

    with patch.object(scraper, 'create_browser', side_effect=create_browser_side_effect):
        # Test
        result = await scraper.scrape_weekly_update(clubs=['ACC'], days_back=30)

        # Assertions
        assert 'performances' in result
        assert 'total_performances' in result
        assert result['clubs'] == ['ACC']
        assert result['days_back'] == 30

        performances = result['performances']
        assert len(performances) > 0, "Should have player performances"

        # Check a performance has all required fields
        perf = performances[0]
        assert 'player_name' in perf
        assert 'match_id' in perf
        assert 'tier' in perf
        assert 'fantasy_points' in perf
        assert 'batting' in perf or 'bowling' in perf or 'fielding' in perf

        print("✅ Full integration test passed!")
        print(f"   Total performances: {result['total_performances']}")
        print(f"   Sample player: {perf['player_name']} - {perf['fantasy_points']} points")


# =============================================================================
# TEST: Edge Cases
# =============================================================================

def test_empty_scorecard(scraper):
    """Test handling of empty scorecard"""
    players = scraper.extract_player_stats({}, 'ACC', 'tier2')
    assert len(players) == 0, "Empty scorecard should return no players"
    print("✅ Empty scorecard test passed!")


def test_scorecard_without_innings(scraper):
    """Test handling of scorecard without innings"""
    players = scraper.extract_player_stats({'match_id': 123}, 'ACC', 'tier2')
    assert len(players) == 0, "Scorecard without innings should return no players"
    print("✅ No innings test passed!")


def test_player_with_no_stats(scraper):
    """Test fantasy points for player with no stats"""
    performance = {
        'tier': 'tier2',
        'batting': {},
        'bowling': {},
        'fielding': {}
    }
    points = scraper._calculate_fantasy_points(performance)
    assert points == 0, "Player with no stats should have 0 points"
    print("✅ No stats test passed!")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🏏 RUNNING SCRAPER TESTS (MOCKED)")
    print("=" * 80)
    print()

    # Run with pytest
    pytest.main([__file__, '-v', '-s'])
