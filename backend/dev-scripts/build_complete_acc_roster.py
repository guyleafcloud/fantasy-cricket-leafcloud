#!/usr/bin/env python3
"""
Complete ACC Roster Builder - All Teams & All Leagues
=====================================================
Builds a comprehensive ACC roster across all Dutch cricket leagues.

Dutch Cricket League Structure:
- Hoofdklasse (Premier Division) - ACC 1
- Tweede Klasse (Second Division) - ACC 2
- Derde Klasse (Third Division) - ACC 3, ACC 4
- Vierde Klasse (Fourth Division) - ACC 5, ACC 6
- ZAMI Klasse (Social/Recreational) - ACC ZAMI 1, ACC ZAMI 2
- Youth Leagues - Various youth teams

This creates a realistic roster with:
- 11-15 players per team
- Varied performance profiles based on league level
- Calculated fantasy values with proper tier adjustments
"""

import json
import random
from typing import List, Dict
from player_value_calculator import PlayerValueCalculator, PlayerStats

# Seed for reproducibility
random.seed(42)


# =============================================================================
# DUTCH CRICKET LEAGUE STRUCTURE
# =============================================================================

ACC_TEAMS = {
    "Hoofdklasse": {
        "teams": ["ACC 1"],
        "level_code": "hoofdklasse",
        "player_count": 16,
        "skill_distribution": {"elite": 4, "good": 8, "average": 4},
        "tier_multiplier": 1.0,
        "description": "Premier Division - Highest level"
    },
    "Tweede Klasse": {
        "teams": ["ACC 2"],
        "level_code": "tweede",
        "player_count": 15,
        "skill_distribution": {"good": 5, "average": 8, "developing": 2},
        "tier_multiplier": 1.1,
        "description": "Second Division"
    },
    "Derde Klasse": {
        "teams": ["ACC 3", "ACC 4"],
        "level_code": "derde",
        "player_count": 14,
        "skill_distribution": {"good": 2, "average": 8, "developing": 4},
        "tier_multiplier": 1.2,
        "description": "Third Division"
    },
    "Vierde Klasse": {
        "teams": ["ACC 5", "ACC 6"],
        "level_code": "vierde",
        "player_count": 13,
        "skill_distribution": {"average": 5, "developing": 8},
        "tier_multiplier": 1.3,
        "description": "Fourth Division"
    },
    "ZAMI Klasse": {
        "teams": ["ACC ZAMI 1", "ACC ZAMI 2"],
        "level_code": "zami",
        "player_count": 12,
        "skill_distribution": {"average": 3, "developing": 7, "beginner": 2},
        "tier_multiplier": 1.4,
        "description": "Social/Recreational Division"
    },
    "Youth": {
        "teams": ["ACC Youth U19", "ACC Youth U17"],
        "level_code": "youth",
        "player_count": 13,
        "skill_distribution": {"good": 2, "average": 5, "developing": 6},
        "tier_multiplier": 1.25,
        "description": "Youth Leagues"
    }
}


