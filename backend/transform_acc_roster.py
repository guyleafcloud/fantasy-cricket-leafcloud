#!/usr/bin/env python3
"""
Transform ACC roster CSV from Dutch format to API-compatible format.

Input format (Dutch):
    Voornaam,Tussenvoegsel,Achternaam,Team

Output format (API):
    name,team_name,role,tier,is_active

Transformations:
- Combine name fields: Voornaam + Tussenvoegsel + Achternaam → CamelCase no spaces
- Fix team format: ACC1 → ACC 1, Zami-1 → ZAMI 1
- Filter invalid entries: nsp, afvoeren, blank teams
- Add default fields: role=ALL_ROUNDER, tier=HOOFDKLASSE, is_active=true

Usage:
    python3 transform_acc_roster.py /path/to/acc-pelim.csv
"""

import csv
import sys
from pathlib import Path


def combine_name(voornaam: str, tussenvoegsel: str, achternaam: str) -> str:
    """
    Combine name fields into CamelCase format without spaces.

    Examples:
        ('Berno', 'de', 'Klerk') → 'BernodeKlerk'
        ('Akash', '', 'Arora') → 'AkashArora'
        ('John Pieter', 'van', 'Vliet') → 'JohnPietervanVliet'
    """
    # Remove any leading/trailing spaces and combine
    parts = [p.strip() for p in [voornaam, tussenvoegsel, achternaam] if p.strip()]
    # Remove all spaces and combine
    return ''.join(parts).replace(' ', '')


def fix_team_format(team: str) -> str:
    """
    Convert team format to match database expectations.

    Examples:
        'ACC1' → 'ACC 1'
        'ACC2' → 'ACC 2'
        'Zami-1' → 'ZAMI 1'
        'Zami-2' → 'ZAMI 2'
    """
    team = team.strip()

    # Handle ACC teams
    if team.startswith('ACC'):
        # ACC1 → ACC 1, ACC2 → ACC 2, etc.
        return team.replace('ACC', 'ACC ')

    # Handle Zami teams
    if team.startswith('Zami'):
        # Zami-1 → ZAMI 1, Zami-2 → ZAMI 2
        return team.upper().replace('-', ' ')

    return team


def is_valid_entry(team: str) -> bool:
    """
    Check if entry should be included in the roster.

    Exclude:
        - 'nsp' (not selected preliminary)
        - 'afvoeren' (remove)
        - blank/empty teams
    """
    team = team.strip().lower()

    if not team:
        return False

    if team in ['nsp', 'afvoeren']:
        return False

    return True


def transform_roster(input_file: Path, output_file: Path = None):
    """
    Transform ACC roster CSV from Dutch format to API format.

    Args:
        input_file: Path to input CSV (acc-pelim.csv)
        output_file: Path to output CSV (default: acc-roster-transformed.csv)
    """
    if output_file is None:
        output_file = input_file.parent / 'acc-roster-transformed.csv'

    valid_count = 0
    invalid_count = 0
    invalid_reasons = {'nsp': 0, 'afvoeren': 0, 'blank': 0}

    with open(input_file, 'r', encoding='utf-8-sig') as infile:
        # utf-8-sig handles the BOM (byte order mark) at start of file
        reader = csv.DictReader(infile)

        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['name', 'team_name', 'role', 'tier', 'is_active']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                team = row['Team'].strip()

                # Check if valid entry
                if not is_valid_entry(team):
                    invalid_count += 1
                    if team.lower() == 'nsp':
                        invalid_reasons['nsp'] += 1
                    elif team.lower() == 'afvoeren':
                        invalid_reasons['afvoeren'] += 1
                    else:
                        invalid_reasons['blank'] += 1
                    continue

                # Combine name fields
                name = combine_name(
                    row['Voornaam'],
                    row['Tussenvoegsel'],
                    row['Achternaam']
                )

                # Fix team format
                team_name = fix_team_format(team)

                # Write transformed row
                writer.writerow({
                    'name': name,
                    'team_name': team_name,
                    'role': 'ALL_ROUNDER',  # Default, will be updated during confirmation
                    'tier': 'HOOFDKLASSE',
                    'is_active': 'true'
                })

                valid_count += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"ACC Roster Transformation Complete")
    print(f"{'='*60}")
    print(f"Input file:  {input_file}")
    print(f"Output file: {output_file}")
    print(f"\nValid entries:   {valid_count}")
    print(f"Invalid entries: {invalid_count}")
    print(f"  - nsp:         {invalid_reasons['nsp']}")
    print(f"  - afvoeren:    {invalid_reasons['afvoeren']}")
    print(f"  - blank team:  {invalid_reasons['blank']}")
    print(f"\nReady to upload via: POST /api/admin/players/bulk")
    print(f"{'='*60}\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 transform_acc_roster.py <input_csv_file>")
        print("\nExample:")
        print("  python3 transform_acc_roster.py /Users/guypa/Downloads/acc-pelim.csv")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    transform_roster(input_file)


if __name__ == '__main__':
    main()
