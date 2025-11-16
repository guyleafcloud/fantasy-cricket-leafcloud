#!/usr/bin/env python3
"""
KNCB ResultsVault API Client - FIXED VERSION
============================================
Correct endpoints discovered from browser Network tab
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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://matchcentre.kncb.nl/',
            'Origin': 'https://matchcentre.kncb.nl'
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
        
        # Always add apiid
        params['apiid'] = self.api_id
        
        url = f"{self.base_url}/{endpoint}"
        
        logger.info(f"🔍 Requesting: {url}")
        logger.debug(f"📋 Params: {params}")
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 404:
                logger.error(f"❌ 404 Not Found: {url}")
                return None
            
            if response.status_code == 401:
                logger.error(f"❌ 401 Unauthorized - IP might be blocked: {url}")
                return None
            
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
        
        Uses: /rv/134453/grades/?apiid=1002&seasonId=19
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
                grade['tier'] = self._determine_tier(grade.get('grade_name', ''))
        
        return data if data else []
    
    def get_person_season(self, person_id: int) -> Optional[Dict]:
        """
        Get person information for a season
        
        CORRECT ENDPOINT: /rv/personseason/{person_id}/?apiid=1002
        
        This returns player info including:
        - Basic details (name, etc)
        - Season statistics
        - Performance data
        """
        logger.info(f"📥 Fetching person {person_id}")
        
        data = self._make_request(f"personseason/{person_id}/")
        
        if data:
            logger.info(f"✅ Retrieved person: {data.get('person_name', 'Unknown')}")
        else:
            logger.error(f"❌ Failed to fetch person {person_id}")
        
        return data
    
    def get_teams_in_grade(self, grade_id: int, season_id: int = None) -> List[Dict]:
        """Get all teams in a specific grade/competition"""
        if season_id is None:
            current_season = self.get_current_season()
            season_id = current_season['season_id'] if current_season else 19
        
        data = self._make_request(
            f"{self.kncb_entity_id}/grades/{grade_id}/",
            {'seasonId': season_id}
        )
        
        if data and 'teams' in data:
            return data['teams']
        return []
    
    def get_matches(self, grade_id: int, season_id: int = None, 
                    max_records: int = 1000) -> List[Dict]:
        """
        Get matches for a grade/competition
        """
        if season_id is None:
            current_season = self.get_current_season()
            season_id = current_season['season_id'] if current_season else 19
        
        data = self._make_request(
            f"{self.kncb_entity_id}/matches/",
            {
                'seasonId': season_id,
                'gradeId': grade_id,
                'action': 'ors',
                'maxrecs': max_records,
                'strmflg': 1
            }
        )
        
        return data if data else []
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Get detailed scorecard for a specific match"""
        return self._make_request(f"match/{match_id}/")
    
    def get_team_roster(self, team_id: int) -> List[Dict]:
        """Get all players in a team"""
        data = self._make_request(f"team/{team_id}/roster/")
        return data if data else []
    
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
                'grade_id': grade.get('grade_id'),
                'grade_name': grade.get('grade_name'),
                'tier': grade.get('tier'),
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
# TESTING
# =============================================================================

def test_api_client():
    """Test the KNCB API client with correct endpoints"""
    
    print("🏏 Testing KNCB ResultsVault API Client")
    print("=" * 70)
    
    client = KNCBAPIClient()
    
    # Test 1: Get entity info
    print("\n1️⃣ Getting KNCB entity info...")
    entity = client.get_entity_info()
    if entity:
        print(f"   ✅ Entity: {entity.get('entity_name', 'Unknown')}")
    else:
        print("   ❌ Failed to get entity info")
    
    # Test 2: Get grades/competitions
    print("\n2️⃣ Getting competitions for season 19...")
    grades = client.get_grades(season_id=19)
    if grades:
        print(f"   ✅ Found {len(grades)} competitions")
        # Show first few
        for grade in grades[:5]:
            print(f"      - {grade.get('grade_name')} ({grade.get('tier')})")
    else:
        print("   ❌ Failed to get grades")
    
    # Test 3: Get person data (Sean Walsh)
    print("\n3️⃣ Testing person endpoint with Sean Walsh (11190879)...")
    person = client.get_person_season(11190879)
    if person:
        print(f"   ✅ Retrieved person data!")
        print(f"   👤 Name: {person.get('person_name', 'Unknown')}")
        print(f"   🔑 Available keys: {list(person.keys())[:10]}")
        
        # Save for inspection
        with open('sean_walsh_data.json', 'w') as f:
            json.dump(person, f, indent=2)
        print(f"   💾 Full data saved to sean_walsh_data.json")
    else:
        print("   ❌ Failed to get person data")
        print("   🚫 This means the API is still blocked from your server IP")
        print("   💡 You MUST use the GitHub Bridge solution")
    
    print("\n" + "=" * 70)
    if person:
        print("✅ API Client Working!")
        print("\n📝 Next steps:")
        print("1. Update your backend to use get_person_season() method")
        print("2. Parse the person data structure")
        print("3. Set up scheduled fetching")
    else:
        print("❌ API Still Blocked - Use GitHub Bridge")
        print("\n📝 Next steps:")
        print("1. Set up fetch script on your laptop")
        print("2. Configure GitHub repo for data storage")
        print("3. Server reads from GitHub instead of API")


if __name__ == "__main__":
    test_api_client()