def generate_player_stats(
    name: str,
    club: str,
    league: str,
    team_name: str,
    player_type: str = "all-rounder",
    skill_level: str = "average"
) -> PlayerStats:
    """
    Generate realistic player stats based on league level, type, and skill.

    Args:
        name: Player name
        club: Club name (ACC)
        league: League name (Hoofdklasse, Tweede Klasse, etc.)
        team_name: Specific team (ACC 1, ACC 2, etc.)
        player_type: batsman, bowler, all-rounder, wicket-keeper
        skill_level: elite, good, average, developing, beginner
    """

    # Matches vary by league level
    league_matches = {
        "Hoofdklasse": (12, 16),
        "Tweede Klasse": (11, 14),
        "Derde Klasse": (10, 13),
        "Vierde Klasse": (9, 12),
        "ZAMI Klasse": (7, 10),
        "Youth": (10, 14)
    }

    matches = random.randint(*league_matches.get(league, (8, 12)))

    # Skill multipliers
    skill_multipliers = {
        "elite": 1.6,
        "good": 1.3,
        "average": 1.0,
        "developing": 0.75,
        "beginner": 0.5
    }
    multiplier = skill_multipliers.get(skill_level, 1.0)

    # Create stats object
    stats = PlayerStats(
        player_name=name,
        club=club,
        matches_played=matches,
        team_level=ACC_TEAMS[league]["level_code"]
    )

    # Generate batting stats
    if player_type in ["batsman", "all-rounder", "wicket-keeper"]:
        base_runs = random.randint(120, 650)
        stats.total_runs = int(base_runs * multiplier)
        stats.batting_average = round(stats.total_runs / max(1, matches - random.randint(1, 3)), 1)
        stats.strike_rate = round(random.uniform(75, 155) * multiplier, 1)
        stats.fours = int(stats.total_runs / random.uniform(5, 8))
        stats.sixes = int(stats.total_runs / random.uniform(25, 35))

        if stats.total_runs > 350:
            stats.fifties = random.randint(1, 4)
        if stats.total_runs > 500:
            stats.hundreds = random.randint(1, 2)

    # Generate bowling stats
    if player_type in ["bowler", "all-rounder"]:
        base_wickets = random.randint(6, 38)
        stats.total_wickets = int(base_wickets * multiplier)
        stats.total_overs_bowled = round(matches * random.uniform(5, 11), 1)
        stats.bowling_average = round(random.uniform(14, 38) / multiplier, 1)
        stats.economy_rate = round(random.uniform(3.2, 6.8) / multiplier, 2)
        stats.total_runs_conceded = int(stats.total_overs_bowled * stats.economy_rate)

        if stats.total_wickets > 20:
            stats.five_wicket_hauls = random.randint(1, 3)

        stats.maidens = int(stats.total_overs_bowled / random.uniform(8, 15))

    # Fielding stats (everyone fields)
    stats.catches = random.randint(2, 14)
    stats.run_outs = random.randint(0, 4)

    if player_type == "wicket-keeper":
        stats.catches = random.randint(10, 25)
        stats.stumpings = random.randint(1, 6)

    return stats


