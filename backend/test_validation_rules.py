"""
Test validation rules directly in backend
"""
from database_models import User, League, Player, FantasyTeam, FantasyTeamPlayer
from database import SessionLocal
from collections import Counter

db = SessionLocal()

print("=" * 60)
print("TESTING VALIDATION RULES")
print("=" * 60)

# Find existing team
team = db.query(FantasyTeam).filter(FantasyTeam.team_name == 'testing').first()

if not team:
    print("No 'testing' team found")
    db.close()
    exit(1)

print(f"\nTeam: {team.team_name}")
print(f"League: {team.league.name if team.league else 'None'}")
print(f"Players in team: {len(team.players)}")

# Get league rules
league = team.league
if league:
    print(f"\nLeague Rules:")
    print(f"  squad_size: {league.squad_size}")
    print(f"  min_batsmen: {league.min_batsmen}")
    print(f"  min_bowlers: {league.min_bowlers}")
    print(f"  max_players_per_team: {league.max_players_per_team}")
    print(f"  require_from_each_team: {league.require_from_each_team}")
    print(f"  min_players_per_team: {league.min_players_per_team}")

    # Count RL teams in club
    from sqlalchemy import func
    total_rl_teams = db.query(func.count(func.distinct(Player.rl_team)))\
        .filter(Player.club_id == league.club_id, Player.rl_team.isnot(None))\
        .scalar()
    print(f"  Total RL teams in club: {total_rl_teams}")

# Analyze current team composition
print(f"\n Current Team Composition:")

# By RL team
team_counts = Counter()
unique_teams = set()
for ftp in team.players:
    if ftp.player and ftp.player.rl_team:
        team_counts[ftp.player.rl_team] += 1
        unique_teams.add(ftp.player.rl_team)

print(f"  Players by RL team:")
for rl_team, count in sorted(team_counts.items()):
    print(f"    {rl_team}: {count} player(s)")

# By role
role_counts = {'BATSMAN': 0, 'BOWLER': 0, 'ALL_ROUNDER': 0, 'WICKET_KEEPER': 0}
batsmen_count = 0
bowlers_count = 0
for ftp in team.players:
    if ftp.player:
        role = ftp.player.role
        if role in role_counts:
            role_counts[role] += 1
        if role in ['BATSMAN', 'ALL_ROUNDER']:
            batsmen_count += 1
        if role in ['BOWLER', 'ALL_ROUNDER']:
            bowlers_count += 1

print(f"  Players by role:")
for role, count in role_counts.items():
    print(f"    {role}: {count}")
print(f"  Effective batsmen: {batsmen_count} (ALL_ROUNDERS count as both)")
print(f"  Effective bowlers: {bowlers_count} (ALL_ROUNDERS count as both)")

# Validation checks
print(f"\nValidation Results:")

# Squad size
if len(team.players) == league.squad_size:
    print(f"  ✅ Squad size: {len(team.players)}/{league.squad_size}")
else:
    print(f"  ❌ Squad size: {len(team.players)}/{league.squad_size} (incomplete)")

# Min batsmen
if batsmen_count >= league.min_batsmen:
    print(f"  ✅ Min batsmen: {batsmen_count}/{league.min_batsmen}")
else:
    print(f"  ❌ Min batsmen: {batsmen_count}/{league.min_batsmen}")

# Min bowlers
if bowlers_count >= league.min_bowlers:
    print(f"  ✅ Min bowlers: {bowlers_count}/{league.min_bowlers}")
else:
    print(f"  ❌ Min bowlers: {bowlers_count}/{league.min_bowlers}")

# Wicketkeeper
if role_counts['WICKET_KEEPER'] >= 1:
    print(f"  ✅ Wicketkeeper: {role_counts['WICKET_KEEPER']}")
else:
    print(f"  ❌ Wicketkeeper: {role_counts['WICKET_KEEPER']} (need at least 1)")

# Max players per team
max_per_team_ok = True
for rl_team, count in team_counts.items():
    if count > league.max_players_per_team:
        print(f"  ❌ Max players per team: {rl_team} has {count} (max {league.max_players_per_team})")
        max_per_team_ok = False
if max_per_team_ok:
    print(f"  ✅ Max players per team: All teams within limit ({league.max_players_per_team})")

# Require from each team
if league.require_from_each_team:
    if len(unique_teams) >= total_rl_teams:
        print(f"  ✅ Require from each team: {len(unique_teams)}/{total_rl_teams} teams represented")
    else:
        missing_teams = total_rl_teams - len(unique_teams)
        print(f"  ❌ Require from each team: {len(unique_teams)}/{total_rl_teams} teams (missing {missing_teams})")

        # Show which teams are missing
        all_rl_teams = db.query(Player.rl_team).filter(
            Player.club_id == league.club_id,
            Player.rl_team.isnot(None)
        ).distinct().all()
        all_rl_teams = {t[0] for t in all_rl_teams}
        missing = all_rl_teams - unique_teams
        if missing:
            print(f"      Missing teams: {sorted(missing)}")

db.close()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
