#!/usr/bin/env python3
"""
Fantasy Cricket - Complete Player Data Import System
====================================================
Fetches player data from ResultsVault API with retry logic
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayerDataImporter:
    """Import player performance data from ResultsVault API"""
    
    def __init__(self):
        self.base_url = "https://api.resultsvault.co.uk/rv"
        self.api_id = "1002"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://matchcentre.kncb.nl/'
        })
        
        # Fantasy points system
        self.points = {
            'batting': {
                'run': 1,
                'boundary_4': 1,
                'boundary_6': 2,
                'fifty_bonus': 8,
                'century_bonus': 16,
                'duck_penalty': -2
            },
            'bowling': {
                'wicket': 12,
                'maiden': 4,
                'four_wicket_bonus': 4,
                'five_wicket_bonus': 8
            },
            'fielding': {
                'catch': 4,
                'stumping': 6,
                'run_out': 6
            }
        }
        
        # Tier multipliers
        self.tier_multipliers = {
            'tier1': 1.2,
            'tier2': 1.0,
            'tier3': 0.8,
            'social': 0.4,
            'youth': 0.6,
            'ladies': 0.9
        }
    
    def fetch_player_season(self, player_id: str, season_id: int = 19, 
                           max_retries: int = 3) -> Optional[List[Dict]]:
        """
        Fetch player season data with retry logic
        
        Args:
            player_id: Player ID from ResultsVault
            season_id: Season ID (19 = 2025)
            max_retries: Number of retry attempts
        
        Returns:
            List of match performances or None
        """
        
        url = f"{self.base_url}/0/report/rpt_plsml/"
        params = {
            'apiid': self.api_id,
            'seasonid': season_id,
            'playerid': player_id,
            'sportid': 1,
            'sort': '-DATE1'
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Fetched {len(data)} matches for player {player_id}")
                    return data
                    
                elif response.status_code == 401:
                    logger.warning(f"⚠️  401 Unauthorized for player {player_id}, attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    
                else:
                    logger.error(f"❌ HTTP {response.status_code} for player {player_id}")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Error fetching player {player_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                    
        logger.error(f"❌ Failed to fetch player {player_id} after {max_retries} attempts")
        return None
    
    def parse_match_performance(self, match_data: Dict) -> Dict:
        """Parse single match performance from API format"""
        
        # Convert items list to dict
        items_dict = {}
        for item in match_data.get('items', []):
            items_dict[item['id']] = item.get('val')
        
        performance = {
            'player_id': match_data.get('player_id'),
            'player_name': match_data.get('player_name'),
            'entity_name': match_data.get('entity_name'),
            'match_id': items_dict.get('MID'),
            'date': items_dict.get('DATE1'),
            'grade_name': items_dict.get('GRNM'),
            'grade_id': items_dict.get('GRID'),
            'round': items_dict.get('RNDN', '').strip(),
            'home_team': items_dict.get('HMTM'),
            'away_team': items_dict.get('AWTM'),
            'is_home': items_dict.get('PLHOME') == '1',
        }
        
        # Batting stats
        batting = {}
        if items_dict.get('BAT') == '1':
            batting['runs'] = int(items_dict.get('BARUN', 0))
            batting['batting_number'] = int(items_dict.get('BANM', 0))
            batting['dismissal'] = items_dict.get('BADSAB')
        performance['batting'] = batting if batting else None
        
        # Bowling stats
        bowling = {}
        if items_dict.get('BOW') == '1':
            bowling['wickets'] = int(items_dict.get('BWWK', 0) or 0)
            bowling['maidens'] = int(items_dict.get('BWMD', 0) or 0)
            bowling['runs_conceded'] = int(items_dict.get('BWRN', 0) or 0)
            bowling['overs'] = float(items_dict.get('BWOV', 0) or 0)
        performance['bowling'] = bowling if bowling else None
        
        # Fielding stats
        fielding = {}
        if items_dict.get('FLD') == '1':
            fielding['catches_not_wk'] = int(items_dict.get('FLCNWK', 0) or 0)
            fielding['catches_as_wk'] = int(items_dict.get('FLCCWK', 0) or 0)
            fielding['run_outs_assist'] = int(items_dict.get('FLROA', 0) or 0)
            fielding['run_outs_unassist'] = int(items_dict.get('FLROU', 0) or 0)
            fielding['stumpings'] = int(items_dict.get('FLST', 0) or 0)
            
            fielding['total_catches'] = fielding['catches_not_wk'] + fielding['catches_as_wk']
            fielding['total_run_outs'] = fielding['run_outs_assist'] + fielding['run_outs_unassist']
        performance['fielding'] = fielding if fielding else None
        
        return performance
    
    def determine_tier(self, grade_name: str) -> str:
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
    
    def calculate_fantasy_points(self, performance: Dict, tier: str) -> int:
        """Calculate fantasy points from performance"""
        
        points = 0
        
        # Batting points
        if performance.get('batting'):
            bat = performance['batting']
            runs = bat.get('runs', 0)
            
            points += runs * self.points['batting']['run']
            
            if runs >= 100:
                points += self.points['batting']['century_bonus']
            elif runs >= 50:
                points += self.points['batting']['fifty_bonus']
            elif runs == 0:
                points += self.points['batting']['duck_penalty']
        
        # Bowling points
        if performance.get('bowling'):
            bowl = performance['bowling']
            wickets = bowl.get('wickets', 0)
            
            points += wickets * self.points['bowling']['wicket']
            points += bowl.get('maidens', 0) * self.points['bowling']['maiden']
            
            if wickets >= 5:
                points += self.points['bowling']['five_wicket_bonus']
            elif wickets >= 4:
                points += self.points['bowling']['four_wicket_bonus']
        
        # Fielding points
        if performance.get('fielding'):
            field = performance['fielding']
            points += field.get('total_catches', 0) * self.points['fielding']['catch']
            points += field.get('stumpings', 0) * self.points['fielding']['stumping']
            points += field.get('total_run_outs', 0) * self.points['fielding']['run_out']
        
        # Apply tier multiplier
        multiplier = self.tier_multipliers.get(tier, 1.0)
        points = int(points * multiplier)
        
        return max(0, points)
    
    def process_player(self, player_id: str, season_id: int = 19) -> Optional[Dict]:
        """
        Process complete player data including fantasy points
        
        Returns player profile with stats and all matches
        """
        
        # Fetch raw data
        raw_data = self.fetch_player_season(player_id, season_id)
        
        if not raw_data:
            return None
        
        # Parse all matches
        matches = []
        for match_data in raw_data:
            perf = self.parse_match_performance(match_data)
            tier = self.determine_tier(perf['grade_name'])
            perf['tier'] = tier
            perf['fantasy_points'] = self.calculate_fantasy_points(perf, tier)
            matches.append(perf)
        
        # Calculate season totals
        total_runs = sum(m['batting']['runs'] for m in matches if m.get('batting'))
        total_wickets = sum(m['bowling']['wickets'] for m in matches if m.get('bowling'))
        total_catches = sum(m['fielding']['total_catches'] for m in matches if m.get('fielding'))
        total_points = sum(m['fantasy_points'] for m in matches)
        
        # Get player info from first match
        first = matches[0] if matches else {}
        
        player_profile = {
            'player_id': player_id,
            'player_name': first.get('player_name', 'Unknown'),
            'entity_name': first.get('entity_name', 'Unknown'),
            'season_id': season_id,
            'last_updated': datetime.now().isoformat(),
            
            'season_stats': {
                'matches_played': len(matches),
                'total_runs': total_runs,
                'total_wickets': total_wickets,
                'total_catches': total_catches,
                'total_fantasy_points': total_points,
                'average_points': total_points // len(matches) if matches else 0,
                'highest_score': max((m['batting']['runs'] for m in matches if m.get('batting')), default=0),
                'best_bowling': max((m['bowling']['wickets'] for m in matches if m.get('bowling')), default=0),
                'centuries': len([m for m in matches if m.get('batting') and m['batting']['runs'] >= 100]),
                'fifties': len([m for m in matches if m.get('batting') and 50 <= m['batting']['runs'] < 100]),
                'five_wickets': len([m for m in matches if m.get('bowling') and m['bowling']['wickets'] >= 5])
            },
            
            'matches': matches,
            
            'suggested_price': self._suggest_price(
                total_points // len(matches) if matches else 0,
                total_points,
                len(matches)
            )
        }
        
        return player_profile
    
    def _suggest_price(self, avg_points: int, total_points: int, matches: int) -> float:
        """Suggest fantasy price based on performance"""
        
        base_price = 15.0
        price = base_price + avg_points
        
        # Consistency bonus
        if matches >= 10:
            price += 5
        elif matches >= 5:
            price += 2
        
        # High scorer bonus
        if total_points >= 500:
            price += 10
        elif total_points >= 300:
            price += 5
        
        # Round to nearest 5
        price = round(price / 5) * 5
        
        return min(price, 100.0)
    
    def import_multiple_players(self, player_ids: List[str], season_id: int = 19,
                               output_dir: str = "player_data") -> Dict:
        """
        Import multiple players with progress tracking
        
        Args:
            player_ids: List of player IDs to import
            season_id: Season ID
            output_dir: Directory to save data
        
        Returns:
            Summary of import
        """
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        results = {
            'successful': [],
            'failed': [],
            'total_attempted': len(player_ids),
            'import_date': datetime.now().isoformat()
        }
        
        logger.info(f"Starting import of {len(player_ids)} players...")
        
        for i, player_id in enumerate(player_ids, 1):
            logger.info(f"[{i}/{len(player_ids)}] Processing player {player_id}...")
            
            player_data = self.process_player(player_id, season_id)
            
            if player_data:
                # Save individual player file
                filename = f"{output_dir}/player_{player_id}.json"
                with open(filename, 'w') as f:
                    json.dump(player_data, f, indent=2)
                
                results['successful'].append({
                    'player_id': player_id,
                    'name': player_data['player_name'],
                    'matches': player_data['season_stats']['matches_played'],
                    'points': player_data['season_stats']['total_fantasy_points']
                })
                
                logger.info(f"  ✅ {player_data['player_name']}: {player_data['season_stats']['matches_played']} matches")
            else:
                results['failed'].append(player_id)
                logger.warning(f"  ❌ Failed to import player {player_id}")
            
            # Rate limiting - small delay between requests
            if i < len(player_ids):
                time.sleep(1)
        
        # Save summary
        with open(f"{output_dir}/import_summary.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n✅ Import complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
        
        return results


# =============================================================================
# USAGE EXAMPLES AND CLI
# =============================================================================

def test_single_player():
    """Test with Sean Walsh"""
    
    print("🏏 Testing Player Import - Sean Walsh")
    print("=" * 70)
    
    importer = PlayerDataImporter()
    player_data = importer.process_player('11190879')
    
    if player_data:
        print(f"\n✅ Player: {player_data['player_name']}")
        print(f"   Entity: {player_data['entity_name']}")
        
        stats = player_data['season_stats']
        print(f"\n📊 Season Stats:")
        print(f"   Matches: {stats['matches_played']}")
        print(f"   Runs: {stats['total_runs']}")
        print(f"   Wickets: {stats['total_wickets']}")
        print(f"   Catches: {stats['total_catches']}")
        print(f"   Fantasy Points: {stats['total_fantasy_points']}")
        print(f"   Average Points: {stats['average_points']}")
        
        print(f"\n💰 Suggested Price: €{player_data['suggested_price']}")
        
        # Save to file
        with open('sean_walsh_complete.json', 'w') as f:
            json.dump(player_data, f, indent=2)
        print(f"\n📁 Saved to sean_walsh_complete.json")
        
        return player_data
    else:
        print("❌ Failed to import player")
        return None


def import_acc_players():
    """Import known ACC players"""
    
    print("🏏 Importing ACC Players")
    print("=" * 70)
    
    # Example ACC player IDs (you'd get these from team rosters)
    player_ids = [
        '11190879',  # Sean Walsh
        # Add more player IDs here
    ]
    
    importer = PlayerDataImporter()
    results = importer.import_multiple_players(player_ids)
    
    print("\n📊 Import Summary:")
    print(f"   Total attempted: {results['total_attempted']}")
    print(f"   Successful: {len(results['successful'])}")
    print(f"   Failed: {len(results['failed'])}")
    
    if results['successful']:
        print("\n✅ Successfully imported:")
        for player in results['successful']:
            print(f"   - {player['name']}: {player['matches']} matches, {player['points']} points")
    
    if results['failed']:
        print("\n❌ Failed imports:")
        for player_id in results['failed']:
            print(f"   - Player ID: {player_id}")


if __name__ == "__main__":
    # Test with single player
    test_single_player()
    
    # Uncomment to import multiple players
    # import_acc_players()
