#!/usr/bin/env python3
"""
Scraper Configuration
=====================
Centralized configuration for KNCB scraper with support for:
- Production mode (real KNCB API)
- Test mode (mock server)
- Environment variable overrides

Usage:
    from scraper_config import get_scraper_config, ScraperMode

    # Use production
    config = get_scraper_config(ScraperMode.PRODUCTION)

    # Use mock for testing
    config = get_scraper_config(ScraperMode.MOCK)

    # Or use environment variable
    # export SCRAPER_MODE=mock
    config = get_scraper_config()
"""

import os
from enum import Enum
from typing import Dict


class ScraperMode(Enum):
    """Scraper operating modes"""
    PRODUCTION = "production"
    MOCK = "mock"


class ScraperConfig:
    """Configuration container for scraper"""

    def __init__(
        self,
        mode: ScraperMode,
        api_url: str,
        matchcentre_url: str,
        api_id: str = "1002",
        entity_id: str = "134453"
    ):
        self.mode = mode
        self.api_url = api_url
        self.matchcentre_url = matchcentre_url
        self.api_id = api_id
        self.entity_id = entity_id

    def is_mock(self) -> bool:
        """Check if running in mock mode"""
        return self.mode == ScraperMode.MOCK

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.mode == ScraperMode.PRODUCTION

    def __repr__(self):
        return f"ScraperConfig(mode={self.mode.value}, api_url={self.api_url})"


# Configuration presets
CONFIGS = {
    ScraperMode.PRODUCTION: ScraperConfig(
        mode=ScraperMode.PRODUCTION,
        api_url="https://api.resultsvault.co.uk/rv",
        matchcentre_url="https://matchcentre.kncb.nl",
        api_id="1002",
        entity_id="134453"
    ),
    ScraperMode.MOCK: ScraperConfig(
        mode=ScraperMode.MOCK,
        api_url="http://localhost:5001/rv",  # Mock server inside container
        matchcentre_url="http://localhost:5001",  # Not used in mock mode
        api_id="1002",
        entity_id="134453"
    )
}


def get_scraper_config(mode: ScraperMode = None) -> ScraperConfig:
    """
    Get scraper configuration

    Args:
        mode: Explicit mode to use (overrides environment)

    Returns:
        ScraperConfig instance

    Environment Variables:
        SCRAPER_MODE: "production" or "mock" (default: production)
        SCRAPER_API_URL: Override API URL
        SCRAPER_MATCHCENTRE_URL: Override match centre URL
    """
    # Determine mode
    if mode is None:
        env_mode = os.environ.get('SCRAPER_MODE', 'production').lower()
        if env_mode == 'mock':
            mode = ScraperMode.MOCK
        else:
            mode = ScraperMode.PRODUCTION

    # Get base config
    config = CONFIGS[mode]

    # Allow environment variable overrides
    api_url = os.environ.get('SCRAPER_API_URL', config.api_url)
    matchcentre_url = os.environ.get('SCRAPER_MATCHCENTRE_URL', config.matchcentre_url)

    # Create config with overrides
    return ScraperConfig(
        mode=config.mode,
        api_url=api_url,
        matchcentre_url=matchcentre_url,
        api_id=config.api_id,
        entity_id=config.entity_id
    )


def print_config(config: ScraperConfig):
    """Print configuration details"""
    print(f"🔧 Scraper Configuration:")
    print(f"   Mode: {config.mode.value.upper()}")
    print(f"   API URL: {config.api_url}")
    print(f"   Match Centre URL: {config.matchcentre_url}")
    print(f"   API ID: {config.api_id}")
    print(f"   Entity ID: {config.entity_id}")

    if config.is_mock():
        print(f"   ⚠️  RUNNING IN TEST MODE - Using mock data")
    else:
        print(f"   ✅ RUNNING IN PRODUCTION MODE - Using real KNCB API")


if __name__ == "__main__":
    # Demo
    print("="*80)
    print("Scraper Configuration Examples")
    print("="*80)

    print("\n1. Production mode:")
    prod_config = get_scraper_config(ScraperMode.PRODUCTION)
    print_config(prod_config)

    print("\n2. Mock mode:")
    mock_config = get_scraper_config(ScraperMode.MOCK)
    print_config(mock_config)

    print("\n3. Environment variable control:")
    print("   Set: export SCRAPER_MODE=mock")
    print("   Then call: get_scraper_config()")
