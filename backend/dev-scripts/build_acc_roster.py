#!/usr/bin/env python3
"""
ACC Complete Roster Builder
============================
Builds a comprehensive ACC roster across all teams (1st, 2nd, 3rd, social).

This creates a realistic roster with:
- 15-20 players per team
- 4-5 teams (ACC 1, ACC 2, ACC 3, etc.)
- Varied performance profiles
- Calculated fantasy values

Based on typical Dutch club cricket structure.
"""

import json
import random
from typing import List, Dict
from player_value_calculator import PlayerValueCalculator, PlayerStats

# Seed for reproducibility
random.seed(42)


def generate_player_stats(
    name: str,
    club: str,
    team_level: str,
    player_type: str = "all-rounder",
    skill_level: str = "average"
) -> PlayerStats:
    """
    Generate realistic player stats based on type and skill level

    Args:
        name: Player name
        club: Club name (ACC)
        team_level: 1st, 2nd, 3rd, or social
        player_type: batsman, bowler, all-rounder, wicket-keeper
        skill_level: elite, good, average, developing
    """

    # Base matches by team level
    matches_by_level = {
        "1st": (10, 15),
        "2nd": (8, 12),
        "3rd": (6, 10),
        "social": (5, 8)
    }

    matches = random.randint(*matches_by_level.get(team_level, (5, 10)))

    # Skill multipliers
    skill_multipliers = {
        "elite": 1.5,
        "good": 1.2,
        "average": 1.0,
        "developing": 0.7
    }
    multiplier = skill_multipliers.get(skill_level, 1.0)

    # Generate stats based on player type
    stats = PlayerStats(
        player_name=name,
        club=club,
        matches_played=matches,
        team_level=team_level
    )

    if player_type in ["batsman", "all-rounder", "wicket-keeper"]:
        # Batting stats
        base_runs = random.randint(150, 600)
        stats.total_runs = int(base_runs * multiplier)
        stats.batting_average = round(stats.total_runs / max(1, matches - 2), 1)
        stats.strike_rate = round(random.uniform(80, 150) * multiplier, 1)
        stats.fours = int(stats.total_runs / 6)
        stats.sixes = int(stats.total_runs / 30)

        if stats.total_runs > 400:
            stats.fifties = random.randint(2, 4)
        if stats.total_runs > 500:
            stats.hundreds = random.randint(1, 2)

    if player_type in ["bowler", "all-rounder"]:
        # Bowling stats
        base_wickets = random.randint(8, 35)
        stats.total_wickets = int(base_wickets * multiplier)
        stats.total_overs_bowled = round(matches * random.uniform(6, 10), 1)
        stats.bowling_average = round(random.uniform(15, 35) / multiplier, 1)
        stats.economy_rate = round(random.uniform(3.5, 6.5) / multiplier, 2)
        stats.total_runs_conceded = int(stats.total_overs_bowled * stats.economy_rate)

        if stats.total_wickets > 25:
            stats.five_wicket_hauls = random.randint(1, 2)

        stats.maidens = int(stats.total_overs_bowled / 10)

    # Fielding (everyone fields)
    stats.catches = random.randint(2, 12)
    stats.run_outs = random.randint(0, 3)

    if player_type == "wicket-keeper":
        stats.catches = random.randint(8, 20)
        stats.stumpings = random.randint(1, 5)

    return stats


