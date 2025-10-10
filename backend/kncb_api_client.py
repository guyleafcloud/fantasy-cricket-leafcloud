#!/usr/bin/env python3
"""
KNCB ResultsVault API Client
============================
Official API client for fetching Dutch cricket data from ResultsVault

Much better than web scraping - returns clean JSON data!
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KNCBAPIClient:
    """Client for KNCB ResultsVault API"""
    
    def __init__(self):
        self.base_url = "https://api.resultsvault.co.uk/rv"
        self.api_id = "1002"
        self.kncb_entity_id = "134453"  # KNCB main entity
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Fantasy Cricket Platform',
            'Accept': 'application/json'
        })
        
        # Competition tier mappings from grade names
        self.tier_mappings = {
            'topklasse': 'tier1',
            'hoofdklasse': 'tier1',
            'eerste klasse': 'tier2',
            'tweede klasse': 'tier2',
            'derde klasse': 'tier3',
            'vierde klasse': 'tier3',
            'zami': 'social',
            'zomi': 'social',
            'u17': 'youth',
            'u15': 'youth',
            'u13': 'youth',
            'u11': 'youth',
            'vrouwen': 'ladies',
            'women': 'ladies'
        }
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling"""
        
        if params is None:
            params = {}
        
        params['apiid'] = self.api_id
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed: {e}")
            return None
    
    def get_entity_info(self) -> Optional[Dict]:
        """Get KNCB entity information"""
        return self._make_request(f"{self.kncb_entity_id}/")
    
    def get_seasons(self) -> List[Dict]:
        """Get all available seasons"""
        data = self._make_request(f"{self.kncb_entity_id}/seasons/")
        return data if data else []
    
    def get_current_season(self) -> Optional[Dict]:
        """Get current season ID"""
        seasons = self.get_seasons()
        if seasons:
            # Assuming first is current
            return seasons[0]
        return None
    
    def get_grades(self, season_id: int = None) -> List[Dict]:
        """
        Get all competitions/grades for a season
        
        Returns leagues like:
        - Topklasse (tier1)
        - Hoofdklasse (tier1)
        - Eerste Klasse (tier2)
        - Zami (social)
        - U17, U15 (youth)
        - Vrouwen (ladies)
        """
        if season_id is None:
            current_season = self.get_current_season()
            season_id = current_season['season_id'] if current_season else 19
        
        data = self._make_request(
            f"{self.kncb_entity_id}/grades/",
            {'seasonId': season_id}
        )
        
        # Add tier information
        if data:
            for grade in data:
                grade['tier'] = self._determine_tier(grade['grade_name'])
        
        return data if data else []
    
    def get_teams_in_grade(self, grade_id: int, season_id: int = None) -> List[Dict]:
        """Get all teams in a specific grade/competition"""
        if season_id is None:
            current_season = self.get_current_season()
            season_id = current_season['season_id'] if current_season else 19
        
        data = self._make_request(
            f"{self.kncb_entity_id}/grades/{grade_id}/",
            {'seasonid': season_id}
        )
        
        if data and 'teams' in data:
            return data['teams']
        return []
    
    def get_matches(self, grade_id: int, season_id: int = None, 
                    max_records: int = 1000) -> List[Dict]:
        """
        Get matches for a grade/competition
        
        Args:
            grade_id: Competition ID (e.g., 71374 for Topklasse)
            season_id: Season ID (default: current season)
            max_records: Maximum matches to return
        """
        if season_id is None:
            current_season = self.get_current_season()
            season_id = current_season['season_id'] if current_season else 19
        
        data = self._make_request(
            f"{self.kncb_entity_id}/matches/",
            {
                'seasonid': season_id,
                'gradeid': grade_id,
                'action': 'ors',
                'maxrecs': max_records,
                'strmflg': 1
            }
        )
        
        return data if data else []
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Get detailed scorecard for a specific match"""
        return self._make_request(f"match/{match_id}/")
    
    def get_player_stats(self, player_id: int, season_id: int = None) -> Optional[Dict]:
        """Get statistics for a specific player"""
        if season_id is None:
            current_season = self.get_current_season()
            season_id = current_season['season_id'] if current_season else 19
        
        return self._make_request(
            f"player/{player_id}/",
            {'seasonid': season_id}
        )
    
    def get_team_roster(self, team_id: int) -> List[Dict]:
        """Get all players in a team"""
        data = self._make_request(f"team/{team_id}/roster/")
        return data if data else []
    
    def search_clubs(self, search_term: str) -> List[Dict]:
        """Search for clubs in KNCB"""
        # This might need different endpoint structure
        # For now, we know ACC is entity 134453
        logger.warning("Club search not yet implemented - use known entity IDs")
        return []
    
    def _determine_tier(self, grade_name: str) -> str:
        """Determine competition tier from grade name"""
        name_lower = grade_name.lower()
        
        for keyword, tier in self.tier_mappings.items():
            if keyword in name_lower:
                return tier
        
        # Default to tier3 for unknown
        return 'tier3'
    
    def get_all_grades_with_teams(self, season_id: int = None) -> Dict:
        """
        Get complete structure: all grades with their teams
        Useful for initial data import
        """
        grades = self.get_grades(season_id)
        
        result = {
            'season_id': season_id,
            'grades': []
        }
        
        for grade in grades:
            grade_data = {
                'grade_id': grade['grade_id'],
                'grade_name': grade['grade_name'],
                'tier': grade['tier'],
                'teams': []
            }
            
            # Get teams for this grade
            teams = self.get_teams_in_grade(grade['grade_id'], season_id)
            grade_data['teams'] = teams
            
            result['grades'].append(grade_data)
            
            logger.info(f"Loaded {len(teams)} teams from {grade['grade_name']}")
        
        return result
    
    def calculate_fantasy_points(self, player_performance: Dict) -> int:
        """
        Calculate fantasy points from player performance data
        
        Points system:
        - Batting: 1 per run, 1 per 4, 2 per 6, 8 for 50, 16 for 100
        - Bowling: 12 per wicket, 4 per maiden, 8 for 5-wicket haul
        - Fielding: 4 per catch, 6 per stumping/runout
        """
        points = 0
        
        # Batting
        if 'batting' in player_performance:
            bat = player_performance['batting']
            runs = bat.get('runs', 0)
            points += runs  # 1 per run
            points += bat.get('fours', 0)  # 1 per four
            points += bat.get('sixes', 0) * 2  # 2 per six
            
            # Milestones
            if runs >= 100:
                points += 16
            elif runs >= 50:
                points += 8
            elif runs == 0 and bat.get('balls_faced', 0) > 0:
                points -= 2  # Duck penalty
        
        # Bowling
        if 'bowling' in player_performance:
            bowl = player_performance['bowling']
            wickets = bowl.get('wickets', 0)
            points += wickets * 12
            points += bowl.get('maidens', 0) * 4
            
            if wickets >= 5:
                points += 8
        
        # Fielding
        if 'fielding' in player_performance:
            field = player_performance['fielding']
            points += field.get('catches', 0) * 4
            points += field.get('stumpings', 0) * 6
            points += field.get('runouts', 0) * 6
        
        return max(0, points)


# =============================================================================
# TESTING AND USAGE EXAMPLES
# =============================================================================

def test_api_client():
    """Test the KNCB API client"""
    
    print("🏏 Testing KNCB ResultsVault API Client")
    print("=" * 70)
    
    client = KNCBAPIClient()
    
    # Test 1: Get entity info
    print("\n1️⃣ Getting KNCB entity info...")
    entity = client.get_entity_info()
    if entity:
        print(f"   ✅ Entity: {entity['entity_name']}")
        print(f"   📍 Location: {entity['location']}")
        print(f"   📅 Current Season: {entity['current_season_name']}")
    else:
        print("   ❌ Failed to get entity info")
        return
    
    # Test 2: Get seasons
    print("\n2️⃣ Getting available seasons...")
    seasons = client.get_seasons()
    print(f"   ✅ Found {len(seasons)} seasons:")
    for season in seasons[:3]:
        print(f"      - {season['season_text']} (ID: {season['season_id']})")
    
    # Test 3: Get grades/competitions
    print("\n3️⃣ Getting competitions for 2025...")
    grades = client.get_grades(season_id=19)
    print(f"   ✅ Found {len(grades)} competitions")
    
    # Show main competitions
    main_comps = [g for g in grades if g['tier'] in ['tier1', 'tier2', 'social']]
    print(f"   📋 Main competitions:")
    for grade in main_comps[:10]:
        print(f"      - {grade['grade_name']} ({grade['tier']}) - ID: {grade['grade_id']}")
    
    # Test 4: Get teams from Topklasse
    print("\n4️⃣ Getting teams from Topklasse...")
    topklasse_grade = next((g for g in grades if 'topklasse' in g['grade_name'].lower()), None)
    
    if topklasse_grade:
        teams = client.get_teams_in_grade(topklasse_grade['grade_id'])
        print(f"   ✅ Found {len(teams)} teams in Topklasse:")
        for team in teams[:5]:
            print(f"      - {team.get('team_name', 'Unknown')}")
    
    # Test 5: Get recent matches
    print("\n5️⃣ Getting recent Topklasse matches...")
    if topklasse_grade:
        matches = client.get_matches(topklasse_grade['grade_id'], max_records=10)
        if matches:
            print(f"   ✅ Found {len(matches)} recent matches")
            for match in matches[:3]:
                print(f"      - Match {match.get('match_id', 'N/A')}: {match.get('home_team', 'Team')} vs {match.get('away_team', 'Team')}")
        else:
            print("   ⚠️  No matches found (might need different parameters)")
    
    print("\n" + "=" * 70)
    print("✅ API Client Test Complete!")
    print("\n📝 Next Steps:")
    print("1. Integrate this client into your backend")
    print("2. Create database models to store this data")
    print("3. Set up scheduled tasks to fetch data weekly")
    print("4. Use the data for fantasy points calculation")


def import_all_data_for_season(season_id: int = 19):
    """
    Import all data for a season
    This would be your initial data load
    """
    
    client = KNCBAPIClient()
    
    print(f"📥 Importing all data for season {season_id}...")
    print("=" * 70)
    
    # Get all grades with teams
    data = client.get_all_grades_with_teams(season_id)
    
    # Save to JSON file
    filename = f"kncb_data_season_{season_id}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Data saved to {filename}")
    
    # Print summary
    total_teams = sum(len(g['teams']) for g in data['grades'])
    print(f"\n📊 Summary:")
    print(f"   - Competitions: {len(data['grades'])}")
    print(f"   - Total Teams: {total_teams}")
    
    return data


if __name__ == "__main__":
    # Run tests
    test_api_client()
    
    # Uncomment to import all data
    # import_all_data_for_season(19)
