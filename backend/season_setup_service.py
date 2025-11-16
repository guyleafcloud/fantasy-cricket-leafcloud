#!/usr/bin/env python3
"""
Season Setup Service
===================
Service for admin season setup operations including loading legacy rosters.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database_models import Season, Club, Team, Player, PlayerPriceHistory
from player_value_calculator import PlayerValueCalculator

logger = logging.getLogger(__name__)


class SeasonSetupService:
    """
    Service for setting up new seasons and loading legacy rosters
    """

    # Tier multipliers for different team levels
    TIER_MULTIPLIERS = {
        "1st": 1.0,
        "2nd": 1.1,
        "3rd": 1.2,
        "4th": 1.25,
        "social": 1.3
    }

    def __init__(self, db: Session):
        self.db = db
        self.value_calculator = PlayerValueCalculator()

    # =========================================================================
    # SEASON MANAGEMENT
    # =========================================================================

    def create_season(
        self,
        year: str,
        name: str,
        start_date: datetime,
        end_date: datetime,
        created_by: str,
        description: Optional[str] = None,
        activate: bool = False
    ) -> Season:
        """
        Create a new season.

        Args:
            year: Season year (e.g., "2026")
            name: Season name (e.g., "Topklasse 2026")
            start_date: Season start date
            end_date: Season end date
            created_by: Admin user ID
            description: Optional description
            activate: Automatically activate this season

        Returns:
            Created Season object
        """
        logger.info(f"Creating season {year}: {name}")

        # Check if season already exists
        existing = self.db.query(Season).filter_by(year=year).first()
        if existing:
            raise ValueError(f"Season {year} already exists")

        # Create season
        season = Season(
            year=year,
            name=name,
            start_date=start_date,
            end_date=end_date,
            description=description,
            is_active=False,
            registration_open=False,
            scraping_enabled=False,
            created_by=created_by
        )

        self.db.add(season)
        self.db.flush()

        logger.info(f"✅ Season created: {season.id}")

        # Activate if requested
        if activate:
            self.activate_season(season.id)

        return season

    def activate_season(self, season_id: str) -> Season:
        """
        Activate a season (deactivates all others).

        Args:
            season_id: Season to activate

        Returns:
            Activated Season object
        """
        logger.info(f"Activating season {season_id}")

        # Deactivate all seasons
        self.db.query(Season).update({
            "is_active": False,
            "registration_open": False,
            "scraping_enabled": False
        })

        # Activate this season
        season = self.db.query(Season).filter_by(id=season_id).first()
        if not season:
            raise ValueError(f"Season {season_id} not found")

        season.is_active = True
        season.registration_open = True
        season.scraping_enabled = True

        self.db.flush()

        logger.info(f"✅ Season {season.year} activated")
        return season

    def get_active_season(self) -> Optional[Season]:
        """Get the currently active season"""
        return self.db.query(Season).filter_by(is_active=True).first()

    # =========================================================================
    # CLUB & TEAM MANAGEMENT
    # =========================================================================

    def create_club(
        self,
        season_id: str,
        name: str,
        full_name: str,
        country: str = "Netherlands",
        cricket_board: str = "KNCB",
        website_url: Optional[str] = None
    ) -> Club:
        """
        Create a new club for a season.

        Args:
            season_id: Season ID
            name: Short name (e.g., "ACC")
            full_name: Full name (e.g., "Amsterdamsche Cricket Club")
            country: Country
            cricket_board: Cricket board
            website_url: Optional website URL

        Returns:
            Created Club object
        """
        logger.info(f"Creating club {name} for season {season_id}")

        # Check if club already exists in this season
        existing = self.db.query(Club).filter_by(
            season_id=season_id,
            name=name
        ).first()
        if existing:
            raise ValueError(f"Club {name} already exists in this season")

        # Create club
        club = Club(
            season_id=season_id,
            name=name,
            full_name=full_name,
            country=country,
            cricket_board=cricket_board,
            website_url=website_url
        )

        self.db.add(club)
        self.db.flush()

        logger.info(f"✅ Club created: {club.id}")
        return club

    def create_teams_for_club(self, club_id: str) -> List[Team]:
        """
        Create standard teams for a club (1st, 2nd, 3rd, social).

        Args:
            club_id: Club ID

        Returns:
            List of created Team objects
        """
        logger.info(f"Creating teams for club {club_id}")

        club = self.db.query(Club).filter_by(id=club_id).first()
        if not club:
            raise ValueError(f"Club {club_id} not found")

        teams_config = [
            {"name": f"{club.name} 1", "level": "1st", "value_multiplier": 1.0},
            {"name": f"{club.name} 2", "level": "2nd", "value_multiplier": 1.1},
            {"name": f"{club.name} 3", "level": "3rd", "value_multiplier": 1.2},
            {"name": f"{club.name} Social", "level": "social", "value_multiplier": 1.3},
        ]

        teams = []
        for config in teams_config:
            team = Team(
                club_id=club_id,
                name=config["name"],
                level=config["level"],
                value_multiplier=config["value_multiplier"],
                tier_type="senior"
            )
            self.db.add(team)
            teams.append(team)

        self.db.flush()

        logger.info(f"✅ Created {len(teams)} teams for {club.name}")
        return teams

    # =========================================================================
    # LEGACY ROSTER LOADING
    # =========================================================================

    def load_legacy_roster(
        self,
        club_id: str,
        roster_file_path: str,
        recalculate_values: bool = False
    ) -> Dict:
        """
        Load legacy roster from JSON file into database.

        Args:
            club_id: Club to load players into
            roster_file_path: Path to roster JSON file
            recalculate_values: If True, recalculate values instead of using file values

        Returns:
            Dictionary with loading statistics
        """
        logger.info(f"Loading legacy roster for club {club_id}")
        logger.info(f"   File: {roster_file_path}")

        # Load JSON
        with open(roster_file_path, 'r') as f:
            roster_data = json.load(f)

        # Get club
        club = self.db.query(Club).filter_by(id=club_id).first()
        if not club:
            raise ValueError(f"Club {club_id} not found")

        # Get or create teams - map by team name
        teams_by_name = {}
        for team in club.teams:
            teams_by_name[team.name] = team

        # If no teams exist, create them
        if not teams_by_name:
            created_teams = self.create_teams_for_club(club_id)
            for team in created_teams:
                teams_by_name[team.name] = team

        # Load players
        players_loaded = 0
        players_skipped = 0
        total_value = 0.0

        for player_data in roster_data.get('players', []):
            try:
                # Check if player already exists
                existing = self.db.query(Player).filter_by(
                    club_id=club_id,
                    name=player_data['name']
                ).first()

                if existing:
                    logger.debug(f"   Skipping existing player: {player_data['name']}")
                    players_skipped += 1
                    continue

                # Get team by mapping team_name from JSON
                team_name_raw = player_data.get('team_name', 'ACC 1')

                # Normalize team name (e.g., "ACC U17" -> "U17", "ACC 3" -> "ACC 3", "ACC ZAMI" -> "ZAMI 1")
                # Map team names from JSON to database team names
                team_name_map = {
                    "ACC U17": "U17",
                    "ACC U15": "U15",
                    "ACC U13": "U13",
                    "ACC ZAMI": "ZAMI 1",  # Default to ZAMI 1
                    "ACC 1": "ACC 1",
                    "ACC 2": "ACC 2",
                    "ACC 3": "ACC 3",
                    "ACC 4": "ACC 4",
                    "ACC 5": "ACC 5",
                    "ACC 6": "ACC 6"
                }

                team_name = team_name_map.get(team_name_raw, team_name_raw)
                team = teams_by_name.get(team_name)

                if not team:
                    # Try without club prefix
                    for t_name, t_obj in teams_by_name.items():
                        if team_name_raw.endswith(t_name) or t_name in team_name_raw:
                            team = t_obj
                            break

                if not team:
                    logger.warning(f"   No team found for {team_name_raw}, skipping player {player_data['name']}")
                    players_skipped += 1
                    continue

                # Get multiplier from legacy data (range: 0.69-5.0, with 1.0 = median)
                # Lower multiplier = better player but points are multiplied by less
                # Higher multiplier = worse player but points are multiplied by more
                multiplier = player_data.get('multiplier', 1.0)

                # Create player
                player = Player(
                    club_id=club_id,
                    team_id=team.id,
                    name=player_data['name'],
                    multiplier=multiplier,
                    multiplier_updated_at=datetime.utcnow(),
                    fantasy_value=25.0,  # Deprecated, not used in multiplier system
                    stats=player_data.get('stats', {}),
                    is_wicket_keeper=player_data.get('is_wicket_keeper', False),
                    legacy_player_id=player_data.get('player_id'),
                    value_calculation_date=datetime.utcnow(),
                    value_manually_adjusted=False
                )

                self.db.add(player)
                self.db.flush()  # Flush to get player.id

                # Create price history entry
                price_history = PlayerPriceHistory(
                    player_id=player.id,
                    old_value=0.0,
                    new_value=player.fantasy_value,
                    change_reason="initial",
                    reason_details="Loaded from legacy roster"
                )
                self.db.add(price_history)

                players_loaded += 1
                total_value += player.fantasy_value

            except Exception as e:
                logger.error(f"   Error loading player {player_data.get('name')}: {e}")
                players_skipped += 1

        self.db.flush()

        avg_value = total_value / players_loaded if players_loaded > 0 else 0

        result = {
            "club": club.name,
            "roster_file": roster_file_path,
            "players_loaded": players_loaded,
            "players_skipped": players_skipped,
            "total_players": players_loaded,
            "average_value": round(avg_value, 2),
            "total_value": round(total_value, 2)
        }

        logger.info(f"✅ Legacy roster loaded:")
        logger.info(f"   Loaded: {players_loaded} players")
        logger.info(f"   Skipped: {players_skipped} players")
        logger.info(f"   Average value: €{avg_value:.2f}")

        return result

    # =========================================================================
    # PLAYER VALUE MANAGEMENT
    # =========================================================================

    def update_player_value(
        self,
        player_id: str,
        new_value: float,
        reason: str,
        changed_by: Optional[str] = None
    ) -> Player:
        """
        Manually update a player's fantasy value.

        Args:
            player_id: Player ID
            new_value: New value (€20-€50)
            reason: Reason for change
            changed_by: Admin user ID

        Returns:
            Updated Player object
        """
        player = self.db.query(Player).filter_by(id=player_id).first()
        if not player:
            raise ValueError(f"Player {player_id} not found")

        old_value = player.fantasy_value

        # Update player
        player.fantasy_value = new_value
        player.value_manually_adjusted = True
        player.value_adjustment_reason = reason

        # Record price history
        price_history = PlayerPriceHistory(
            player_id=player_id,
            old_value=old_value,
            new_value=new_value,
            change_reason="manual",
            reason_details=reason,
            changed_by=changed_by
        )
        self.db.add(price_history)

        self.db.flush()

        logger.info(f"✅ Player value updated: {player.name} €{old_value:.1f} → €{new_value:.1f}")

        return player

    def add_player_manually(
        self,
        club_id: str,
        team_level: str,
        name: str,
        fantasy_value: float = 25.0,
        stats: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> Player:
        """
        Manually add a new player to the club.

        Args:
            club_id: Club ID
            team_level: Team level (1st, 2nd, 3rd, social)
            name: Player name
            fantasy_value: Initial value
            stats: Optional stats dictionary
            created_by: Admin user ID

        Returns:
            Created Player object
        """
        # Get club and team
        club = self.db.query(Club).filter_by(id=club_id).first()
        if not club:
            raise ValueError(f"Club {club_id} not found")

        team = self.db.query(Team).filter_by(
            club_id=club_id,
            level=team_level
        ).first()

        if not team:
            raise ValueError(f"Team {team_level} not found for club {club.name}")

        # Check for duplicate
        existing = self.db.query(Player).filter_by(
            club_id=club_id,
            name=name
        ).first()
        if existing:
            raise ValueError(f"Player {name} already exists in {club.name}")

        # Create player
        player = Player(
            club_id=club_id,
            team_id=team.id,
            name=name,
            fantasy_value=fantasy_value,
            stats=stats or {},
            value_manually_adjusted=True,
            value_adjustment_reason="Manually added",
            created_by=created_by
        )

        self.db.add(player)

        # Record price history
        price_history = PlayerPriceHistory(
            player_id=player.id,
            old_value=0.0,
            new_value=fantasy_value,
            change_reason="manual",
            reason_details="Manually added player",
            changed_by=created_by
        )
        self.db.add(price_history)

        self.db.flush()

        logger.info(f"✅ Player added: {name} (€{fantasy_value:.1f}) to {team.name}")

        return player

    # =========================================================================
    # COMPLETE SEASON SETUP WORKFLOW
    # =========================================================================

    def setup_season_with_club(
        self,
        year: str,
        season_name: str,
        start_date: datetime,
        end_date: datetime,
        club_name: str,
        club_full_name: str,
        roster_file_path: str,
        created_by: str,
        activate: bool = True
    ) -> Dict:
        """
        Complete workflow: Create season, club, teams, and load roster.

        Args:
            year: Season year (e.g., "2026")
            season_name: Season name
            start_date: Season start
            end_date: Season end
            club_name: Club short name (e.g., "ACC")
            club_full_name: Club full name
            roster_file_path: Path to legacy roster JSON
            created_by: Admin user ID
            activate: Activate season after setup

        Returns:
            Dictionary with setup results
        """
        logger.info(f"🏗️  Setting up season {year} with club {club_name}")

        # 1. Create season
        season = self.create_season(
            year=year,
            name=season_name,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            activate=False  # Activate at the end
        )

        # 2. Create club
        club = self.create_club(
            season_id=season.id,
            name=club_name,
            full_name=club_full_name
        )

        # 3. Create teams
        teams = self.create_teams_for_club(club.id)

        # 4. Load roster
        roster_result = self.load_legacy_roster(
            club_id=club.id,
            roster_file_path=roster_file_path
        )

        # 5. Activate season if requested
        if activate:
            self.activate_season(season.id)

        result = {
            "season": {
                "id": season.id,
                "year": season.year,
                "name": season.name,
                "is_active": season.is_active
            },
            "club": {
                "id": club.id,
                "name": club.name,
                "teams_count": len(teams)
            },
            "roster": roster_result
        }

        logger.info(f"✅ Season setup complete!")
        logger.info(f"   Season: {season.year}")
        logger.info(f"   Club: {club.name}")
        logger.info(f"   Teams: {len(teams)}")
        logger.info(f"   Players: {roster_result['players_loaded']}")

        return result


# =============================================================================
# MAIN - Test the service
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from database import get_db_session, init_db

    print("\n🏏 Season Setup Service Test\n")

    # Initialize database
    init_db()

    with get_db_session() as db:
        service = SeasonSetupService(db)

        # Setup 2026 season with ACC
        result = service.setup_season_with_club(
            year="2026",
            season_name="Topklasse 2026",
            start_date=datetime(2026, 4, 1),
            end_date=datetime(2026, 9, 30),
            club_name="ACC",
            club_full_name="Amsterdamsche Cricket Club",
            roster_file_path="rosters/acc_2025_complete.json",
            created_by="admin_test",
            activate=True
        )

        print("\n✅ Setup complete!")
        print(f"   Season ID: {result['season']['id']}")
        print(f"   Club ID: {result['club']['id']}")
        print(f"   Players loaded: {result['roster']['players_loaded']}")
