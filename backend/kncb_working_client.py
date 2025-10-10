#!/usr/bin/env python3
"""
KNCB ResultsVault API Client - Working Version
==============================================
Uses only publicly accessible endpoints
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KNCBClient:
    """Working KNCB API client using public endpoints"""
    
    def __init__(self, entity_id: str = "134453"):
        self.base_url = "https://api.resultsvault.co.uk/rv"
        self.api_id = "1002"
        self.entity_id = entity_id  # KNCB/ACC entity
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
    
    def get_entity_info(self) -> Optional[Dict]:
        """Get KNCB/Club entity information"""
        url = f"{self.base_url}/{self.entity_id}/"
        params = {'apiid': self.api_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get entity info: {e}")
            return None
    
    def get_seasons(self) -> List[Dict]:
        """Get available seasons"""
        url = f"{self.base_url}/{self.entity_id}/seasons/"
        params = {'apiid': self.api_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get seasons: {e}")
            return []
    
    def get_grades(self, season_id: int) -> List[Dict]:
        """Get all competitions/grades for a season"""
        url = f"{self.base_url}/{self.entity_id}/grades/"
        params = {
            'apiid': self.api_id,
            'seasonId': season_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            grades = response.json()
            
            # Add tier info
            for grade in grades:
                grade['tier'] = self._determine_tier(grade['grade_name'])
            
            return grades
        except Exception as e:
            logger.error(f"Failed to get grades: {e}")
            return []
    
    def get_grade_details(self, grade_id: int, season_id: int) -> Optional[Dict]:
        """Get detailed info for a grade including teams"""
        url = f"{self.base_url}/{self.entity_id}/grades/{grade_id}/"
        params = {
            'apiid': self.api_id,
            'seasonid': season_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get grade details: {e}")
            return None
    
    def get_matches(self, grade_id: int, season_id: int, max_records: int = 100) -> List[Dict]:
        """Get matches for a competition"""
        url = f"{self.base_url}/{self.entity_id}/matches/"
        params = {
            'apiid': self.api_id,
            'seasonid': season_id,
            'gradeid': grade_id,
            'action': 'ors',
            'maxrecs': max_records,
            'strmflg': 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get matches: {e}")
            return []
    
    def get_match_scorecard(self, match_id: int) -> Optional[Dict]:
        """Get detailed scorecard for a match"""
        url = f"{self.base_url}/match/{match_id}/"
        params = {'apiid': self.api_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get match scorecard: {e}")
            return None
    
    def _determine_tier(self, grade_name: str) -> str:
        """Determine competition tier from grade name"""
        if not grade_name:
            return 'tier3'
        
        name_lower = grade_name.lower()
        
        if 'topklasse' in name_lower:
            return 'tier1'
        elif 'hoofdklasse' in name_lower:
            return 'tier1'
        elif 'eerste' in name_lower:
            return 'tier2'
        elif 'tweede' in name_lower:
            return 'tier2'
        elif 'derde' in name_lower:
            return 'tier3'
        elif 'vierde' in name_lower:
            return 'tier3'
        elif 'zami' in name_lower or 'zomi' in name_lower:
            return 'social'
        elif any(x in name_lower for x in ['u17', 'u15', 'u13', 'u11', 'jeugd']):
            return 'youth'
        elif 'vrouwen' in name_lower or 'dames' in name_lower:
            return 'ladies'
        else:
            return 'tier3'
    
    def get_all_data(self, season_id: int = 19) -> Dict:
        """
        Get complete data structure for import
        
        Returns:
        - Entity info
        - All grades
        - All teams per grade
        - Sample matches
        """
        
        logger.info(f"Fetching all data for season {season_id}...")
        
        result = {
            'entity': self.get_entity_info(),
            'season_id': season_id,
            'grades': []
        }
        
        # Get all grades
        grades = self.get_grades(season_id)
        logger.info(f"Found {len(grades)} grades")
        
        for grade in grades:
            grade_data = {
                'grade_id': grade['grade_id'],
                'grade_name': grade['grade_name'],
                'grade_short_name': grade['grade_short_name'],
                'tier': grade['tier'],
                'teams': [],
                'sample_matches': []
            }
            
            # Get grade details (includes teams)
            details = self.get_grade_details(grade['grade_id'], season_id)
            if details and 'teams' in details:
                grade_data['teams'] = details['teams']
                logger.info(f"  {grade['grade_name']}: {len(details['teams'])} teams")
            
            # Get sample matches (first 5)
            matches = self.get_matches(grade['grade_id'], season_id, max_records=5)
            grade_data['sample_matches'] = matches
            
            result['grades'].append(grade_data)
        
        return result


def test_client():
    """Test the KNCB client"""
    
    print("🏏 Testing KNCB API Client")
    print("=" * 70)
    
    # Test with ACC entity (134454) or KNCB main (134453)
    client = KNCBClient(entity_id="134453")
    
    # Test 1: Entity info
    print("\n1️⃣ Getting entity info...")
    entity = client.get_entity_info()
    if entity:
        print(f"   ✅ Entity: {entity['entity_name']}")
        print(f"   📍 Location: {entity.get('location', 'N/A')}")
        print(f"   📅 Current Season: {entity.get('current_season_name', 'N/A')}")
    else:
        print("   ❌ Failed")
        return
    
    # Test 2: Seasons
    print("\n2️⃣ Getting seasons...")
    seasons = client.get_seasons()
    if seasons:
        print(f"   ✅ Found {len(seasons)} seasons:")
        for season in seasons[:3]:
            print(f"      - {season['season_text']} (ID: {season['season_id']})")
    else:
        print("   ❌ Failed")
    
    # Test 3: Grades
    print("\n3️⃣ Getting grades for 2025...")
    grades = client.get_grades(season_id=19)
    if grades:
        print(f"   ✅ Found {len(grades)} competitions")
        
        # Show main ones
        main_grades = [g for g in grades if g['tier'] in ['tier1', 'tier2', 'social']][:8]
        for grade in main_grades:
            print(f"      - {grade['grade_name']} ({grade['tier']})")
    else:
        print("   ❌ Failed")
    
    # Test 4: Grade details (Topklasse)
    print("\n4️⃣ Getting Topklasse details...")
    topklasse = next((g for g in grades if 'topklasse' in g['grade_name'].lower()), None)
    if topklasse:
        details = client.get_grade_details(topklasse['grade_id'], 19)
        if details and 'teams' in details:
            teams = details['teams']
            print(f"   ✅ Found {len(teams)} teams:")
            for team in teams[:5]:
                print(f"      - {team.get('team_name', 'Unknown')}")
        else:
            print("   ⚠️  No teams found")
    
    # Test 5: Matches
    print("\n5️⃣ Getting recent Topklasse matches...")
    if topklasse:
        matches = client.get_matches(topklasse['grade_id'], 19, max_records=5)
        if matches:
            print(f"   ✅ Found {len(matches)} matches")
            for match in matches[:3]:
                print(f"      - Match {match.get('match_id', 'N/A')}")
        else:
            print("   ⚠️  No matches found")
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print("\n📝 Next steps:")
    print("1. Use get_all_data() to import full season")
    print("2. Store in database")
    print("3. Set up weekly updates")


def import_full_season(season_id: int = 19, output_file: str = "kncb_season_data.json"):
    """Import complete season data and save to file"""
    
    client = KNCBClient(entity_id="134453")
    
    print(f"📥 Importing full season {season_id}...")
    print("This may take a few minutes...")
    print("=" * 70)
    
    data = client.get_all_data(season_id)
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Data saved to {output_file}")
    
    # Print summary
    total_teams = sum(len(g['teams']) for g in data['grades'])
    total_matches = sum(len(g['sample_matches']) for g in data['grades'])
    
    print(f"\n📊 Summary:")
    print(f"   Entity: {data['entity']['entity_name']}")
    print(f"   Season: {season_id}")
    print(f"   Competitions: {len(data['grades'])}")
    print(f"   Total Teams: {total_teams}")
    print(f"   Sample Matches: {total_matches}")
    
    # Show grade breakdown
    print(f"\n📋 Grade Breakdown:")
    for grade in data['grades'][:10]:
        print(f"   - {grade['grade_name']}: {len(grade['teams'])} teams ({grade['tier']})")
    
    return data


if __name__ == "__main__":
    # Run basic test
    test_client()
    
    # Uncomment to import full season
    import_full_season(season_id=19)
