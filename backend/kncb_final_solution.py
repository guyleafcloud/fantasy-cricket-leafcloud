#!/usr/bin/env python3
"""
KNCB Fantasy Cricket - Complete Data Import Solution
===================================================
Works with publicly accessible ResultsVault endpoints
Stores data for fantasy cricket platform
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KNCBFantasyImporter:
    """Import KNCB data for fantasy cricket"""
    
    def __init__(self, entity_id: str = "134453"):
        self.base_url = "https://api.resultsvault.co.uk/rv"
        self.api_id = "1002"
        self.entity_id = entity_id
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        })
        
        # Fantasy scoring
        self.tier_multipliers = {
            'tier1': 1.2,
            'tier2': 1.0,
            'tier3': 0.8,
            'social': 0.4,
            'youth': 0.6,
            'ladies': 0.9
        }
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request"""
        if params is None:
            params = {}
        params['apiid'] = self.api_id
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.warning(f"Endpoint requires auth: {endpoint}")
            else:
                logger.error(f"HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def get_entity_info(self) -> Optional[Dict]:
        """Get KNCB entity info"""
        return self._make_request(f"{self.entity_id}/")
    
    def get_seasons(self) -> List[Dict]:
        """Get available seasons"""
        data = self._make_request(f"{self.entity_id}/seasons/")
        return data if data else []
    
    def get_grades(self, season_id: int) -> List[Dict]:
        """Get all competitions"""
        data = self._make_request(
            f"{self.entity_id}/grades/",
            {'seasonId': season_id}
        )
        
        if data:
            for grade in data:
                grade['tier'] = self._determine_tier(grade['grade_name'])
        
        return data if data else []
    
    def get_grade_details(self, grade_id: int, season_id: int) -> Optional[Dict]:
        """Get grade details including teams"""
        return self._make_request(
            f"{self.entity_id}/grades/{grade_id}/",
            {'seasonid': season_id}
        )
    
    def _determine_tier(self, grade_name: str) -> str:
        """Determine tier from grade name"""
        if not grade_name:
            return 'tier3'
        
        name_lower = grade_name.lower()
        
        if 'topklasse' in name_lower or 'hoofdklasse' in name_lower:
            return 'tier1'
        elif 'eerste' in name_lower or 'tweede' in name_lower:
            return 'tier2'
        elif 'derde' in name_lower or 'vierde' in name_lower:
            return 'tier3'
        elif 'zami' in name_lower or 'zomi' in name_lower:
            return 'social'
        elif any(x in name_lower for x in ['u17', 'u15', 'u13', 'u11', 'jeugd']):
            return 'youth'
        elif 'vrouwen' in name_lower or 'dames' in name_lower:
            return 'ladies'
        else:
            return 'tier3'
    
    def import_league_structure(self, season_id: int = 19) -> Dict:
        """
        Import complete league structure for fantasy setup
        
        Returns data ready for database import:
        - Competitions (grades)
        - Teams
        - Initial player list (from team rosters)
        """
        
        logger.info(f"Importing league structure for season {season_id}...")
        
        result = {
            'entity': self.get_entity_info(),
            'season_id': season_id,
            'import_date': datetime.now().isoformat(),
            'competitions': []
        }
        
        # Get all grades
        grades = self.get_grades(season_id)
        logger.info(f"Found {len(grades)} competitions")
        
        # Filter to main playing competitions
        main_grades = [
            g for g in grades 
            if g['tier'] in ['tier1', 'tier2', 'tier3', 'social', 'youth', 'ladies']
            and 'twenty20' not in g['grade_name'].lower()  # Skip T20 for now
            and 'friendly' not in g['grade_name'].lower()
        ]
        
        logger.info(f"Processing {len(main_grades)} main competitions...")
        
        total_teams = 0
        
        for grade in main_grades:
            comp_data = {
                'grade_id': grade['grade_id'],
                'name': grade['grade_name'],
                'short_name': grade['grade_short_name'],
                'tier': grade['tier'],
                'multiplier': self.tier_multipliers[grade['tier']],
                'teams': []
            }
            
            # Get teams
            details = self.get_grade_details(grade['grade_id'], season_id)
            if details and 'teams' in details:
                teams = details['teams']
                
                for team in teams:
                    team_data = {
                        'team_id': team.get('team_id'),
                        'team_name': team.get('team_name'),
                        'club_name': team.get('club_name'),
                        'grade': grade['grade_name'],
                        'tier': grade['tier']
                    }
                    comp_data['teams'].append(team_data)
                
                total_teams += len(teams)
                logger.info(f"  {grade['grade_name']}: {len(teams)} teams")
            
            result['competitions'].append(comp_data)
        
        logger.info(f"\n✅ Import complete: {len(result['competitions'])} competitions, {total_teams} teams")
        
        return result
    
    def generate_initial_player_list(self, structure_data: Dict) -> List[Dict]:
        """
        Generate initial player list from team structure
        
        For initial setup, we'll create placeholder players
        Real player data would come from match scorecards
        """
        
        players = []
        player_id_counter = 1
        
        for comp in structure_data['competitions']:
            for team in comp['teams']:
                # Create 15 placeholder players per team
                for i in range(1, 16):
                    player = {
                        'player_id': f"placeholder_{player_id_counter}",
                        'name': f"{team['team_name']} Player {i}",
                        'team_id': team['team_id'],
                        'team_name': team['team_name'],
                        'club_name': team['club_name'],
                        'tier': team['tier'],
                        'grade': team['grade'],
                        'position': 'All-rounder',
                        'initial_price': self._suggest_initial_price(team['tier']),
                        'is_placeholder': True
                    }
                    players.append(player)
                    player_id_counter += 1
        
        return players
    
    def _suggest_initial_price(self, tier: str) -> float:
        """Suggest initial player price based on tier"""
        base_prices = {
            'tier1': 35.0,
            'tier2': 25.0,
            'tier3': 20.0,
            'social': 15.0,
            'youth': 12.0,
            'ladies': 20.0
        }
        return base_prices.get(tier, 20.0)
    
    def export_for_database(self, season_id: int = 19, output_dir: str = "."):
        """
        Export data in format ready for database import
        
        Creates 3 files:
        1. competitions.json - All competitions/grades
        2. teams.json - All teams
        3. players.json - Initial player list
        """
        
        logger.info("Starting database export...")
        
        # Import structure
        structure = self.import_league_structure(season_id)
        
        # Extract competitions
        competitions = [{
            'grade_id': c['grade_id'],
            'name': c['name'],
            'short_name': c['short_name'],
            'tier': c['tier'],
            'multiplier': c['multiplier']
        } for c in structure['competitions']]
        
        # Extract all teams
        teams = []
        for comp in structure['competitions']:
            teams.extend(comp['teams'])
        
        # Generate player list
        players = self.generate_initial_player_list(structure)
        
        # Save files
        with open(f"{output_dir}/competitions.json", 'w') as f:
            json.dump(competitions, f, indent=2)
        logger.info(f"✅ Saved {len(competitions)} competitions")
        
        with open(f"{output_dir}/teams.json", 'w') as f:
            json.dump(teams, f, indent=2)
        logger.info(f"✅ Saved {len(teams)} teams")
        
        with open(f"{output_dir}/players.json", 'w') as f:
            json.dump(players, f, indent=2)
        logger.info(f"✅ Saved {len(players)} players")
        
        # Save complete structure
        with open(f"{output_dir}/full_structure.json", 'w') as f:
            json.dump(structure, f, indent=2)
        logger.info(f"✅ Saved complete structure")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 Export Summary")
        print("=" * 70)
        print(f"Competitions: {len(competitions)}")
        print(f"Teams: {len(teams)}")
        print(f"Players: {len(players)}")
        print("\nFiles created:")
        print(f"  - competitions.json")
        print(f"  - teams.json")
        print(f"  - players.json")
        print(f"  - full_structure.json")
        print("=" * 70)
        
        return {
            'competitions': competitions,
            'teams': teams,
            'players': players
        }


def main():
    """Main import function"""
    
    print("🏏 KNCB Fantasy Cricket - Data Import")
    print("=" * 70)
    print()
    
    importer = KNCBFantasyImporter(entity_id="134453")
    
    # Test connection
    print("Testing connection...")
    entity = importer.get_entity_info()
    if not entity:
        print("❌ Failed to connect to KNCB API")
        return
    
    print(f"✅ Connected to: {entity['entity_name']}")
    print(f"📍 Location: {entity.get('location', 'N/A')}")
    print(f"📅 Current Season: {entity.get('current_season_name', 'N/A')}")
    print()
    
    # Import data
    print("Starting import...")
    data = importer.export_for_database(season_id=19)
    
    # Show sample data
    print("\n📋 Sample Competitions:")
    for comp in data['competitions'][:5]:
        print(f"  - {comp['name']} ({comp['tier']}, {comp['multiplier']}x)")
    
    print("\n🏆 Sample Teams:")
    for team in data['teams'][:5]:
        print(f"  - {team['team_name']} ({team['club_name']}) - {team['tier']}")
    
    print("\n👥 Sample Players:")
    for player in data['players'][:5]:
        print(f"  - {player['name']} ({player['team_name']}) - €{player['initial_price']}")
    
    print("\n✅ Import complete! Data ready for database.")
    print("\n📝 Next steps:")
    print("1. Load these JSON files into your database")
    print("2. Update player names from match data later")
    print("3. Set up weekly points calculation")


if __name__ == "__main__":
    main()
