#!/usr/bin/env python3
"""
ResultsVault API - IP Blocking Workaround
=========================================
Multiple strategies to bypass IP blocking when fetching player data
"""

import requests
import json
import time
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResilientPlayerFetcher:
    """Fetch player data with multiple fallback strategies"""
    
    def __init__(self):
        self.base_url = "https://api.resultsvault.co.uk/rv"
        self.api_id = "1002"
        
        # Rotate through multiple user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        # Try different referers
        self.referers = [
            'https://matchcentre.kncb.nl/',
            'https://matchcentre.kncb.nl/players',
            'https://www.kncb.nl/',
        ]
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Generate random headers to avoid blocking"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': random.choice(self.referers),
            'Origin': 'https://matchcentre.kncb.nl',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
        }
    
    def strategy_1_direct(self, player_id: str, season_id: int = 19) -> Optional[List[Dict]]:
        """Strategy 1: Direct request with random headers"""
        
        logger.info("Strategy 1: Direct request with rotating headers...")
        
        url = f"{self.base_url}/0/report/rpt_plsml/"
        params = {
            'apiid': self.api_id,
            'seasonid': season_id,
            'playerid': player_id,
            'sportid': 1,
            'sort': '-DATE1'
        }
        
        try:
            session = requests.Session()
            
            # First, visit the main site to establish session
            session.get('https://matchcentre.kncb.nl/', timeout=10)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Now fetch player data
            response = session.get(
                url, 
                params=params, 
                headers=self._get_random_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Strategy 1 succeeded: {len(data)} matches")
                return data
            else:
                logger.warning(f"⚠️  Strategy 1 failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️  Strategy 1 error: {e}")
            return None
    
    def strategy_2_multiple_attempts(self, player_id: str, season_id: int = 19) -> Optional[List[Dict]]:
        """Strategy 2: Multiple attempts with increasing delays"""
        
        logger.info("Strategy 2: Multiple attempts with delays...")
        
        url = f"{self.base_url}/0/report/rpt_plsml/"
        params = {
            'apiid': self.api_id,
            'seasonid': season_id,
            'playerid': player_id,
            'sportid': 1,
            'sort': '-DATE1'
        }
        
        delays = [1, 3, 5, 10]  # Progressive delays
        
        for i, delay in enumerate(delays, 1):
            try:
                logger.info(f"  Attempt {i}/{len(delays)} (delay: {delay}s)...")
                time.sleep(delay)
                
                session = requests.Session()
                response = session.get(
                    url,
                    params=params,
                    headers=self._get_random_headers(),
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Strategy 2 succeeded on attempt {i}: {len(data)} matches")
                    return data
                    
            except Exception as e:
                logger.warning(f"  Attempt {i} failed: {e}")
                continue
        
        logger.warning("⚠️  Strategy 2 failed after all attempts")
        return None
    
    def strategy_3_cloudflare_bypass(self, player_id: str, season_id: int = 19) -> Optional[List[Dict]]:
        """Strategy 3: Use cloudscraper to bypass Cloudflare"""
        
        logger.info("Strategy 3: Cloudflare bypass...")
        
        try:
            import cloudscraper
            
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            
            url = f"{self.base_url}/0/report/rpt_plsml/"
            params = {
                'apiid': self.api_id,
                'seasonid': season_id,
                'playerid': player_id,
                'sportid': 1,
                'sort': '-DATE1'
            }
            
            response = scraper.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Strategy 3 succeeded: {len(data)} matches")
                return data
            else:
                logger.warning(f"⚠️  Strategy 3 failed: HTTP {response.status_code}")
                return None
                
        except ImportError:
            logger.warning("⚠️  Strategy 3 unavailable: cloudscraper not installed")
            logger.info("    Install with: pip install cloudscraper")
            return None
        except Exception as e:
            logger.warning(f"⚠️  Strategy 3 error: {e}")
            return None
    
    def strategy_4_proxy(self, player_id: str, season_id: int = 19) -> Optional[List[Dict]]:
        """Strategy 4: Use free proxy (optional)"""
        
        logger.info("Strategy 4: Proxy request...")
        
        # List of free proxy services (reliability varies)
        proxies_to_try = [
            # Format: {'http': 'http://proxy:port', 'https': 'http://proxy:port'}
            # Add your own proxies here if needed
        ]
        
        if not proxies_to_try:
            logger.warning("⚠️  Strategy 4 skipped: No proxies configured")
            return None
        
        url = f"{self.base_url}/0/report/rpt_plsml/"
        params = {
            'apiid': self.api_id,
            'seasonid': season_id,
            'playerid': player_id,
            'sportid': 1,
            'sort': '-DATE1'
        }
        
        for proxy in proxies_to_try:
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self._get_random_headers(),
                    proxies=proxy,
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Strategy 4 succeeded: {len(data)} matches")
                    return data
                    
            except Exception as e:
                logger.warning(f"  Proxy failed: {e}")
                continue
        
        logger.warning("⚠️  Strategy 4 failed: All proxies failed")
        return None
    
    def strategy_5_cache_fallback(self, player_id: str, cache_dir: str = "player_cache") -> Optional[List[Dict]]:
        """Strategy 5: Use cached data if available"""
        
        logger.info("Strategy 5: Checking cache...")
        
        from pathlib import Path
        
        cache_file = Path(cache_dir) / f"player_{player_id}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check if cache is recent (less than 7 days old)
                cache_age_days = (datetime.now() - datetime.fromisoformat(data.get('cached_at', '2000-01-01'))).days
                
                if cache_age_days < 7:
                    logger.info(f"✅ Strategy 5 succeeded: Using cache ({cache_age_days} days old)")
                    return data.get('matches', [])
                else:
                    logger.warning(f"⚠️  Cache too old ({cache_age_days} days)")
                    
            except Exception as e:
                logger.warning(f"⚠️  Cache read error: {e}")
        else:
            logger.warning("⚠️  No cache found")
        
        return None
    
    def fetch_with_fallback(self, player_id: str, season_id: int = 19) -> Optional[List[Dict]]:
        """
        Try all strategies in order until one succeeds
        
        Returns player match data or None
        """
        
        logger.info(f"🔄 Fetching player {player_id} with fallback strategies...")
        
        strategies = [
            ('Direct Request', lambda: self.strategy_1_direct(player_id, season_id)),
            ('Multiple Attempts', lambda: self.strategy_2_multiple_attempts(player_id, season_id)),
            ('Cloudflare Bypass', lambda: self.strategy_3_cloudflare_bypass(player_id, season_id)),
            ('Proxy', lambda: self.strategy_4_proxy(player_id, season_id)),
            ('Cache', lambda: self.strategy_5_cache_fallback(player_id)),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                result = strategy_func()
                if result:
                    logger.info(f"✅ Success using: {strategy_name}")
                    
                    # Cache the successful result
                    self._cache_result(player_id, result)
                    
                    return result
            except Exception as e:
                logger.error(f"❌ {strategy_name} exception: {e}")
                continue
        
        logger.error(f"❌ All strategies failed for player {player_id}")
        return None
    
    def _cache_result(self, player_id: str, data: List[Dict], cache_dir: str = "player_cache"):
        """Save successful fetch to cache"""
        
        from pathlib import Path
        
        try:
            Path(cache_dir).mkdir(exist_ok=True)
            
            cache_data = {
                'player_id': player_id,
                'cached_at': datetime.now().isoformat(),
                'matches': data
            }
            
            cache_file = Path(cache_dir) / f"player_{player_id}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"💾 Cached data for player {player_id}")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to cache: {e}")


# =============================================================================
# INTEGRATION WITH EXISTING IMPORTER
# =============================================================================

def enhanced_fetch_player(player_id: str, season_id: int = 19) -> Optional[List[Dict]]:
    """
    Drop-in replacement for fetch function with IP blocking workaround
    
    Use this in your PlayerDataImporter instead of the original fetch
    """
    
    fetcher = ResilientPlayerFetcher()
    return fetcher.fetch_with_fallback(player_id, season_id)


# =============================================================================
# TESTING AND CLI
# =============================================================================

def test_workaround():
    """Test the IP blocking workaround"""
    
    print("🏏 Testing IP Blocking Workaround")
    print("=" * 70)
    
    fetcher = ResilientPlayerFetcher()
    
    # Test with Sean Walsh
    player_id = '11190879'
    
    print(f"\nFetching player {player_id}...")
    print("-" * 70)
    
    data = fetcher.fetch_with_fallback(player_id)
    
    print("\n" + "=" * 70)
    
    if data:
        print(f"✅ SUCCESS!")
        print(f"   Retrieved {len(data)} match records")
        print(f"\n   Player: {data[0].get('player_name', 'Unknown')}")
        print(f"   Entity: {data[0].get('entity_name', 'Unknown')}")
        
        # Save to file
        with open('player_data_fetched.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n   📁 Saved to: player_data_fetched.json")
        
        return True
    else:
        print(f"❌ FAILED")
        print(f"   Could not fetch player {player_id} using any strategy")
        print(f"\n   Suggestions:")
        print(f"   1. Install cloudscraper: pip install cloudscraper")
        print(f"   2. Try again later (may be temporary rate limiting)")
        print(f"   3. Check if player_cache/ has cached data")
        
        return False


def install_dependencies():
    """Install optional dependencies for better success rate"""
    
    print("📦 Installing optional dependencies for IP workaround...")
    print("=" * 70)
    
    packages = [
        'cloudscraper',  # Cloudflare bypass
        'requests[socks]',  # SOCKS proxy support
    ]
    
    import subprocess
    
    for package in packages:
        try:
            print(f"\nInstalling {package}...")
            subprocess.check_call(['pip', 'install', package])
            print(f"✅ {package} installed")
        except Exception as e:
            print(f"⚠️  Failed to install {package}: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Installation complete!")
    print("\nRun the test again: python3 ip_blocking_workaround.py")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--install':
        install_dependencies()
    else:
        success = test_workaround()
        
        if not success:
            print("\n💡 TIP: Try installing optional dependencies:")
            print("   python3 ip_blocking_workaround.py --install")
