#!/usr/bin/env python3
"""
KNCB Scraper Enhancements for 2026 Season
==========================================
Production-ready improvements to make scraper robust against layout changes.

This module contains enhancements that should be integrated into kncb_html_scraper.py:
- React render validation
- Retry logic with exponential backoff
- Data quality validation
- Comprehensive error logging
- Dynamic field detection helpers

Usage:
    Mix these methods into KNCBMatchCentreScraper class or use as standalone utilities.

Author: Claude Code
Date: 2025-12-16
Status: Production Ready
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


# ==============================================================================
# PHASE 1: React Render Validation
# ==============================================================================

async def wait_for_scorecard_ready(page, timeout: int = 10) -> bool:
    """
    Wait for scorecard to fully render with validation

    Checks for:
    - BATTING section present
    - BOWLING section present
    - Numeric data present
    - Sufficient content (not just loading screen)

    Args:
        page: Playwright page object
        timeout: Maximum seconds to wait

    Returns:
        True if scorecard rendered completely, False if timeout
    """
    start_time = asyncio.get_event_loop().time()

    logger.info(f"   Waiting for scorecard to render (max {timeout}s)...")

    while True:
        # Get current page content
        text = await page.inner_text('body')

        # Check for expected sections
        has_batting = 'BATTING' in text
        has_bowling = 'BOWLING' in text
        has_numbers = any(char.isdigit() for char in text)
        has_content = len([line for line in text.split('\n') if len(line.strip()) > 3]) > 10

        # All checks must pass
        if has_batting and has_bowling and has_numbers and has_content:
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"   ✅ Scorecard ready after {elapsed:.1f}s")
            return True

        # Check timeout
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            logger.warning(f"   ⚠️  Scorecard didn't fully render in {timeout}s")
            logger.warning(f"      Has BATTING: {has_batting}")
            logger.warning(f"      Has BOWLING: {has_bowling}")
            logger.warning(f"      Has numbers: {has_numbers}")
            logger.warning(f"      Has content: {has_content}")
            return False

        # Wait before checking again
        await asyncio.sleep(0.5)


# ==============================================================================
# PHASE 1: Retry Logic with Exponential Backoff
# ==============================================================================

async def fetch_with_retry(page, url: str, max_retries: int = 3) -> bool:
    """
    Fetch URL with retry and exponential backoff

    Handles:
    - Network timeouts
    - Server errors (5xx)
    - Temporary failures

    Args:
        page: Playwright page
        url: URL to fetch
        max_retries: Maximum retry attempts

    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"   Fetching {url} (attempt {attempt + 1}/{max_retries})")

            response = await page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=30000
            )

            if response and response.status == 200:
                logger.info(f"   ✅ Success on attempt {attempt + 1}")
                return True
            else:
                status = response.status if response else 'No response'
                logger.warning(f"   ⚠️  Got status {status}")

                # Don't retry on 404 (match doesn't exist)
                if response and response.status == 404:
                    logger.error(f"   ❌ Match not found (404), not retrying")
                    return False

        except Exception as e:
            logger.warning(f"   ⚠️  Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                wait = 2 ** attempt  # Exponential: 1s, 2s, 4s
                logger.info(f"   Waiting {wait}s before retry...")
                await asyncio.sleep(wait)
            else:
                logger.error(f"   ❌ All {max_retries} attempts failed")
                return False

    return False


# ==============================================================================
# PHASE 2: Data Quality Validation
# ==============================================================================

def validate_batting_stats(stats: Dict) -> Tuple[bool, List[str]]:
    """
    Validate batting statistics are reasonable

    Checks:
    - No negative values
    - Boundary math (4s + 6s <= total runs)
    - Strike rate calculation
    - Reasonable value ranges

    Returns:
        (is_valid, warnings_list)
    """
    warnings = []

    runs = stats.get('runs', 0)
    balls = stats.get('balls_faced', 0)
    fours = stats.get('fours', 0)
    sixes = stats.get('sixes', 0)
    sr = stats.get('strike_rate', 0)

    # Check for impossible values
    if runs < 0:
        warnings.append(f"Negative runs: {runs}")

    if balls < 0:
        warnings.append(f"Negative balls: {balls}")

    if fours < 0 or sixes < 0:
        warnings.append(f"Negative boundaries: 4s={fours}, 6s={sixes}")

    # Check boundary math
    boundary_runs = (fours * 4) + (sixes * 6)
    if boundary_runs > runs:
        warnings.append(f"Boundaries ({boundary_runs}) > total runs ({runs})")

    # Check strike rate calculation
    if balls > 0:
        expected_sr = (runs / balls) * 100
        if abs(expected_sr - sr) > 1.0:  # Allow 1% tolerance for rounding
            warnings.append(f"SR mismatch: expected {expected_sr:.1f}, got {sr:.1f}")

    # Check for unusual but possible values
    if sr > 400:
        warnings.append(f"Very high SR: {sr:.1f} (possible but unusual)")

    if balls > 300:  # Unlikely in limited overs
        warnings.append(f"Many balls faced: {balls} (check match format)")

    return len(warnings) == 0, warnings


def validate_bowling_stats(stats: Dict) -> Tuple[bool, List[str]]:
    """
    Validate bowling statistics are reasonable

    Checks:
    - Wickets in valid range (0-10)
    - Maidens <= overs
    - No negative values
    - Reasonable over counts

    Returns:
        (is_valid, warnings_list)
    """
    warnings = []

    overs = stats.get('overs', 0)
    maidens = stats.get('maidens', 0)
    runs = stats.get('runs', 0)
    wickets = stats.get('wickets', 0)

    # Check for impossible values
    if wickets < 0 or wickets > 10:
        warnings.append(f"Invalid wickets: {wickets} (must be 0-10)")

    if maidens < 0:
        warnings.append(f"Negative maidens: {maidens}")

    if runs < 0:
        warnings.append(f"Negative runs conceded: {runs}")

    if overs < 0:
        warnings.append(f"Negative overs: {overs}")

    # Check logical constraints
    if maidens > overs:
        warnings.append(f"Maidens ({maidens}) > overs ({overs})")

    # Check for unusual values
    if overs > 50:  # Very long spell
        warnings.append(f"Many overs: {overs} (check match format)")

    return len(warnings) == 0, warnings


# ==============================================================================
# PHASE 2: Dynamic Field Detection (Core Innovation)
# ==============================================================================

def detect_batting_fields(lines: List[str], section_start: int) -> Tuple[List[str], int, int]:
    """
    Dynamically detect batting section field structure

    This eliminates the hardcoded "7 lines per player" assumption!

    Looks for column headers (single letters or short codes) and determines:
    1. What fields are present (R, B, 4, 6, SR, DOTS, etc.)
    2. How many lines per player
    3. Where player data starts

    Returns:
        (field_names, field_count, data_start_idx)
    """
    # Common batting field headers
    known_headers = ['R', 'B', '4', '6', 'SR', 'DOTS', 'ECON']

    headers = []
    idx = section_start + 1  # Skip "BATTING" line

    # Scan for column headers (single letters or short codes)
    while idx < len(lines) and idx < section_start + 20:  # Check up to 20 lines
        line = lines[idx].strip()

        # Stop if we hit what looks like a player name
        if len(line) > 5 and not line.isdigit():
            break

        # Add to headers if it's a known field
        if line in known_headers:
            headers.append(line)
        elif line and len(line) <= 4 and line.isupper():
            # Unknown short header, add it anyway
            headers.append(line)

        idx += 1

    # Field count = headers + 2 (name and dismissal always present)
    field_count = len(headers) + 2

    logger.info(f"   Detected {len(headers)} fields: {headers}")
    logger.info(f"   Field count per player: {field_count} lines")

    return headers, field_count, idx


def detect_bowling_fields(lines: List[str], section_start: int) -> Tuple[List[str], int, int]:
    """
    Dynamically detect bowling section field structure

    Handles both 7-line and 8-line formats (with/without ECON)

    Returns:
        (field_names, field_count, data_start_idx)
    """
    # Common bowling field headers
    known_headers = ['O', 'M', 'R', 'W', 'NB', 'WD', 'ECON']

    headers = []
    idx = section_start + 1  # Skip "BOWLING" line

    while idx < len(lines) and idx < section_start + 20:
        line = lines[idx].strip()

        # Stop if we hit what looks like a player name
        if len(line) > 5 and not line.isdigit():
            break

        if line in known_headers:
            headers.append(line)
        elif line and len(line) <= 4 and line.isupper():
            headers.append(line)

        idx += 1

    field_count = len(headers) + 1  # +1 for name

    logger.info(f"   Detected {len(headers)} bowling fields: {headers}")
    logger.info(f"   Field count per bowler: {field_count} lines")

    return headers, field_count, idx


def is_section_marker(line: str) -> bool:
    """
    Check if line is a section marker (BATTING, BOWLING, FIELDING, etc.)

    Returns:
        True if line indicates a new section
    """
    markers = [
        'BATTING',
        'BOWLING',
        'FIELDING',
        'Players',
        'FALL OF WICKETS',
        'EXTRAS',
        'TOTAL'
    ]

    line_stripped = line.strip()
    return line_stripped in markers or any(m in line_stripped for m in markers)


def is_name_line_position(position_in_section: int, field_count: int) -> bool:
    """
    Check if position matches where player names appear

    In a 7-line pattern: positions 0, 7, 14, 21... are names
    In an 8-line pattern: positions 0, 8, 16, 24... are names

    Args:
        position_in_section: Line number within section (0-indexed)
        field_count: Number of lines per player

    Returns:
        True if this position should be a player name
    """
    return position_in_section % field_count == 0


# ==============================================================================
# PHASE 1 & 2: Enhanced Error Logging
# ==============================================================================

def log_extraction_summary(club_name: str, players: List[Dict], warnings: List[str]):
    """
    Log comprehensive extraction summary

    Args:
        club_name: Club being processed
        players: List of extracted players
        warnings: List of warning messages
    """
    logger.info(f"📊 Extraction summary for {club_name}:")
    logger.info(f"   Players: {len(players)}")

    if warnings:
        logger.warning(f"   Warnings: {len(warnings)}")
        # Show first 5 warnings
        for warning in warnings[:5]:
            logger.warning(f"      - {warning}")
        if len(warnings) > 5:
            logger.warning(f"      ... and {len(warnings) - 5} more")
    else:
        logger.info(f"   ✅ No warnings")


def log_match_extraction_stats(scorecard: Dict):
    """
    Log match-level extraction statistics

    Args:
        scorecard: Parsed scorecard dict
    """
    if not scorecard or 'innings' not in scorecard:
        logger.warning("⚠️  Empty scorecard")
        return

    total_batters = sum(len(inn.get('batting', [])) for inn in scorecard['innings'])
    total_bowlers = sum(len(inn.get('bowling', [])) for inn in scorecard['innings'])

    logger.info(f"   ✅ Extracted {total_batters} batters, {total_bowlers} bowlers")

    # Check for suspiciously low numbers
    if total_batters < 5:
        logger.warning(f"   ⚠️  Very few batters extracted ({total_batters}), check parsing")

    if total_bowlers < 3:
        logger.warning(f"   ⚠️  Very few bowlers extracted ({total_bowlers}), check parsing")


# ==============================================================================
# UTILITY: Better Dismissal Handling
# ==============================================================================

def is_player_out(dismissal: str) -> bool:
    """
    Determine if player is out based on dismissal text

    Handles:
    - not out
    - retired hurt (not out)
    - retired not out
    - retired (ambiguous, treat as not out to be safe)
    - absent hurt (didn't bat)

    Args:
        dismissal: Dismissal text from scorecard

    Returns:
        True if player is out (duck penalty applies)
    """
    dismissal_lower = dismissal.lower()

    # Not out cases
    not_out_patterns = [
        'not out',
        'retired hurt',
        'retired not out',
        'absent',
        'dnb'  # Did not bat
    ]

    for pattern in not_out_patterns:
        if pattern in dismissal_lower:
            return False

    # Check for common dismissals (definitely out)
    out_patterns = ['b ', 'c ', 'lbw', 'st ', 'run out', 'hit wicket', 'timed out']
    for pattern in out_patterns:
        if pattern in dismissal_lower:
            return True

    # Default: if it's just "retired" with no qualifier, treat as not out
    if 'retired' in dismissal_lower:
        return False

    # Otherwise assume out
    return True


# ==============================================================================
# INTEGRATION EXAMPLE
# ==============================================================================

def example_integration():
    """
    Example of how to integrate these enhancements into kncb_html_scraper.py

    Add these methods to KNCBMatchCentreScraper class:

    class KNCBMatchCentreScraper:

        # Add to _scrape_scorecard_html() after page.goto():
        if not await wait_for_scorecard_ready(page, timeout=10):
            logger.error("Scorecard failed to render")
            return None

        # Replace page.goto() with:
        if not await fetch_with_retry(page, url, max_retries=3):
            return None

        # In _parse_batting_section(), add at start:
        fields, field_count, data_start = detect_batting_fields(lines, start_idx)
        # Then use field_count instead of hardcoded 7

        # In extract_player_stats(), add for each player:
        is_valid, warnings = validate_batting_stats(batter)
        if not is_valid:
            logger.warning(f"Validation issues for {player_name}: {warnings}")

        # After extraction:
        log_extraction_summary(club_name, players, all_warnings)
    """
    pass


if __name__ == "__main__":
    print("=" * 80)
    print("KNCB Scraper 2026 Enhancements")
    print("=" * 80)
    print()
    print("This module contains production-ready enhancements:")
    print()
    print("✅ Phase 1 (Critical):")
    print("   - React render validation")
    print("   - Retry logic with exponential backoff")
    print("   - Enhanced error logging")
    print()
    print("✅ Phase 2 (Robustness):")
    print("   - Dynamic field detection (eliminates hardcoded assumptions)")
    print("   - Data quality validation")
    print("   - Better dismissal handling")
    print()
    print("📝 Integration:")
    print("   See example_integration() function for usage")
    print("   Or see SCRAPER_2026_READINESS_PLAN.md for detailed instructions")
    print()
    print("🚀 Status: Production Ready for 2026 Season")
    print("=" * 80)
