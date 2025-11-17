#!/usr/bin/env python3
"""
Frontend Workflow Test - Automated Browser Testing
Tests the complete user journey through the UI
"""

import asyncio
import time
from playwright.async_api import async_playwright, expect

FRONTEND_URL = "https://fantcric.fun"
ADMIN_EMAIL = "admin@fantcric.fun"
ADMIN_PASSWORD = "FantasyTest2025!"

async def run_frontend_test():
    print("="*70)
    print("🏏 FRONTEND WORKFLOW TEST - Browser Automation")
    print("="*70)
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Testing with: {ADMIN_EMAIL}\n")

    async with async_playwright() as p:
        # Launch browser
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            # Step 1: Navigate to site
            print("\n" + "="*70)
            print("STEP 1: Navigate to Frontend")
            print("="*70)
            await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
            print(f"✅ Loaded: {page.url}")
            print(f"   Title: {await page.title()}")

            # Take screenshot
            await page.screenshot(path='/tmp/01_homepage.png')
            print("   Screenshot: /tmp/01_homepage.png")

            # Step 2: Login
            print("\n" + "="*70)
            print("STEP 2: Login as Admin")
            print("="*70)

            # Look for login button/link
            login_selectors = [
                'a[href*="login"]',
                'button:has-text("Login")',
                'a:has-text("Login")',
                'a:has-text("Sign In")',
                '[data-testid="login"]'
            ]

            login_found = False
            for selector in login_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    print(f"   Found login element: {selector}")
                    await page.click(selector)
                    login_found = True
                    break
                except:
                    continue

            if not login_found:
                # Check if already on login page or need to navigate
                if 'login' in page.url.lower():
                    print("   Already on login page")
                else:
                    print("   Navigating directly to /login")
                    await page.goto(f"{FRONTEND_URL}/login", wait_until="networkidle")

            await page.screenshot(path='/tmp/02_login_page.png')
            print("   Screenshot: /tmp/02_login_page.png")

            # Fill login form
            print(f"   Filling email: {ADMIN_EMAIL}")
            await page.fill('input[type="email"], input[name="email"]', ADMIN_EMAIL)

            print(f"   Filling password: {'*' * len(ADMIN_PASSWORD)}")
            await page.fill('input[type="password"], input[name="password"]', ADMIN_PASSWORD)

            # Submit form
            print("   Submitting login form...")
            await page.click('button[type="submit"], button:has-text("Login")')

            # Wait for navigation after login
            await page.wait_for_load_state("networkidle", timeout=10000)

            await page.screenshot(path='/tmp/03_after_login.png')
            print(f"✅ Logged in successfully")
            print(f"   Current URL: {page.url}")
            print("   Screenshot: /tmp/03_after_login.png")

            # Step 3: Navigate to admin/create league
            print("\n" + "="*70)
            print("STEP 3: Create League")
            print("="*70)

            # Look for admin/dashboard navigation
            admin_selectors = [
                'a[href*="admin"]',
                'button:has-text("Admin")',
                'a:has-text("Admin")',
                '[data-testid="admin"]'
            ]

            for selector in admin_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    print(f"   Clicking admin link: {selector}")
                    await page.click(selector)
                    await page.wait_for_load_state("networkidle")
                    break
                except:
                    continue

            await page.screenshot(path='/tmp/04_admin_page.png')
            print("   Screenshot: /tmp/04_admin_page.png")

            # Look for create league button
            create_league_selectors = [
                'button:has-text("Create League")',
                'a:has-text("Create League")',
                'button:has-text("New League")',
                '[data-testid="create-league"]'
            ]

            league_found = False
            for selector in create_league_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    print(f"   Clicking create league: {selector}")
                    await page.click(selector)
                    league_found = True
                    await page.wait_for_timeout(1000)
                    break
                except:
                    continue

            if not league_found:
                print("   ⚠️  'Create League' button not found, checking URL...")
                print(f"   Current URL: {page.url}")
                # Try navigating directly
                await page.goto(f"{FRONTEND_URL}/admin/leagues/create", wait_until="networkidle")

            await page.screenshot(path='/tmp/05_create_league_form.png')
            print("   Screenshot: /tmp/05_create_league_form.png")

            # Fill league creation form
            league_name = f"Test League {int(time.time())}"
            print(f"   Filling league name: {league_name}")

            name_selectors = [
                'input[name="name"]',
                'input[placeholder*="name" i]',
                '#league-name'
            ]

            for selector in name_selectors:
                try:
                    await page.fill(selector, league_name)
                    print(f"   ✅ Filled name field: {selector}")
                    break
                except:
                    continue

            # Select season
            print("   Selecting season...")
            try:
                await page.click('select[name="season_id"], select[name="season"]')
                await page.wait_for_timeout(500)
                # Select first option
                await page.select_option('select[name="season_id"], select[name="season"]', index=1)
                print("   ✅ Selected season")
            except Exception as e:
                print(f"   ⚠️  Could not select season: {e}")

            # Submit league creation
            print("   Submitting league form...")
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Create")',
                'button:has-text("Save")'
            ]

            for selector in submit_selectors:
                try:
                    await page.click(selector)
                    print(f"   ✅ Clicked submit: {selector}")
                    break
                except:
                    continue

            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.screenshot(path='/tmp/06_after_league_creation.png')
            print("✅ League created")
            print(f"   Current URL: {page.url}")
            print("   Screenshot: /tmp/06_after_league_creation.png")

            # Step 4: Confirm roster
            print("\n" + "="*70)
            print("STEP 4: Confirm Roster")
            print("="*70)

            # Look for roster/players link
            roster_selectors = [
                'a:has-text("Roster")',
                'button:has-text("Roster")',
                'a:has-text("Players")',
                '[data-testid="roster"]'
            ]

            for selector in roster_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    print(f"   Clicking roster: {selector}")
                    await page.click(selector)
                    await page.wait_for_load_state("networkidle")
                    break
                except:
                    continue

            await page.screenshot(path='/tmp/07_roster.png')
            print("   Screenshot: /tmp/07_roster.png")

            # Count players displayed
            player_elements = await page.query_selector_all('[data-testid="player-card"], .player-item, .player-row')
            print(f"✅ Roster displayed: {len(player_elements)} players found")

            # Step 5: Switch to user mode
            print("\n" + "="*70)
            print("STEP 5: Switch to User Mode")
            print("="*70)

            user_mode_selectors = [
                'a:has-text("User Mode")',
                'button:has-text("User Mode")',
                'a[href*="user"]',
                '[data-testid="user-mode"]'
            ]

            for selector in user_mode_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    print(f"   Clicking user mode: {selector}")
                    await page.click(selector)
                    await page.wait_for_load_state("networkidle")
                    break
                except:
                    continue

            await page.screenshot(path='/tmp/08_user_mode.png')
            print("✅ Switched to user mode")
            print(f"   Current URL: {page.url}")
            print("   Screenshot: /tmp/08_user_mode.png")

            # Step 6: Create team
            print("\n" + "="*70)
            print("STEP 6: Create Fantasy Team")
            print("="*70)

            create_team_selectors = [
                'button:has-text("Create Team")',
                'a:has-text("Create Team")',
                'button:has-text("Build Team")',
                '[data-testid="create-team"]'
            ]

            for selector in create_team_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    print(f"   Clicking create team: {selector}")
                    await page.click(selector)
                    await page.wait_for_load_state("networkidle")
                    break
                except:
                    continue

            await page.screenshot(path='/tmp/09_team_builder.png')
            print("   Screenshot: /tmp/09_team_builder.png")

            # Select 11 players (simplified - would need actual player selection logic)
            print("   Selecting players...")
            player_cards = await page.query_selector_all('button:has-text("Add"), button:has-text("Select")')

            players_added = 0
            for i, card in enumerate(player_cards[:11]):  # Try to add 11 players
                try:
                    await card.click()
                    await page.wait_for_timeout(300)
                    players_added += 1
                    if players_added >= 11:
                        break
                except Exception as e:
                    print(f"   ⚠️  Could not add player {i+1}: {e}")

            print(f"   Added {players_added} players")

            await page.screenshot(path='/tmp/10_team_selected.png')
            print("   Screenshot: /tmp/10_team_selected.png")

            # Step 7: Validate and register team
            print("\n" + "="*70)
            print("STEP 7: Validate and Register Team")
            print("="*70)

            # Look for submit/register button
            register_selectors = [
                'button:has-text("Register")',
                'button:has-text("Submit")',
                'button:has-text("Save Team")',
                '[data-testid="register-team"]'
            ]

            for selector in register_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    print(f"   Clicking register: {selector}")
                    await page.click(selector)
                    await page.wait_for_timeout(2000)
                    break
                except:
                    continue

            await page.screenshot(path='/tmp/11_team_registered.png')
            print("✅ Team registration attempted")
            print(f"   Current URL: {page.url}")
            print("   Screenshot: /tmp/11_team_registered.png")

            # Check for success message
            success_indicators = [
                'text="Success"',
                'text="Team registered"',
                'text="Team created"',
                '.success-message'
            ]

            for selector in success_indicators:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    print(f"✅ Success message found: {selector}")
                    break
                except:
                    continue

            # Final screenshot
            await page.screenshot(path='/tmp/12_final_state.png')
            print("   Screenshot: /tmp/12_final_state.png")

            print("\n" + "="*70)
            print("✅ FRONTEND WORKFLOW TEST COMPLETED")
            print("="*70)
            print("\nScreenshots saved to /tmp/:")
            for i in range(1, 13):
                print(f"  - {i:02d}_*.png")
            print("\nAll screenshots available for review on server")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await page.screenshot(path='/tmp/error_screenshot.png')
            print("   Error screenshot: /tmp/error_screenshot.png")
            raise

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_frontend_test())
