#!/usr/bin/env python3
"""
Extract ALL API endpoints from endpoint files
"""

import re
import os

endpoint_files = [
    '/Users/guypa/Github/fantasy-cricket-leafcloud/backend/admin_endpoints.py',
    '/Users/guypa/Github/fantasy-cricket-leafcloud/backend/api_endpoints.py',
    '/Users/guypa/Github/fantasy-cricket-leafcloud/backend/league_endpoints.py',
    '/Users/guypa/Github/fantasy-cricket-leafcloud/backend/player_endpoints.py',
    '/Users/guypa/Github/fantasy-cricket-leafcloud/backend/user_auth_endpoints.py',
    '/Users/guypa/Github/fantasy-cricket-leafcloud/backend/user_team_endpoints.py',
]

all_endpoints = []

for filepath in endpoint_files:
    filename = os.path.basename(filepath)

    with open(filepath, 'r') as f:
        content = f.read()

    # Extract router prefix
    prefix_match = re.search(r'router\s*=\s*APIRouter\([^)]*prefix=["\']([^"\']+)', content)
    prefix = prefix_match.group(1) if prefix_match else "/api"

    # Extract all route decorators
    route_pattern = r'@router\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']'
    routes = re.findall(route_pattern, content)

    print(f"\n{'='*80}")
    print(f"File: {filename}")
    print(f"Prefix: {prefix}")
    print(f"{'='*80}")

    for method, path in routes:
        full_path = prefix + path if not path.startswith('/') else prefix + path
        print(f"  {method.upper():7s} {full_path}")
        all_endpoints.append({
            'file': filename,
            'method': method.upper(),
            'path': full_path,
            'prefix': prefix
        })

print(f"\n{'='*80}")
print(f"TOTAL ENDPOINTS FOUND: {len(all_endpoints)}")
print(f"{'='*80}")

# Save to JSON
import json
with open('/tmp/all_endpoints.json', 'w') as f:
    json.dump(all_endpoints, f, indent=2)

print(f"\nEndpoints saved to: /tmp/all_endpoints.json")