def create_acc_complete_roster() -> Dict:
    """
    Create complete ACC roster with all teams
    """

    # ACC Team Structure
    teams = {
        "1st": {
            "name": "ACC 1 (Topklasse)",
            "player_count": 18,
            "skill_distribution": {
                "elite": 3,
                "good": 8,
                "average": 7
            }
        },
        "2nd": {
            "name": "ACC 2 (Hoofdklasse)",
            "player_count": 16,
            "skill_distribution": {
                "good": 4,
                "average": 10,
                "developing": 2
            }
        },
        "3rd": {
            "name": "ACC 3 (Eerste Klasse)",
            "player_count": 15,
            "skill_distribution": {
                "average": 8,
                "developing": 7
            }
        },
        "social": {
            "name": "ACC Social",
            "player_count": 12,
            "skill_distribution": {
                "average": 4,
                "developing": 8
            }
        }
    }

    # Dutch/International names for realism
    first_names = [
        "Boris", "Sikander", "Shariz", "Musa", "Saqib", "Asad", "Kashif",
        "Roel", "Victor", "Olivier", "Sebastiaan", "Arnav", "Jitse", "Niels",
        "Tom", "Quirijn", "Daniel", "Sjoerd", "Robin", "Mitchell", "Julian",
        "Tobias", "Maarten", "Rohan", "Tim", "Lars", "Daan", "Bram", "Jasper",
        "Finn", "Lucas", "Max", "Noah", "Levi", "Sem", "Milan", "Luuk",
        "Jayden", "Ryan", "Thijs", "Jesse", "Thomas", "Ruben", "Stijn",
        "Imran", "Hassan", "Ali", "Omar", "Bilal", "Hamza", "Tariq",
        "Pradeep", "Raj", "Arun", "Vikram", "Rahul", "Amit", "Suresh"
    ]

    last_names = [
        "Gorlee", "Zulfiqar", "Ahmad", "Naseem", "Verhagen", "Lubbers",
        "Elenbaas", "Braat", "Jain", "Wilders", "Etman", "de Grooth",
        "Gunning", "Watson", "Stolk", "van Manen", "Koot", "de Mey",
        "Visee", "Boers", "Chopra", "Gruijters", "van der Berg", "Bakker",
        "Jansen", "Smit", "de Vries", "van Dijk", "Mulder", "Bos",
        "Khan", "Patel", "Singh", "Sharma", "Kumar", "Reddy", "Rao",
        "van Leeuwen", "de Jong", "Hendriks", "van den Berg", "Peters"
    ]

    all_players = []
    player_stats_list = []

    calculator = PlayerValueCalculator()

    print("\n🏏 Building Complete ACC Roster\n")
    print("=" * 80)

    # Generate players for each team
    for team_level, team_info in teams.items():
        print(f"\n📋 {team_info['name']}")
        print(f"   Target: {team_info['player_count']} players")

        team_players = []
        skill_levels = []

        # Build skill level list
        for skill, count in team_info['skill_distribution'].items():
            skill_levels.extend([skill] * count)

        # Generate players
        for i in range(team_info['player_count']):
            # Create unique name
            first = random.choice(first_names)
            last = random.choice(last_names)
            name = f"{first} {last}"

            # Avoid duplicates
            while name in [p['name'] for p in all_players]:
                first = random.choice(first_names)
                last = random.choice(last_names)
                name = f"{first} {last}"

            # Determine player type
            if i < 2:
                player_type = "wicket-keeper"
            elif i < 8:
                player_type = "batsman"
            elif i < 14:
                player_type = "all-rounder"
            else:
                player_type = "bowler"

            # Get skill level
            skill = skill_levels[i] if i < len(skill_levels) else "average"

            # Generate stats
            stats = generate_player_stats(name, "ACC", team_level, player_type, skill)
            player_stats_list.append(stats)

            team_players.append({
                "name": name,
                "team_level": team_level,
                "player_type": player_type,
                "skill_level": skill
            })

        print(f"   ✅ Generated {len(team_players)} players")

    # Calculate values for all players
    print(f"\n💰 Calculating fantasy values...")
    results = calculator.calculate_team_values(player_stats_list)

    # Build final roster
    roster = {
        "club": "ACC",
        "season": "2025",
        "created_at": "2025-11-05",
        "notes": "Complete ACC roster across all teams (manually generated for season setup)",
        "total_players": len(player_stats_list),
        "teams": {
            "1st": teams["1st"]["player_count"],
            "2nd": teams["2nd"]["player_count"],
            "3rd": teams["3rd"]["player_count"],
            "social": teams["social"]["player_count"]
        },
        "players": []
    }

    for i, (stats, value, justification) in enumerate(results):
        player_entry = {
            "player_id": f"acc_2025_{i+1:03d}",
            "name": stats.player_name,
            "club": "ACC",
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
    """Print summary of generated roster"""
    players = roster['players']

    print("\n" + "=" * 80)
    print(f"🏏 ACC Complete Roster Summary")
    print("=" * 80)
    print(f"\nTotal Players: {roster['total_players']}")
    print(f"Season: {roster['season']}")

    print(f"\n📊 Team Distribution:")
    for team, count in roster['teams'].items():
        print(f"   {team}: {count} players")

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

    print(f"\n🌟 Top 15 Most Valuable Players:")
    for i, player in enumerate(players[:15], 1):
        print(f"   {i:2d}. {player['name']:<25} €{player['fantasy_value']:.1f} ({player['team_level']}) - {player['stats']['runs']}r/{player['stats']['wickets']}w")

    print(f"\n💎 Best Value Budget Players (€20-25):")
    budget_players = [p for p in players if p['fantasy_value'] < 25]
    for i, player in enumerate(budget_players[:10], 1):
        print(f"   {i:2d}. {player['name']:<25} €{player['fantasy_value']:.1f} ({player['team_level']}) - {player['stats']['runs']}r/{player['stats']['wickets']}w")

    print("\n" + "=" * 80)


def main():
    print("\n🏗️  ACC Complete Roster Builder")
    print("=" * 80)

    # Generate roster
    roster = create_acc_complete_roster()

    # Save to file
    output_file = "rosters/acc_2025_complete.json"
    with open(output_file, 'w') as f:
        json.dump(roster, f, indent=2)

    print(f"\n✅ Roster saved to {output_file}")

    # Print summary
    print_roster_summary(roster)

    print(f"\n✅ Complete! You now have {roster['total_players']} ACC players ready for season setup")
    print(f"   - All teams covered (1st, 2nd, 3rd, social)")
    print(f"   - Values range €20-€50")
    print(f"   - Mix of batsmen, bowlers, all-rounders, keepers")
    print(f"   - Ready for fantasy team selection!")


if __name__ == "__main__":
    main()
