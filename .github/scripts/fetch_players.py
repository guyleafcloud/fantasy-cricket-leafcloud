#!/usr/bin/env python3
"""
Fetch player data from ResultsVault API via GitHub Actions
Since GitHub Actions run from different IPs, they're less likely to be blocked
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

def fetch_player_data(player_id: str, season_id: int = 19):
    """Fetch player data from API"""
    
    url = "https://api.resultsvault.co.uk/rv/0/report/rpt_plsml/"
    params = {
        'apiid': '1002',
        'seasonid': season_id,
        'playerid': player_id,
        'sportid': '1',
        'sort': '-DATE1'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://matchcentre.kncb.nl/'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Fetched {len(data)} matches for player {player_id}")
            return data
        else:
            print(f"❌ HTTP {response.status_code} for player {player_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching player {player_id}: {e}")
        return None


def main():
    """Main fetch routine"""
    
    print("🏏 KNCB Player Data Fetch")
    print("=" * 70)
    
    # Read player list
    player_list_file = Path('data/player_list.json')
    
    if not player_list_file.exists():
        print("⚠️  No player_list.json found, using default players")
        players_to_fetch = [
            {'player_id': '11190879', 'name': 'Sean Walsh'},
        ]
    else:
        with open(player_list_file, 'r') as f:
            players_to_fetch = json.load(f)
    
    print(f"📋 Fetching data for {len(players_to_fetch)} players...")
    
    # Create output directory
    output_dir = Path('data/players')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    successful = 0
    failed = 0
    
    for player in players_to_fetch:
        player_id = player['player_id']
        print(f"\n📥 Fetching player {player_id} ({player.get('name', 'Unknown')})...")
        
        data = fetch_player_data(player_id)
        
        if data:
            # Save to file
            output_file = output_dir / f"player_{player_id}.json"
            
            player_data = {
                'player_id': player_id,
                'fetched_at': datetime.now().isoformat(),
                'matches': data
            }
            
            with open(output_file, 'w') as f:
                json.dump(player_data, f, indent=2)
            
            print(f"   ✅ Saved to {output_file}")
            successful += 1
        else:
            print(f"   ❌ Failed to fetch player {player_id}")
            failed += 1
        
        # Rate limiting
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print(f"✅ Complete: {successful} successful, {failed} failed")
    
    # Create summary
    summary = {
        'last_updated': datetime.now().isoformat(),
        'total_players': len(players_to_fetch),
        'successful': successful,
        'failed': failed
    }
    
    with open('data/fetch_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
