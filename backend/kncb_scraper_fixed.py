#!/usr/bin/env python3
"""
Fixed KNCB MatchCentre Scraper for Fantasy Cricket
==================================================
Updated for current KNCB website structure (2025)
"""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KNCBScraperFixed:
    def __init__(self):
        self.base_url = "https://matchcentre.kncb.nl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Competition tier mappings
        self.tier_mappings = {
            'topklasse': 'tier1',
            'hoofdklasse': 'tier1',
            'eerste': 'tier2',
            'tweede': 'tier2',
            'derde': 'tier3',
            'vierde': 'tier3',
            'zami': 'social',
            'zomi': 'social',
            'recreanten': 'social',
            'jeugd': 'youth',
            'u19': 'youth',
            'u17': 'youth',
            'dames': 'ladies',
            'vrouwen': 'ladies'
        }
        
        # Points system
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
                'five_wicket_bonus': 8,
                'four_wicket_bonus': 4
            },
            'fielding': {
                'catch': 4,
                'stumping': 6,
                'run_out': 6
            }
        }
    
    def test_connection(self):
        """Test if KNCB website is accessible"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ KNCB website is accessible")
                return True
            else:
                logger.error(f"❌ KNCB returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to KNCB: {e}")
            return False
    
    def find_club_by_name(self, club_name: str) -> Optional[str]:
        """
        Search for a club and return its ID
        Example: "Amsterdam" -> club ID
        """
        try:
            # Try club search endpoint
            search_url = f"{self.base_url}/search"
            params = {'query': club_name, 'type': 'club'}
            
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for club links (structure may vary)
                club_links = soup.find_all('a', href=re.compile(r'/club/\d+'))
                
                for link in club_links:
                    if club_name.lower() in link.text.lower():
                        club_id = re.search(r'/club/(\d+)', link['href']).group(1)
                        logger.info(f"Found club: {link.text} (ID: {club_id})")
                        return club_id
            
            logger.warning(f"Could not find club: {club_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for club: {e}")
            return None
    
    def scrape_club_teams(self, club_id: str) -> List[Dict]:
        """Get all teams for a club"""
        try:
            url = f"{self.base_url}/club/{club_id}/teams"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch teams: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            teams = []
            
            # Parse teams - adjust selectors based on actual HTML
            team_elements = soup.find_all('div', class_='team-item')
            
            for team_elem in team_elements:
                team_name = team_elem.find('h3', class_='team-name')
                team_link = team_elem.find('a', href=re.compile(r'/team/\d+'))
                
                if team_name and team_link:
                    team_id = re.search(r'/team/(\d+)', team_link['href']).group(1)
                    name = team_name.text.strip()
                    
                    # Determine tier from team name
                    tier = self._determine_tier(name)
                    
                    teams.append({
                        'id': team_id,
                        'name': name,
                        'tier': tier
                    })
                    
            logger.info(f"Found {len(teams)} teams for club {club_id}")
            return teams
            
        except Exception as e:
            logger.error(f"Error scraping teams: {e}")
            return []
    
    def scrape_team_players(self, team_id: str) -> List[Dict]:
        """Get players for a team"""
        try:
            url = f"{self.base_url}/team/{team_id}/players"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            players = []
            
            # Parse player list - adjust based on HTML structure
            player_rows = soup.find_all('tr', class_='player-row')
            
            for row in player_rows:
                name_elem = row.find('td', class_='player-name')
                if not name_elem:
                    continue
                
                player_link = name_elem.find('a')
                if player_link:
                    player_id = re.search(r'/player/(\d+)', player_link['href'])
                    player_id = player_id.group(1) if player_id else None
                    
                    players.append({
                        'id': player_id,
                        'name': name_elem.text.strip(),
                        'team_id': team_id
                    })
            
            return players
            
        except Exception as e:
            logger.error(f"Error scraping players: {e}")
            return []
    
    def scrape_recent_matches(self, team_id: str, weeks: int = 2) -> List[Dict]:
        """Get recent match data for a team"""
        try:
            url = f"{self.base_url}/team/{team_id}/matches"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            matches = []
            
            # Find recent matches
            match_items = soup.find_all('div', class_='match-item')
            cutoff_date = datetime.now() - timedelta(weeks=weeks)
            
            for match in match_items:
                date_elem = match.find('span', class_='match-date')
                if not date_elem:
                    continue
                
                # Parse date
                date_text = date_elem.text.strip()
                match_date = self._parse_date(date_text)
                
                if match_date and match_date >= cutoff_date:
                    match_link = match.find('a', href=re.compile(r'/match/\d+'))
                    if match_link:
                        match_id = re.search(r'/match/(\d+)', match_link['href']).group(1)
                        matches.append({
                            'id': match_id,
                            'date': match_date,
                            'team_id': team_id
                        })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error scraping matches: {e}")
            return []
    
    def scrape_match_scorecard(self, match_id: str) -> Dict:
        """
        Scrape detailed scorecard for a match
        Returns player performances for fantasy points
        """
        try:
            url = f"{self.base_url}/match/{match_id}/scorecard"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            performances = []
            
            # Parse batting innings
            batting_tables = soup.find_all('table', class_='batting-table')
            
            for table in batting_tables:
                rows = table.find_all('tr', class_='batsman')
                
                for row in rows:
                    player_name = row.find('td', class_='player-name').text.strip()
                    runs = int(row.find('td', class_='runs').text.strip() or 0)
                    balls = int(row.find('td', class_='balls').text.strip() or 0)
                    fours = int(row.find('td', class_='fours').text.strip() or 0)
                    sixes = int(row.find('td', class_='sixes').text.strip() or 0)
                    
                    performances.append({
                        'player_name': player_name,
                        'match_id': match_id,
                        'batting': {
                            'runs': runs,
                            'balls': balls,
                            'fours': fours,
                            'sixes': sixes
                        }
                    })
            
            # Parse bowling innings
            bowling_tables = soup.find_all('table', class_='bowling-table')
            
            for table in bowling_tables:
                rows = table.find_all('tr', class_='bowler')
                
                for row in rows:
                    player_name = row.find('td', class_='player-name').text.strip()
                    wickets = int(row.find('td', class_='wickets').text.strip() or 0)
                    maidens = int(row.find('td', class_='maidens').text.strip() or 0)
                    
                    # Find or create performance entry
                    perf = next((p for p in performances if p['player_name'] == player_name), None)
                    if perf:
                        perf['bowling'] = {'wickets': wickets, 'maidens': maidens}
                    else:
                        performances.append({
                            'player_name': player_name,
                            'match_id': match_id,
                            'bowling': {'wickets': wickets, 'maidens': maidens}
                        })
            
            return {
                'match_id': match_id,
                'performances': performances
            }
            
        except Exception as e:
            logger.error(f"Error scraping scorecard: {e}")
            return {}
    
    def calculate_fantasy_points(self, performance: Dict) -> int:
        """Calculate fantasy points from performance data"""
        points = 0
        
        # Batting points
        if 'batting' in performance:
            bat = performance['batting']
            points += bat.get('runs', 0) * self.points['batting']['run']
            points += bat.get('fours', 0) * self.points['batting']['boundary_4']
            points += bat.get('sixes', 0) * self.points['batting']['boundary_6']
            
            runs = bat.get('runs', 0)
            if runs >= 100:
                points += self.points['batting']['century_bonus']
            elif runs >= 50:
                points += self.points['batting']['fifty_bonus']
            elif runs == 0 and bat.get('balls', 0) > 0:
                points += self.points['batting']['duck_penalty']
        
        # Bowling points
        if 'bowling' in performance:
            bowl = performance['bowling']
            wickets = bowl.get('wickets', 0)
            points += wickets * self.points['bowling']['wicket']
            points += bowl.get('maidens', 0) * self.points['bowling']['maiden']
            
            if wickets >= 5:
                points += self.points['bowling']['five_wicket_bonus']
            elif wickets >= 4:
                points += self.points['bowling']['four_wicket_bonus']
        
        # Fielding points
        if 'fielding' in performance:
            field = performance['fielding']
            points += field.get('catches', 0) * self.points['fielding']['catch']
            points += field.get('stumpings', 0) * self.points['fielding']['stumping']
            points += field.get('run_outs', 0) * self.points['fielding']['run_out']
        
        return max(0, points)
    
    def _determine_tier(self, team_name: str) -> str:
        """Determine competition tier from team name"""
        name_lower = team_name.lower()
        
        for keyword, tier in self.tier_mappings.items():
            if keyword in name_lower:
                return tier
        
        return 'tier3'  # Default
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse various date formats from KNCB"""
        try:
            # Try common formats
            formats = [
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%Y-%m-%d',
                '%d %B %Y',
                '%d %b %Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_text.strip(), fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None

# Testing functions
def test_scraper():
    """Test the scraper with real data"""
    scraper = KNCBScraperFixed()
    
    print("🔍 Testing KNCB Scraper...")
    print("=" * 50)
    
    # Test 1: Connection
    print("\n1️⃣ Testing connection...")
    if not scraper.test_connection():
        print("❌ Cannot connect to KNCB. Check your internet connection.")
        return
    
    # Test 2: Club search
    print("\n2️⃣ Testing club search...")
    club_id = scraper.find_club_by_name("Amsterdam")
    if club_id:
        print(f"✅ Found Amsterdam club (ID: {club_id})")
    else:
        print("❌ Could not find Amsterdam club. Try manual ID.")
        club_id = input("Enter club ID manually (or 'skip'): ")
        if club_id == 'skip':
            return
    
    # Test 3: Get teams
    print("\n3️⃣ Getting club teams...")
    teams = scraper.scrape_club_teams(club_id)
    if teams:
        print(f"✅ Found {len(teams)} teams:")
        for team in teams[:5]:  # Show first 5
            print(f"   - {team['name']} ({team['tier']})")
    
    # Test 4: Get players (first team)
    if teams:
        print(f"\n4️⃣ Getting players from {teams[0]['name']}...")
        players = scraper.scrape_team_players(teams[0]['id'])
        print(f"✅ Found {len(players)} players")
        for player in players[:5]:
            print(f"   - {player['name']}")
    
    # Test 5: Get recent matches
    if teams:
        print(f"\n5️⃣ Getting recent matches...")
        matches = scraper.scrape_recent_matches(teams[0]['id'])
        print(f"✅ Found {len(matches)} recent matches")
    
    print("\n" + "=" * 50)
    print("✅ Scraper test complete!")
    print("\nNext steps:")
    print("1. If errors occurred, inspect the HTML structure at:")
    print(f"   {scraper.base_url}")
    print("2. Update the CSS selectors in the code")
    print("3. Test with your specific club ID")

if __name__ == "__main__":
    test_scraper()