def create_complete_acc_roster() -> Dict:
    """
    Create complete ACC roster with all teams across all leagues
    """

    # Dutch/International names for realism
    first_names = [
        "Boris", "Sikander", "Shariz", "Musa", "Saqib", "Asad", "Kashif",
        "Roel", "Victor", "Olivier", "Sebastiaan", "Arnav", "Jitse", "Niels",
        "Tom", "Quirijn", "Daniel", "Sjoerd", "Robin", "Mitchell", "Julian",
        "Tobias", "Maarten", "Rohan", "Tim", "Lars", "Daan", "Bram", "Jasper",
        "Finn", "Lucas", "Max", "Noah", "Levi", "Sem", "Milan", "Luuk",
        "Jayden", "Ryan", "Thijs", "Jesse", "Thomas", "Ruben", "Stijn",
        "Imran", "Hassan", "Ali", "Omar", "Bilal", "Hamza", "Tariq",
        "Pradeep", "Raj", "Arun", "Vikram", "Rahul", "Amit", "Suresh",
        "Mohammed", "Ahmed", "Youssef", "Khalid", "Mustafa", "Ibrahim",
        "Pieter", "Kees", "Willem", "Joost", "Bas", "Jeroen", "Mark",
        "Stefan", "Kevin", "Dennis", "Patrick", "Martijn", "Erik", "Frank"
    ]

    last_names = [
        "Gorlee", "Zulfiqar", "Ahmad", "Naseem", "Verhagen", "Lubbers",
        "Elenbaas", "Braat", "Jain", "Wilders", "Etman", "de Grooth",
        "Gunning", "Watson", "Stolk", "van Manen", "Koot", "de Mey",
        "Visee", "Boers", "Chopra", "Gruijters", "van der Berg", "Bakker",
        "Jansen", "Smit", "de Vries", "van Dijk", "Mulder", "Bos",
        "Khan", "Patel", "Singh", "Sharma", "Kumar", "Reddy", "Rao",
        "van Leeuwen", "de Jong", "Hendriks", "van den Berg", "Peters",
        "Ali", "Hassan", "Hussain", "Mohammed", "Ahmed", "Malik",
        "de Boer", "Visser", "Jacobs", "van der Meer", "Dekker"
    ]

    all_players = []
    player_stats_list = []
    used_names = set()

    calculator = PlayerValueCalculator()

    print("\n🏏 Building Complete ACC Roster - All Leagues\n")
    print("=" * 80)

    total_players = 0

    # Generate players for each league and team
    for league, league_info in ACC_TEAMS.items():
        print(f"\n📋 {league} ({league_info['description']})")
        print(f"   Tier Multiplier: {league_info['tier_multiplier']}x")

        for team_name in league_info["teams"]:
            print(f"\n   🏆 {team_name}")
            print(f"      Target: {league_info['player_count']} players")

            # Build skill level list
            skill_levels = []
            for skill, count in league_info['skill_distribution'].items():
                skill_levels.extend([skill] * count)

            # Generate players for this team
            for i in range(league_info['player_count']):
                # Create unique name
                attempts = 0
                while attempts < 100:
                    first = random.choice(first_names)
                    last = random.choice(last_names)
                    name = f"{first} {last}"
                    if name not in used_names:
                        used_names.add(name)
                        break
                    attempts += 1

                # Determine player type
                if i < 2:
                    player_type = "wicket-keeper"
                elif i < 7:
                    player_type = "batsman"
                elif i < 11:
                    player_type = "all-rounder"
                else:
                    player_type = "bowler"

                # Get skill level
                skill = skill_levels[i] if i < len(skill_levels) else "average"

                # Generate stats
                stats = generate_player_stats(
                    name=name,
                    club="ACC",
                    league=league,
                    team_name=team_name,
                    player_type=player_type,
                    skill_level=skill
                )
                player_stats_list.append(stats)

                all_players.append({
                    "name": name,
                    "league": league,
                    "team_name": team_name,
                    "team_level": league_info["level_code"],
                    "player_type": player_type,
                    "skill_level": skill
                })

                total_players += 1

            print(f"      ✅ Generated {league_info['player_count']} players")

    # Calculate values for all players - PER TEAM (not globally!)
    print(f"\n💰 Calculating fantasy values for {total_players} players...")
    print(f"   Using per-team ranking (best in each team = €50)")

    # Create mapping from player name to team_name
    name_to_team = {}
    for i, stats in enumerate(player_stats_list):
        name_to_team[stats.player_name] = all_players[i]["team_name"]

    # Use per-team value calculation
    results = calculator.calculate_team_values_per_team(
        player_stats_list,
        team_name_getter=lambda p: name_to_team[p.player_name]
    )

    # Build final roster
    roster = {
        "club": "ACC",
        "season": "2025",
        "created_at": "2025-11-05",
        "notes": "Complete ACC roster across all Dutch cricket leagues",
        "total_players": total_players,
        "leagues": {league: {"teams": info["teams"], "tier_multiplier": info["tier_multiplier"]}
                   for league, info in ACC_TEAMS.items()},
        "players": []
    }

    for i, (stats, value, justification) in enumerate(results):
        # Look up team_name using the mapping (results are sorted, all_players is not!)
        team_name = name_to_team[stats.player_name]
        # Find league from team_name
        league = None
        for league_name, league_info in ACC_TEAMS.items():
            if team_name in league_info["teams"]:
                league = league_name
                break

        player_entry = {
            "player_id": f"acc_2025_{i+1:03d}",
            "name": stats.player_name,
            "club": "ACC",
            "team_name": team_name,
            "league": league,
            "team_level": stats.team_level,
            "fantasy_value": round(value, 1),
            "stats": {
                "matches": stats.matches_played,
                "runs": stats.total_runs,
                "batting_avg": round(stats.batting_average, 2),
                "strike_rate": round(stats.strike_rate, 2),
                "wickets": stats.total_wickets,
                "bowling_avg": round(stats.bowling_average, 2),
                "economy": round(stats.economy_rate, 2),
                "catches": stats.catches,
                "run_outs": stats.run_outs
            }
        }
        roster['players'].append(player_entry)

    # Sort by value (highest first)
    roster['players'].sort(key=lambda x: x['fantasy_value'], reverse=True)

    print(f"   ✅ Calculated values for {len(results)} players")

    return roster


