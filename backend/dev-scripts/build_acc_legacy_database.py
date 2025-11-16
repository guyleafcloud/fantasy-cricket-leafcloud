#!/usr/bin/env python3
"""
Build ACC Legacy Database
=========================
One-time script to build the initial ACC player database from known scorecards.
Extracts player names and Match Centre IDs.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple
from playwright.async_api import async_playwright

from player_aggregator import PlayerSeasonAggregator
from player_value_calculator import PlayerValueCalculator, PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def split_camel_case(name: str) -> List[str]:
    """Split CamelCase name into words: 'IrfanAlim' -> ['Irfan', 'Alim']"""
    # Handle names with spaces first (like "Caroline ALange")
    if ' ' in name:
        return name.split()

    # Split on capital letters
    words = re.findall(r'[A-Z][a-z]*', name)
    return words


def create_abbreviated_name(full_name: str) -> str:
    """
    Convert full name to abbreviated scorecard format.
    'IrfanAlim' -> 'I ALIM'
    'HarrySingh' -> 'H SINGH'
    'Caroline ALange' -> 'C ALANGE'
    """
    words = split_camel_case(full_name)
    if len(words) >= 2:
        # First initial + last name(s)
        first_initial = words[0][0].upper()
        last_names = ' '.join(words[1:]).upper()
        return f"{first_initial} {last_names}"
    return full_name.upper()


# Manual mapping of scorecard URLs to team names
# This ensures correct team assignment when page text has ambiguous numbers
SCORECARD_TEAM_MAP = {
    # ACC 1 - Hoofdklasse (18 matches)
    "7254567": "ACC 1",
    "7254572": "ACC 1",
    "7254577": "ACC 1",
    "7254582": "ACC 1",
    "7254587": "ACC 1",
    "7254592": "ACC 1",
    "7254597": "ACC 1",
    "7254602": "ACC 1",
    "7254607": "ACC 1",
    "7258314": "ACC 1",
    "7258315": "ACC 1",
    "7258320": "ACC 1",
    "7258325": "ACC 1",
    "7258330": "ACC 1",
    "7258335": "ACC 1",
    "7258340": "ACC 1",
    "7258345": "ACC 1",
    "7258350": "ACC 1",

    # ACC 2 - Tweede Klasse (14 matches)
    "7323305": "ACC 2",
    "7323309": "ACC 2",
    "7323327": "ACC 2",
    "7323330": "ACC 2",
    "7323334": "ACC 2",
    "7323338": "ACC 2",
    "7323347": "ACC 2",
    "7323351": "ACC 2",
    "7323354": "ACC 2",
    "7323359": "ACC 2",
    "7323344": "ACC 2",
    "7323322": "ACC 2",
    "7323303": "ACC 2",
    "7323293": "ACC 2",

    # ACC 3 - Derde Klasse (14 matches)
    "7324739": "ACC 3",
    "7324742": "ACC 3",
    "7324747": "ACC 3",
    "7324749": "ACC 3",
    "7324755": "ACC 3",
    "7324760": "ACC 3",
    "7324763": "ACC 3",
    "7324766": "ACC 3",
    "7324770": "ACC 3",
    "7324777": "ACC 3",
    "7324784": "ACC 3",
    "7324787": "ACC 3",
    "7324791": "ACC 3",
    "7324776": "ACC 3",

    # ACC 4 - Derde Klasse (14 matches)
    "7324800": "ACC 4",
    "7324801": "ACC 4",
    "7324808": "ACC 4",
    "7324815": "ACC 4",
    "7324817": "ACC 4",
    "7324823": "ACC 4",
    "7324828": "ACC 4",
    "7324836": "ACC 4",
    "7324837": "ACC 4",
    "7324829": "ACC 4",
    "7324795": "ACC 4",
    "7324844": "ACC 4",
    "7324848": "ACC 4",
    "7324809": "ACC 4",

    # ACC 5 - Vierde Klasse (13 matches)
    "7326156": "ACC 5",
    "7326162": "ACC 5",
    "7326166": "ACC 5",
    "7326170": "ACC 5",
    "7326173": "ACC 5",
    "7326177": "ACC 5",
    "7326183": "ACC 5",
    "7326186": "ACC 5",
    "7326195": "ACC 5",
    "7326199": "ACC 5",
    "7326203": "ACC 5",
    "7326207": "ACC 5",
    "7326192": "ACC 5",

    # ACC 6 - Vierde Klasse (15 matches)
    "7326066": "ACC 6",
    "7326073": "ACC 6",
    "7326075": "ACC 6",
    "7326082": "ACC 6",
    "7326086": "ACC 6",
    "7326093": "ACC 6",
    "7326097": "ACC 6",
    "7326102": "ACC 6",
    "7326120": "ACC 6",
    "7326121": "ACC 6",
    "7326130": "ACC 6",
    "7326132": "ACC 6",
    "7326139": "ACC 6",
    "7326143": "ACC 6",
    "7326148": "ACC 6",

    # ACC ZAMI (18 matches - players randomly split into ZAMI 1 and ZAMI 2 each week)
    "7332092": "ACC ZAMI",
    "7332265": "ACC ZAMI",
    "7332269": "ACC ZAMI",
    "7332277": "ACC ZAMI",
    "7332287": "ACC ZAMI",
    "7332115": "ACC ZAMI",
    "7332119": "ACC ZAMI",
    "7332299": "ACC ZAMI",
    "7332129": "ACC ZAMI",
    "7332305": "ACC ZAMI",
    "7332101": "ACC ZAMI",
    "7332315": "ACC ZAMI",
    "7332316": "ACC ZAMI",
    "7332095": "ACC ZAMI",
    "7332122": "ACC ZAMI",
    "7332309": "ACC ZAMI",
    "7332274": "ACC ZAMI",
    "7332302": "ACC ZAMI",

    # ACC U17 (10 matches)
    "7329152": "ACC U17",
    "7329153": "ACC U17",
    "7329157": "ACC U17",
    "7329168": "ACC U17",
    "7329170": "ACC U17",
    "7329172": "ACC U17",
    "7329159": "ACC U17",
    "7329176": "ACC U17",
    "7329179": "ACC U17",
    "7393900": "ACC U17",

    # ACC U15 (11 matches)
    "7331235": "ACC U15",
    "7331237": "ACC U15",
    "7331240": "ACC U15",
    "7331246": "ACC U15",
    "7331249": "ACC U15",
    "7331253": "ACC U15",
    "7331256": "ACC U15",
    "7331262": "ACC U15",
    "7393853": "ACC U15",
    "7395417": "ACC U15",
    "7397066": "ACC U15",

    # ACC U13 (8 matches)
    "7336247": "ACC U13",
    "7336254": "ACC U13",
    "7336258": "ACC U13",
    "7336263": "ACC U13",
    "7336272": "ACC U13",
    "7336280": "ACC U13",
    "7336281": "ACC U13",
    "7336290": "ACC U13",
}

# Add more scorecard URLs as you discover them
KNOWN_SCORECARDS = [
    # ACC 1 - Hoofdklasse (18 matches)
    "https://matchcentre.kncb.nl/match/134453-7254567/scorecard/?period=2821921",
    "https://matchcentre.kncb.nl/match/134453-7254572/scorecard/?period=2841578",
    "https://matchcentre.kncb.nl/match/134453-7254577/scorecard/?period=2854160",
    "https://matchcentre.kncb.nl/match/134453-7254582/scorecard/?period=2871713",
    "https://matchcentre.kncb.nl/match/134453-7254587/scorecard/?period=2904089",
    "https://matchcentre.kncb.nl/match/134453-7254592/scorecard/?period=2933951",
    "https://matchcentre.kncb.nl/match/134453-7254597/scorecard/?period=2957934",
    "https://matchcentre.kncb.nl/match/134453-7254602/scorecard/?period=2964940",
    "https://matchcentre.kncb.nl/match/134453-7254607/scorecard/?period=2998705",
    "https://matchcentre.kncb.nl/match/134453-7258314/scorecard/?period=3010063",
    "https://matchcentre.kncb.nl/match/134453-7258315/scorecard/?period=3029908",
    "https://matchcentre.kncb.nl/match/134453-7258320/scorecard/?period=3064968",
    "https://matchcentre.kncb.nl/match/134453-7258325/scorecard/?period=3100289",
    "https://matchcentre.kncb.nl/match/134453-7258330/scorecard/?period=3134531",
    "https://matchcentre.kncb.nl/match/134453-7258335/scorecard/?period=3165885",
    "https://matchcentre.kncb.nl/match/134453-7258340/scorecard/?period=3176417",
    "https://matchcentre.kncb.nl/match/134453-7258345/scorecard/?period=3202331",
    "https://matchcentre.kncb.nl/match/134453-7258350/scorecard/?period=3252749",

    # ACC 2 - Tweede Klasse (14 matches)
    "https://matchcentre.kncb.nl/match/134453-7323305/scorecard/?period=2904132",
    "https://matchcentre.kncb.nl/match/134453-7323309/scorecard/?period=2939290",
    "https://matchcentre.kncb.nl/match/134453-7323327/scorecard/?period=2996739",
    "https://matchcentre.kncb.nl/match/134453-7323330/scorecard/?period=3029942",
    "https://matchcentre.kncb.nl/match/134453-7323334/scorecard/?period=3065153",
    "https://matchcentre.kncb.nl/match/134453-7323338/scorecard/?period=3100381",
    "https://matchcentre.kncb.nl/match/134453-7323347/scorecard/?period=3165863",
    "https://matchcentre.kncb.nl/match/134453-7323351/scorecard/?period=3202465",
    "https://matchcentre.kncb.nl/match/134453-7323354/scorecard/?period=3227228",
    "https://matchcentre.kncb.nl/match/134453-7323359/scorecard/?period=3278179",
    "https://matchcentre.kncb.nl/match/134453-7323344/scorecard/?period=3299247",
    "https://matchcentre.kncb.nl/match/134453-7323322/scorecard/?period=3310168",
    "https://matchcentre.kncb.nl/match/134453-7323303/scorecard/?period=3329154",
    "https://matchcentre.kncb.nl/match/134453-7323293/scorecard/?period=3348459",

    # ACC 3 - Derde Klasse (14 matches)
    "https://matchcentre.kncb.nl/match/134453-7324739/scorecard/?period=2852194",
    "https://matchcentre.kncb.nl/match/134453-7324742/scorecard/?period=2883336",
    "https://matchcentre.kncb.nl/match/134453-7324747/scorecard/?period=2916332",
    "https://matchcentre.kncb.nl/match/134453-7324749/scorecard/?period=2946803",
    "https://matchcentre.kncb.nl/match/134453-7324755/scorecard/?period=2976460",
    "https://matchcentre.kncb.nl/match/134453-7324760/scorecard/?period=3012923",
    "https://matchcentre.kncb.nl/match/134453-7324763/scorecard/?period=3041462",
    "https://matchcentre.kncb.nl/match/134453-7324766/scorecard/?period=3075853",
    "https://matchcentre.kncb.nl/match/134453-7324770/scorecard/?period=3112798",
    "https://matchcentre.kncb.nl/match/134453-7324777/scorecard/?period=3176994",
    "https://matchcentre.kncb.nl/match/134453-7324784/scorecard/?period=3203046",
    "https://matchcentre.kncb.nl/match/134453-7324787/scorecard/?period=3254305",
    "https://matchcentre.kncb.nl/match/134453-7324791/scorecard/?period=3278195",
    "https://matchcentre.kncb.nl/match/134453-7324776/scorecard/?period=3337237",

    # ACC 4 - Derde Klasse (14 matches)
    "https://matchcentre.kncb.nl/match/134453-7324800/scorecard/?period=2883551",
    "https://matchcentre.kncb.nl/match/134453-7324801/scorecard/?period=2916490",
    "https://matchcentre.kncb.nl/match/134453-7324808/scorecard/?period=2946765",
    "https://matchcentre.kncb.nl/match/134453-7324815/scorecard/?period=3007435",
    "https://matchcentre.kncb.nl/match/134453-7324817/scorecard/?period=3033129",
    "https://matchcentre.kncb.nl/match/134453-7324823/scorecard/?period=3076197",
    "https://matchcentre.kncb.nl/match/134453-7324828/scorecard/?period=3112385",
    "https://matchcentre.kncb.nl/match/134453-7324836/scorecard/?period=3177632",
    "https://matchcentre.kncb.nl/match/134453-7324837/scorecard/?period=3196391",
    "https://matchcentre.kncb.nl/match/134453-7324829/scorecard/?period=3220141",
    "https://matchcentre.kncb.nl/match/134453-7324795/scorecard/?period=3229749",
    "https://matchcentre.kncb.nl/match/134453-7324844/scorecard/?period=3254928",
    "https://matchcentre.kncb.nl/match/134453-7324848/scorecard/?period=3278019",
    "https://matchcentre.kncb.nl/match/134453-7324809/scorecard/?period=3291663",

    # ACC 5 - Vierde Klasse (13 matches)
    "https://matchcentre.kncb.nl/match/134453-7326156/scorecard/?period=2841845",
    "https://matchcentre.kncb.nl/match/134453-7326162/scorecard/?period=2882990",
    "https://matchcentre.kncb.nl/match/134453-7326166/scorecard/?period=2916125",
    "https://matchcentre.kncb.nl/match/134453-7326170/scorecard/?period=2947165",
    "https://matchcentre.kncb.nl/match/134453-7326173/scorecard/?period=2976000",
    "https://matchcentre.kncb.nl/match/134453-7326177/scorecard/?period=3009818",
    "https://matchcentre.kncb.nl/match/134453-7326183/scorecard/?period=3041738",
    "https://matchcentre.kncb.nl/match/134453-7326186/scorecard/?period=3076097",
    "https://matchcentre.kncb.nl/match/134453-7326195/scorecard/?period=3143609",
    "https://matchcentre.kncb.nl/match/134453-7326199/scorecard/?period=3176682",
    "https://matchcentre.kncb.nl/match/134453-7326203/scorecard/?period=3202881",
    "https://matchcentre.kncb.nl/match/134453-7326207/scorecard/?period=3253329",
    "https://matchcentre.kncb.nl/match/134453-7326192/scorecard/?period=3349431",

    # ACC 6 - Vierde Klasse (15 matches)
    "https://matchcentre.kncb.nl/match/134453-7326066/scorecard/?period=2850306",
    "https://matchcentre.kncb.nl/match/134453-7326073/scorecard/?period=2883235",
    "https://matchcentre.kncb.nl/match/134453-7326075/scorecard/?period=2916144",
    "https://matchcentre.kncb.nl/match/134453-7326082/scorecard/?period=2946880",
    "https://matchcentre.kncb.nl/match/134453-7326086/scorecard/?period=2977142",
    "https://matchcentre.kncb.nl/match/134453-7326093/scorecard/?period=3006656",
    "https://matchcentre.kncb.nl/match/134453-7326097/scorecard/?period=3040872",
    "https://matchcentre.kncb.nl/match/134453-7326102/scorecard/?period=3076497",
    "https://matchcentre.kncb.nl/match/134453-7326120/scorecard/?period=3177552",
    "https://matchcentre.kncb.nl/match/134453-7326121/scorecard/?period=3202629",
    "https://matchcentre.kncb.nl/match/134453-7326130/scorecard/?period=3254377",
    "https://matchcentre.kncb.nl/match/134453-7326132/scorecard/?period=3278510",
    "https://matchcentre.kncb.nl/match/134453-7326139/scorecard/?period=3299667",
    "https://matchcentre.kncb.nl/match/134453-7326143/scorecard/?period=3318997",
    "https://matchcentre.kncb.nl/match/134453-7326148/scorecard/?period=3336151",

    # ACC ZAMI (18 matches - players randomly split into ZAMI 1 and ZAMI 2 each week)
    "https://matchcentre.kncb.nl/match/134453-7332092/scorecard/?period=2843768",
    "https://matchcentre.kncb.nl/match/134453-7332265/scorecard/?period=2874105",
    "https://matchcentre.kncb.nl/match/134453-7332269/scorecard/?period=2905571",
    "https://matchcentre.kncb.nl/match/134453-7332277/scorecard/?period=3011077",
    "https://matchcentre.kncb.nl/match/134453-7332287/scorecard/?period=3030800",
    "https://matchcentre.kncb.nl/match/134453-7332115/scorecard/?period=3030130",
    "https://matchcentre.kncb.nl/match/134453-7332119/scorecard/?period=3066708",
    "https://matchcentre.kncb.nl/match/134453-7332299/scorecard/?period=3126107",
    "https://matchcentre.kncb.nl/match/134453-7332129/scorecard/?period=3134372",
    "https://matchcentre.kncb.nl/match/134453-7332305/scorecard/?period=3167281",
    "https://matchcentre.kncb.nl/match/134453-7332101/scorecard/?period=3220873",
    "https://matchcentre.kncb.nl/match/134453-7332315/scorecard/?period=3245799",
    "https://matchcentre.kncb.nl/match/134453-7332316/scorecard/?period=3270149",
    "https://matchcentre.kncb.nl/match/134453-7332095/scorecard/?period=3290232",
    "https://matchcentre.kncb.nl/match/134453-7332122/scorecard/?period=3293739",
    "https://matchcentre.kncb.nl/match/134453-7332309/scorecard/?period=3312111",
    "https://matchcentre.kncb.nl/match/134453-7332274/scorecard/?period=3344089",
    "https://matchcentre.kncb.nl/match/134453-7332302/scorecard/?period=3325946",

    # ACC U17 (10 matches)
    "https://matchcentre.kncb.nl/match/134453-7329152/scorecard/?period=2912677",
    "https://matchcentre.kncb.nl/match/134453-7329153/scorecard/?period=2943897",
    "https://matchcentre.kncb.nl/match/134453-7329157/scorecard/?period=2972028",
    "https://matchcentre.kncb.nl/match/134453-7329168/scorecard/?period=3037165",
    "https://matchcentre.kncb.nl/match/134453-7329170/scorecard/?period=3074823",
    "https://matchcentre.kncb.nl/match/134453-7329172/scorecard/?period=3111697",
    "https://matchcentre.kncb.nl/match/134453-7329159/scorecard/?period=3129887",
    "https://matchcentre.kncb.nl/match/134453-7329176/scorecard/?period=3140558",
    "https://matchcentre.kncb.nl/match/134453-7329179/scorecard/?period=3161466",
    "https://matchcentre.kncb.nl/match/134453-7393900/scorecard/?period=3334719",

    # ACC U15 (11 matches)
    "https://matchcentre.kncb.nl/match/134453-7331235/scorecard/?period=2879394",
    "https://matchcentre.kncb.nl/match/134453-7331237/scorecard/?period=2912048",
    "https://matchcentre.kncb.nl/match/134453-7331240/scorecard/?period=2944264",
    "https://matchcentre.kncb.nl/match/134453-7331246/scorecard/?period=3002096",
    "https://matchcentre.kncb.nl/match/134453-7331249/scorecard/?period=3037245",
    "https://matchcentre.kncb.nl/match/134453-7331253/scorecard/?period=3072449",
    "https://matchcentre.kncb.nl/match/134453-7331256/scorecard/?period=3108869",
    "https://matchcentre.kncb.nl/match/134453-7331262/scorecard/?period=3173537",
    "https://matchcentre.kncb.nl/match/134453-7393853/scorecard/?period=3334732",
    "https://matchcentre.kncb.nl/match/134453-7395417/scorecard/?period=3347172",
    "https://matchcentre.kncb.nl/match/134453-7397066/scorecard/?period=3356986",

    # ACC U13 (8 matches)
    "https://matchcentre.kncb.nl/match/134453-7336247/scorecard/?period=2880895",
    "https://matchcentre.kncb.nl/match/134453-7336254/scorecard/?period=2911963",
    "https://matchcentre.kncb.nl/match/134453-7336258/scorecard/?period=2957282",
    "https://matchcentre.kncb.nl/match/134453-7336263/scorecard/?period=2971797",
    "https://matchcentre.kncb.nl/match/134453-7336272/scorecard/?period=3037077",
    "https://matchcentre.kncb.nl/match/134453-7336280/scorecard/?period=3072362",
    "https://matchcentre.kncb.nl/match/134453-7336281/scorecard/?period=3108918",
    "https://matchcentre.kncb.nl/match/134453-7336290/scorecard/?period=3140511",
]


class LegacyDatabaseBuilder:
    """Build initial ACC player database from scorecards"""

    def __init__(self):
        self.aggregator = PlayerSeasonAggregator()
        self.value_calculator = PlayerValueCalculator()

        # Store player IDs (name -> matchcentre_id)
        # We'll store both abbreviated ("I ALIM") and full ("IrfanAlim") as keys
        self.player_ids = {}

        # Map full names to abbreviated names
        self.full_to_abbrev = {}

        # Map player names to their teams
        self.player_teams = {}

        # Track wicket-keepers (players with † marker)
        self.wicket_keepers = set()

        # Track teams
        self.acc_teams = set()

        # Track which scorecards we've processed
        self.scorecards_processed = []

    async def build_from_scorecards(self, scorecard_urls: List[str]):
        """Build database from a list of scorecard URLs"""

        logger.info("🏏 Building ACC Legacy Database")
        logger.info(f"   Scorecard URLs to process: {len(scorecard_urls)}")
        print()

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)

        try:
            for i, url in enumerate(scorecard_urls, 1):
                logger.info(f"📋 Scorecard {i}/{len(scorecard_urls)}")
                logger.info(f"   URL: {url}")

                page = await browser.new_page()
                try:
                    await self._process_scorecard(page, url)
                    self.scorecards_processed.append(url)
                finally:
                    await page.close()

                print()

        finally:
            await browser.close()
            await playwright.stop()

        logger.info(f"✅ Processing complete!")
        logger.info(f"   Scorecards processed: {len(self.scorecards_processed)}")
        logger.info(f"   Unique players found: {len(self.player_ids)}")
        logger.info(f"   Teams: {sorted(self.acc_teams)}")

    async def _process_scorecard(self, page, url: str):
        """Process a single scorecard to extract players and stats"""

        # Extract match ID from URL
        match_id = url.split('/match/')[-1].split('/')[0] if '/match/' in url else 'unknown'

        try:
            # Load scorecard
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)

            # Extract player IDs from links
            logger.info(f"   Extracting player IDs...")
            player_links = await page.query_selector_all('a[href*="/player/"]')
            player_id_map = {}  # abbreviated_name -> (id, full_name)

            for link in player_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()

                    if href and text:
                        match = re.search(r'/player/(\d+)/', href)
                        if match:
                            player_id = match.group(1)
                            full_name = text.strip()

                            # Create abbreviated version for matching scorecard names
                            # "IrfanAlim" -> "I ALIM"
                            abbreviated = create_abbreviated_name(full_name)

                            # Store using abbreviated name as key (for matching in scorecard)
                            player_id_map[abbreviated] = (player_id, full_name)

                            # Store ID under BOTH abbreviated and full name for later lookup
                            self.player_ids[abbreviated] = player_id
                            self.player_ids[full_name] = player_id
                            self.full_to_abbrev[full_name] = abbreviated

                            logger.debug(f"      {full_name} -> {abbreviated} (ID: {player_id})")
                except:
                    continue

            logger.info(f"   Found {len(player_id_map)} player IDs")

            # Extract team name from URL using manual mapping
            # Extract match ID from URL (e.g., "7324739" from the URL)
            match_id_match = re.search(r'/match/\d+-(\d+)/', url)
            acc_team = None

            if match_id_match:
                match_id_str = match_id_match.group(1)
                acc_team = SCORECARD_TEAM_MAP.get(match_id_str)

            if not acc_team:
                logger.warning(f"   ⚠️  Could not map URL to team, using generic 'ACC'")
                acc_team = 'ACC'

            self.acc_teams.add(acc_team)
            logger.info(f"   Team: {acc_team}")

            # Get page text for parsing
            page_text = await page.inner_text('body')

            # Parse stats from visible text (already fetched above)
            lines = page_text.split('\n')

            # Parse batting and bowling
            for i, line in enumerate(lines):
                if line.strip() == 'BATTING':
                    await self._parse_batting(lines, i, acc_team, player_id_map, match_id)
                elif line.strip() == 'BOWLING':
                    await self._parse_bowling(lines, i, acc_team, player_id_map, match_id)

        except Exception as e:
            logger.error(f"   ❌ Error processing scorecard: {e}")

    async def _parse_batting(self, lines: List[str], start_idx: int, team: str, player_id_map: Dict, match_id: str):
        """Parse batting section"""
        i = start_idx + 1
        players_found = 0

        # Skip headers
        while i < len(lines) and lines[i].strip() in ['BATTING', 'R', 'B', '4', '6', 'SR', '']:
            i += 1

        # Parse players
        while i < len(lines) - 6:
            if lines[i].strip() in ['BOWLING', 'FIELDING', '']:
                break

            player_name = lines[i].strip()
            if not player_name or len(player_name) < 3:
                i += 1
                continue

            if player_name in ['R', 'B', '4', '6', 'SR', 'BATTING', 'Players', 'Round']:
                i += 1
                continue

            if player_name.replace('.', '').isdigit():
                i += 1
                continue

            # Skip invalid entries
            if 'TOTAL:' in player_name or 'Round' in player_name:
                i += 1
                continue
            if player_name.startswith('ACC ') or player_name.startswith('Quick '):
                i += 1
                continue

            try:
                runs = int(lines[i + 2].strip()) if lines[i + 2].strip().isdigit() else 0
                balls = int(lines[i + 3].strip()) if lines[i + 3].strip().isdigit() else 0
                fours = int(lines[i + 4].strip()) if lines[i + 4].strip().isdigit() else 0
                sixes = int(lines[i + 5].strip()) if lines[i + 5].strip().isdigit() else 0

                # Check if player is wicket-keeper (has † marker)
                is_wicket_keeper = '†' in player_name

                # Remove special characters (captain marker *, wicketkeeper marker †)
                clean_name = player_name.replace('*', '').replace('†', '').strip()

                # Look up full name and ID using cleaned name
                full_name = player_name
                for key, (pid, fname) in player_id_map.items():
                    if key.upper() == clean_name.upper():
                        full_name = fname
                        break

                # Track wicket-keeper status
                if is_wicket_keeper:
                    self.wicket_keepers.add(full_name)

                perf = {
                    'player_name': full_name,
                    'club': 'ACC',
                    'team': team,
                    'match_id': match_id,
                    'match_date': datetime.now().isoformat(),
                    'runs': runs,
                    'balls_faced': balls,
                    'fours': fours,
                    'sixes': sixes,
                    'wickets': 0,
                    'overs': 0.0,
                    'runs_conceded': 0,
                    'maidens': 0,
                    'catches': 0,
                    'stumpings': 0,
                    'run_outs': 0,
                }

                self.aggregator.add_match_performance(perf)

                # Track which team this player belongs to
                self.player_teams[full_name] = team

                players_found += 1
                i += 7

            except (ValueError, IndexError):
                i += 1

        if players_found > 0:
            logger.info(f"      Batting: {players_found} players")

    async def _parse_bowling(self, lines: List[str], start_idx: int, team: str, player_id_map: Dict, match_id: str):
        """Parse bowling section for ACC players"""
        i = start_idx + 1
        players_found = 0

        # Skip headers
        while i < len(lines) and lines[i].strip() in ['BOWLING', 'O', 'M', 'R', 'W', 'NB', 'WD', '']:
            i += 1

        # Parse bowlers
        while i < len(lines) - 6:
            if lines[i].strip() in ['FIELDING', 'Players', ''] or 'Players' in lines[i]:
                break

            bowler_name = lines[i].strip()
            if not bowler_name or len(bowler_name) < 3:
                i += 1
                continue

            if bowler_name in ['O', 'M', 'R', 'W', 'NB', 'WD', 'BOWLING']:
                i += 1
                continue

            if bowler_name.replace('.', '').isdigit():
                i += 1
                continue

            # Check if this is an ACC player
            is_acc = False
            full_name = bowler_name
            for key, (pid, fname) in player_id_map.items():
                if key.upper() == bowler_name.upper():
                    full_name = fname
                    is_acc = True
                    break

            if not is_acc:
                i += 7
                continue

            try:
                overs_str = lines[i + 1].strip()
                maidens = int(lines[i + 2].strip()) if lines[i + 2].strip().isdigit() else 0
                runs = int(lines[i + 3].strip()) if lines[i + 3].strip().isdigit() else 0
                wickets = int(lines[i + 4].strip()) if lines[i + 4].strip().isdigit() else 0
                overs = float(overs_str) if overs_str.replace('.', '').isdigit() else 0.0

                perf = {
                    'player_name': full_name,
                    'club': 'ACC',
                    'team': team,
                    'match_id': match_id,
                    'match_date': datetime.now().isoformat(),
                    'runs': 0,
                    'balls_faced': 0,
                    'fours': 0,
                    'sixes': 0,
                    'wickets': wickets,
                    'overs': overs,
                    'runs_conceded': runs,
                    'maidens': maidens,
                    'catches': 0,
                    'stumpings': 0,
                    'run_outs': 0,
                }

                self.aggregator.add_match_performance(perf)

                # Track which team this player belongs to
                self.player_teams[full_name] = team

                players_found += 1
                i += 7

            except (ValueError, IndexError):
                i += 1

        if players_found > 0:
            logger.info(f"      Bowling: {players_found} players")

    def generate_legacy_database(self, output_file: str) -> Dict:
        """Generate the legacy database JSON"""

        logger.info(f"\n💾 Generating legacy database...")
        logger.info(f"   Total players: {len(self.aggregator.players)}")
        logger.info(f"   Players with IDs: {len(self.player_ids)}")

        if len(self.aggregator.players) == 0:
            logger.warning("⚠️  No players found!")
            return {"players": [], "total": 0}

        # Convert to PlayerStats
        player_stats_list = []
        player_team_map = {}

        for player_id, player_data in self.aggregator.players.items():
            player_name = player_data['player_name']
            team_name = self.player_teams.get(player_name, 'ACC')

            stats = PlayerStats(
                player_name=player_name,
                club=player_data['club'],
                matches_played=player_data['matches_played'],
                total_runs=player_data['season_totals']['batting']['runs'],
                batting_average=player_data['averages']['batting_average'],
                strike_rate=player_data['averages']['strike_rate'],
                total_wickets=player_data['season_totals']['bowling']['wickets'],
                bowling_average=player_data['averages']['bowling_average'],
                economy_rate=player_data['averages']['economy_rate'],
                catches=player_data['season_totals']['fielding']['catches'],
                run_outs=player_data['season_totals']['fielding']['runouts'],
                team_level=self._determine_team_level(team_name)
            )
            player_stats_list.append(stats)
            # Use our tracked team assignment, fallback to 'ACC' if not found
            player_team_map[stats.player_name] = self.player_teams.get(stats.player_name, 'ACC')

        # Calculate fantasy values per team
        logger.info(f"💰 Calculating fantasy values...")
        results = self.value_calculator.calculate_team_values_per_team(
            player_stats_list,
            team_name_getter=lambda p: player_team_map[p.player_name]
        )

        # Build database
        database = {
            "club": "ACC",
            "season": "2025",
            "created_at": datetime.now().isoformat(),
            "notes": "Legacy ACC player database with Match Centre IDs",
            "source_scorecards": self.scorecards_processed,
            "total_players": len(results),
            "teams": sorted(list(self.acc_teams)),
            "players": []
        }

        for i, (stats, value, justification) in enumerate(results):
            team_name = player_team_map[stats.player_name]
            matchcentre_id = self.player_ids.get(stats.player_name)

            # Determine grade from team level
            grade_map = {
                'hoofdklasse': 'Hoofdklasse',
                'tweede': 'Tweede Klasse',
                'derde': 'Derde Klasse',
                'vierde': 'Vierde Klasse',
                'zami': 'ZAMI Klasse',
                'youth': 'Youth'
            }
            grade = grade_map.get(stats.team_level, 'Hoofdklasse')

            player_entry = {
                "player_id": f"acc_legacy_{i+1:03d}",
                "name": stats.player_name,
                "matchcentre_id": matchcentre_id,
                "matchcentre_url": f"https://matchcentre.kncb.nl/player/{matchcentre_id}/19/" if matchcentre_id else None,
                "club": "ACC",
                "team_name": team_name,  # e.g., "ACC 3"
                "grade": grade,  # e.g., "Derde Klasse"
                "team_level": stats.team_level,  # e.g., "derde"
                "is_wicket_keeper": stats.player_name in self.wicket_keepers,
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
            database['players'].append(player_entry)

        # Sort by value
        database['players'].sort(key=lambda x: x['fantasy_value'], reverse=True)

        # Save
        with open(output_file, 'w') as f:
            json.dump(database, f, indent=2)

        logger.info(f"✅ Legacy database saved to {output_file}")
        return database

    def _determine_team_level(self, team_name: str) -> str:
        """Map team name to level"""
        team_upper = team_name.upper()

        if 'ACC 1' == team_upper or team_upper == 'ACC1':
            return 'hoofdklasse'
        elif 'ACC 2' == team_upper or team_upper == 'ACC2':
            return 'tweede'
        elif 'ACC 3' in team_upper or 'ACC 4' in team_upper or 'ACC3' in team_upper or 'ACC4' in team_upper:
            return 'derde'
        elif 'ACC 5' in team_upper or 'ACC 6' in team_upper or 'ACC5' in team_upper or 'ACC6' in team_upper:
            return 'vierde'
        elif 'ZAMI' in team_upper:
            return 'zami'
        elif 'U17' in team_upper or 'U15' in team_upper or 'U13' in team_upper:
            return 'youth'
        else:
            return 'hoofdklasse'


async def main():
    print("\n" + "=" * 80)
    print("🏏 ACC LEGACY DATABASE BUILDER")
    print("=" * 80)
    print("Building initial player database from known scorecards...")
    print(f"Scorecard URLs: {len(KNOWN_SCORECARDS)}")
    print("=" * 80)
    print()

    builder = LegacyDatabaseBuilder()

    try:
        await builder.build_from_scorecards(KNOWN_SCORECARDS)
        database = builder.generate_legacy_database('rosters/acc_legacy_database.json')

        print()
        print("=" * 80)
        print("✅ LEGACY DATABASE CREATED!")
        print("=" * 80)
        print(f"   Total players: {database.get('total_players', 0)}")
        print(f"   Teams: {', '.join(database.get('teams', []))}")
        print(f"   Output file: rosters/acc_legacy_database.json")
        print()

        if database.get('players'):
            print("🌟 Top 10 players:")
            for i, p in enumerate(database['players'][:10], 1):
                mc_id = p.get('matchcentre_id') or 'no ID'
                print(f"   {i:2d}. {p['name']:<30} {p['team_name']:<15} €{p['fantasy_value']:>5.1f} [{mc_id}]")

        print()
        print("💡 Next step: Add more scorecard URLs to KNOWN_SCORECARDS and run again")
        print("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
