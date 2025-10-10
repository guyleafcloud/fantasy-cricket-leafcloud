#!/usr/bin/env python3
"""
Enhanced KNCB MatchCentre Scraper for Fantasy Cricket
===================================================
Weekly points calculation with social team support
"""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
import time

logger = logging.getLogger(__name__)

class KNCBScraper:
    def __init__(self):
        self.base_url = "https://matchcentre.kncb.nl/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LeafCloud Fantasy Cricket Bot 1.0'
        })
        
        # Dutch cricket competition tiers with proper league structure
        self.competition_tiers = {
            # Tier 1: Top level competitions
            'tier1': {
                'competitions': ['topklasse', 'hoofdklasse'],
                'multiplier': 1.2,
                'label': 'Tier 1 (Topklasse/Hoofdklasse)'
            },
            # Tier 2: First and second division
            'tier2': {
                'competitions': ['eerste klasse', 'tweede klasse'],
                'multiplier': 1.0,
                'label': 'Tier 2 (Eerste/Tweede Klasse)'
            },
            # Tier 3: Third and fourth division
            'tier3': {
                'competitions': ['derde klasse', 'vierde klasse'],
                'multiplier': 0.8,
                'label': 'Tier 3 (Derde/Vierde Klasse)'
            },
            # Social: Saturday and Sunday recreational
            'social': {
                'competitions': ['zami', 'zomi', 'recreanten', 'vriendschappelijk'],
                'multiplier': 0.4,
                'label': 'Social (Zami/Zomi)'
            },
            # Youth: All junior competitions
            'youth': {
                'competitions': ['jeugd', 'u19', 'u17', 'u15', 'u13', 'u11', 'junior'],
                'multiplier': 0.6,
                'label': 'Youth (Jeugd)'
            },
            # Ladies: Women's competitions
            'ladies': {
                'competitions': ['dames', 'vrouwen', 'women'],
                'multiplier': 0.9,
                'label': 'Ladies (Dames)'
            }
        }
        
        # Fantasy points system
        self.points_system = {
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
                'five_wicket_bonus': 8
            },
            'fielding': {
                'catch': 4,
                'stumping': 6,
                'run_out': 6
            }
        }
    
    def scrape_club_data(self, club_name: str) -> Dict:
        """Scrape recent match data for a club"""
        logger.info(f"Scraping data for {club_name}")
        
        # Implementation would scrape KNCB website
        # Return mock data for now
        return {
            'club': club_name,
            'matches_found': 3,
            'players_updated': 45,
            'last_scraped': datetime.now().isoformat()
        }
    
    def calculate_fantasy_points(self, performance: Dict) -> int:
        """Calculate fantasy points for a player performance"""
        points = 0
        
        # Batting points
        points += performance.get('runs', 0) * self.points_system['batting']['run']
        points += performance.get('fours', 0) * self.points_system['batting']['boundary_4']
        points += performance.get('sixes', 0) * self.points_system['batting']['boundary_6']
        
        # Batting bonuses
        runs = performance.get('runs', 0)
        if runs >= 100:
            points += self.points_system['batting']['century_bonus']
        elif runs >= 50:
            points += self.points_system['batting']['fifty_bonus']
        elif runs == 0 and performance.get('balls_faced', 0) > 0:
            points += self.points_system['batting']['duck_penalty']
        
        # Bowling points
        points += performance.get('wickets', 0) * self.points_system['bowling']['wicket']
        points += performance.get('maidens', 0) * self.points_system['bowling']['maiden']
        
        # Bowling bonuses
        if performance.get('wickets', 0) >= 5:
            points += self.points_system['bowling']['five_wicket_bonus']
        
        # Fielding points
        points += performance.get('catches', 0) * self.points_system['fielding']['catch']
        points += performance.get('stumpings', 0) * self.points_system['fielding']['stumping']
        points += performance.get('run_outs', 0) * self.points_system['fielding']['run_out']
        
        return max(0, points)