def print_roster_summary(roster: Dict):
    """Print detailed summary of generated roster"""
    players = roster['players']

    print("\n" + "=" * 80)
    print(f"🏏 Complete ACC Roster Summary - All Leagues")
    print("=" * 80)
    print(f"\nTotal Players: {roster['total_players']}")
    print(f"Season: {roster['season']}")

    print(f"\n📊 League Distribution:")
    for league, info in roster['leagues'].items():
        teams = info['teams']
        team_players = [p for p in players if p['league'] == league]
        print(f"   {league} ({len(teams)} teams): {len(team_players)} players")
        for team in teams:
            team_count = len([p for p in players if p['team_name'] == team])
            print(f"      - {team}: {team_count} players")

    print(f"\n💰 Value Distribution:")
    ranges = {
        "€45-50 (Superstars)": sum(1 for p in players if p['fantasy_value'] >= 45),
        "€40-45 (Premium)": sum(1 for p in players if 40 <= p['fantasy_value'] < 45),
        "€35-40 (Solid)": sum(1 for p in players if 35 <= p['fantasy_value'] < 40),
        "€30-35 (Average)": sum(1 for p in players if 30 <= p['fantasy_value'] < 35),
        "€25-30 (Budget)": sum(1 for p in players if 25 <= p['fantasy_value'] < 30),
        "€20-25 (Rookies)": sum(1 for p in players if p['fantasy_value'] < 25),
    }

    for range_name, count in ranges.items():
        print(f"   {range_name}: {count} players")

    print(f"\n🌟 Top 20 Most Valuable Players:")
    for i, player in enumerate(players[:20], 1):
        print(f"   {i:2d}. {player['name']:<25} €{player['fantasy_value']:.1f} ({player['team_name']:<15}) - {player['stats']['runs']}r/{player['stats']['wickets']}w")

    print(f"\n💎 Best Value Players by League:")
    for league in roster['leagues'].keys():
        league_players = [p for p in players if p['league'] == league]
        if league_players:
            best = league_players[0]  # Already sorted by value
            print(f"   {league:<20} {best['name']:<25} €{best['fantasy_value']:.1f}")

    print("\n" + "=" * 80)


def main():
    print("\n🏗️  Complete ACC Roster Builder - All Leagues")
    print("=" * 80)

    # Generate roster
    roster = create_complete_acc_roster()

    # Save to file
    output_file = "rosters/acc_2025_complete_all_leagues.json"
    with open(output_file, 'w') as f:
        json.dump(roster, f, indent=2)

    print(f"\n✅ Roster saved to {output_file}")

    # Print summary
    print_roster_summary(roster)

    print(f"\n✅ Complete! You now have {roster['total_players']} ACC players ready")
    print(f"   - All leagues covered (Hoofdklasse → ZAMI + Youth)")
    print(f"   - {len(roster['leagues'])} different leagues")
    print(f"   - Values range €20-€50")
    print(f"   - Mix of batsmen, bowlers, all-rounders, keepers")
    print(f"   - Ready for 11-player fantasy team selection!")


if __name__ == "__main__":
    main()
