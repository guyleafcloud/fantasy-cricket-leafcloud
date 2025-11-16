# #!/usr/bin/env python3
"""
ResultsVault Player Performance Parser
======================================
Parse player statistics from KNCB ResultsVault API format
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResultsVaultParser:
    """Parse player data from ResultsVault API"""
    
    def __init__(self):
        self.base_url = "https://api.resultsvault.co.uk/rv"
        self.api_id = "1002"
        
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
            'tier1': 1.2,  # Topklasse/Hoofdklasse
            'tier2': 1.0,  # Eerste/Tweede Klasse
            'tier3': 0.8,  # Derde/Vierde Klasse
            'social': 0.4, # Zami/Zomi
            'youth': 0.6,  # U17/U15/U13
            'ladies': 0.9  # Vrouwen
        }
    
    def parse_player_item(self, item: Dict) -> Optional[str]:
        """Extract value from item dict"""
        return item.get('val')
    
    def parse_match_performance(self, match_data: Dict) -> Dict:
        """
        Parse a single match performance from ResultsVault format
        
        Input: Single match entry with 'items' list
        Output: Clean performance dict with fantasy points
        """
        
        # Convert items list to dict for easier access
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
            
            # Total catches and run outs
            fielding['total_catches'] = (
                fielding['catches_not_wk'] + fielding['catches_as_wk']
            )
            fielding['total_run_outs'] = (
                fielding['run_outs_assist'] + fielding['run_outs_unassist']
            )
            
        performance['fielding'] = fielding if fielding else None
        
        return performance
    
    def determine_tier(self, grade_name: str) -> str:
        """Determine competition tier from grade name"""
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
        elif 'vrouwen' in name_lower or 'women' in name_lower or 'dames' in name_lower:
            return 'ladies'
        else:
            return 'tier3'
    
    def calculate_fantasy_points(self, performance: Dict, tier: str = None) -> int:
        """Calculate fantasy points from performance data"""
        
        points = 0
        
        # Determine tier if not provided
        if tier is None:
            tier = self.determine_tier(performance.get('grade_name', ''))
        
        # Batting points
        if performance.get('batting'):
            bat = performance['batting']
            runs = bat.get('runs', 0)
            
            # Base points
            points += runs * self.points['batting']['run']
            
            # Milestones
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
    
    def parse_player_season(self, player_data: List[Dict]) -> Dict:
        """
        Parse full season data for a player
        
        Input: List of match performances from API
        Output: Player summary with all matches and total points
        """
        
        if not player_data:
            return {}
        
        # Parse all matches
        matches = []
        for match_data in player_data:
            perf = self.parse_match_performance(match_data)
            tier = self.determine_tier(perf['grade_name'])
            perf['tier'] = tier
            perf['fantasy_points'] = self.calculate_fantasy_points(perf, tier)
            matches.append(perf)
        
        # Calculate season totals
        total_runs = sum(
            m['batting']['runs'] for m in matches 
            if m.get('batting')
        )
        
        total_wickets = sum(
            m['bowling']['wickets'] for m in matches 
            if m.get('bowling')
        )
        
        total_catches = sum(
            m['fielding']['total_catches'] for m in matches 
            if m.get('fielding')
        )
        
        total_points = sum(m['fantasy_points'] for m in matches)
        
        # Get player info from first match
        first_match = matches[0] if matches else {}
        
        return {
            'player_id': first_match.get('player_id'),
            'player_name': first_match.get('player_name'),
            'entity_name': first_match.get('entity_name'),
            'season_stats': {
                'matches_played': len(matches),
                'total_runs': total_runs,
                'total_wickets': total_wickets,
                'total_catches': total_catches,
                'total_fantasy_points': total_points,
                'average_points': total_points // len(matches) if matches else 0,
                'highest_score': max(
                    (m['batting']['runs'] for m in matches if m.get('batting')),
                    default=0
                ),
                'centuries': len([
                    m for m in matches 
                    if m.get('batting') and m['batting']['runs'] >= 100
                ]),
                'fifties': len([
                    m for m in matches 
                    if m.get('batting') and 50 <= m['batting']['runs'] < 100
                ])
            },
            'matches': matches
        }
    
    def fetch_player_season(self, player_id: str, season_id: int = 19) -> Dict:
        """Fetch and parse player season data from API"""
        
        url = f"{self.base_url}/0/report/rpt_plsml/"
        params = {
            'apiid': self.api_id,
            'seasonid': season_id,
            'playerid': player_id,
            'sportid': 1,
            'sort': '-DATE1'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return self.parse_player_season(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch player data: {e}")
            return {}
    
    def suggest_player_price(self, season_stats: Dict, base_price: float = 20.0) -> float:
        """
        Suggest a fantasy price for a player based on their stats
        
        Base price: €20
        Adjusted by: points, tier, consistency
        """
        
        if not season_stats:
            return base_price
        
        avg_points = season_stats.get('average_points', 0)
        total_points = season_stats.get('total_fantasy_points', 0)
        matches = season_stats.get('matches_played', 1)
        
        # Price based on average points per match
        # €1 per point on average
        price = base_price + avg_points
        
        # Bonus for consistency (played many matches)
        if matches >= 10:
            price += 5
        elif matches >= 5:
            price += 2
        
        # Bonus for high total points
        if total_points >= 500:
            price += 10
        elif total_points >= 300:
            price += 5
        
        # Bonus for milestones
        centuries = season_stats.get('centuries', 0)
        fifties = season_stats.get('fifties', 0)
        price += centuries * 5 + fifties * 2
        
        # Round to nearest 5
        price = round(price / 5) * 5
        
        return min(price, 100.0)  # Cap at €100


# =============================================================================
# TESTING
# =============================================================================

def test_parser():
    """Test the parser with Sean Walsh's data"""
    
    print("🏏 Testing ResultsVault Parser")
    print("=" * 70)
    
    parser = ResultsVaultParser()
    
    # Fetch Sean Walsh's data
    print("\n1️⃣ Fetching player data...")
    player_data = parser.fetch_player_season('11190879', season_id=19)
    
    if not player_data:
        print("❌ Failed to fetch data")
        return
    
    print(f"✅ Loaded data for {player_data['player_name']}")
    
    # Display season stats
    print("\n2️⃣ Season Statistics:")
    stats = player_data['season_stats']
    print(f"   Matches Played: {stats['matches_played']}")
    print(f"   Total Runs: {stats['total_runs']}")
    print(f"   Total Wickets: {stats['total_wickets']}")
    print(f"   Total Catches: {stats['total_catches']}")
    print(f"   Centuries: {stats['centuries']}")
    print(f"   Fifties: {stats['fifties']}")
    print(f"   Highest Score: {stats['highest_score']}")
    
    # Fantasy points
    print("\n3️⃣ Fantasy Points:")
    print(f"   Total Points: {stats['total_fantasy_points']}")
    print(f"   Average Points: {stats['average_points']} per match")
    
    # Suggested price
    suggested_price = parser.suggest_player_price(stats)
    print(f"   Suggested Price: €{suggested_price}")
    
    # Show top 5 performances
    print("\n4️⃣ Top 5 Performances:")
    top_matches = sorted(
        player_data['matches'],
        key=lambda x: x['fantasy_points'],
        reverse=True
    )[:5]
    
    for i, match in enumerate(top_matches, 1):
        runs = match.get('batting', {}).get('runs', 0) if match.get('batting') else 0
        wickets = match.get('bowling', {}).get('wickets', 0) if match.get('bowling') else 0
        
        print(f"   {i}. {match['date'][:10]} vs {match['away_team']}")
        print(f"      {runs} runs, {wickets} wickets = {match['fantasy_points']} points")
    
    print("\n" + "=" * 70)
    print("✅ Parser test complete!")
    
    return player_data


if __name__ == "__main__":
    test_parser()
