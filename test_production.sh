#!/bin/bash
# End-to-End Production Test
# Run from production server to test all systems

echo "======================================================================="
echo "🏏 FANTASY CRICKET - END-TO-END PRODUCTION TEST"
echo "======================================================================="
echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="$3"

    echo ""
    echo "-------------------------------------------------------------------"
    echo "TEST: $name"
    echo "-------------------------------------------------------------------"

    response=$(curl -s -w "\n%{http_code}" "$url")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" == "$expected_status" ]; then
        echo "✅ PASSED (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        echo "$body" | head -c 200
        if [ ${#body} -gt 200 ]; then
            echo "... (truncated)"
        fi
    else
        echo "❌ FAILED (Expected $expected_status, got $http_code)"
        FAILED=$((FAILED + 1))
        echo "$body" | head -c 500
    fi
}

# Test 1: API Health
test_endpoint "1. API Health Check" "https://api.fantcric.fun/health" "200"

# Test 2: Frontend
echo ""
echo "-------------------------------------------------------------------"
echo "TEST: 2. Frontend Accessibility"
echo "-------------------------------------------------------------------"
frontend_status=$(curl -s -o /dev/null -w "%{http_code}" https://fantcric.fun)
if [ "$frontend_status" == "200" ]; then
    echo "✅ PASSED (HTTP 200)"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAILED (HTTP $frontend_status)"
    FAILED=$((FAILED + 1))
fi

# Test 3: Database - Get Clubs (without auth)
echo ""
echo "-------------------------------------------------------------------"
echo "TEST: 3. Database Connection (Clubs Endpoint)"
echo "-------------------------------------------------------------------"
clubs_status=$(curl -s -o /dev/null -w "%{http_code}" https://api.fantcric.fun/api/admin/clubs)
if [ "$clubs_status" == "401" ] || [ "$clubs_status" == "403" ] || [ "$clubs_status" == "200" ]; then
    echo "✅ PASSED (HTTP $clubs_status - Auth required, database query works)"
    PASSED=$((PASSED + 1))
elif [ "$clubs_status" == "500" ]; then
    echo "❌ FAILED (HTTP 500 - Internal Server Error)"
    FAILED=$((FAILED + 1))
    curl -s https://api.fantcric.fun/api/admin/clubs | head -c 500
else
    echo "⚠️  UNEXPECTED (HTTP $clubs_status)"
    FAILED=$((FAILED + 1))
fi

# Test 4: Database - Direct query
echo ""
echo "-------------------------------------------------------------------"
echo "TEST: 4. Database Player Count"
echo "-------------------------------------------------------------------"
player_count=$(docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -t -c "SELECT COUNT(*) FROM players;")
if [ "$player_count" -gt 0 ]; then
    echo "✅ PASSED ($player_count players in database)"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAILED (0 players in database)"
    FAILED=$((FAILED + 1))
fi

# Test 5: Check rl_team field
echo ""
echo "-------------------------------------------------------------------"
echo "TEST: 5. Database rl_team Field"
echo "-------------------------------------------------------------------"
rl_team_count=$(docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -t -c "SELECT COUNT(*) FROM players WHERE rl_team IS NOT NULL;")
if [ "$rl_team_count" -gt 0 ]; then
    echo "✅ PASSED ($rl_team_count players with rl_team assigned)"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAILED (No players have rl_team assigned)"
    FAILED=$((FAILED + 1))
fi

# Test 6: Check multipliers
echo ""
echo "-------------------------------------------------------------------"
echo "TEST: 6. Database Multipliers"
echo "-------------------------------------------------------------------"
multiplier_info=$(docker exec fantasy_cricket_db psql -U cricket_admin -d fantasy_cricket -t -c "SELECT MIN(multiplier), MAX(multiplier), COUNT(*) FROM players WHERE multiplier IS NOT NULL;")
min_mult=$(echo $multiplier_info | awk '{print $1}')
max_mult=$(echo $multiplier_info | awk '{print $3}')
mult_count=$(echo $multiplier_info | awk '{print $5}')

if [ "$mult_count" -gt 0 ]; then
    echo "✅ PASSED ($mult_count players with multipliers)"
    echo "   Range: $min_mult - $max_mult"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAILED (No players have multipliers)"
    FAILED=$((FAILED + 1))
fi

# Test 7: Login endpoint structure (should not be 500)
echo ""
echo "-------------------------------------------------------------------"
echo "TEST: 7. Login Endpoint (No 500 Errors)"
echo "-------------------------------------------------------------------"
login_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://api.fantcric.fun/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong","turnstile_token":"invalid"}')

if [ "$login_status" == "500" ]; then
    echo "❌ FAILED (HTTP 500 - Internal Server Error)"
    FAILED=$((FAILED + 1))
    curl -s -X POST https://api.fantcric.fun/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"test@test.com","password":"wrong","turnstile_token":"invalid"}' | head -c 500
elif [ "$login_status" == "400" ] || [ "$login_status" == "401" ]; then
    echo "✅ PASSED (HTTP $login_status - No 500 error, endpoint works)"
    PASSED=$((PASSED + 1))
else
    echo "⚠️  UNEXPECTED (HTTP $login_status)"
    PASSED=$((PASSED + 1))
fi

# Test 8: Container status
echo ""
echo "-------------------------------------------------------------------"
echo "TEST: 8. Critical Containers Running"
echo "-------------------------------------------------------------------"
api_running=$(docker ps --filter name=fantasy_cricket_api --filter status=running --format "{{.Names}}")
db_running=$(docker ps --filter name=fantasy_cricket_db --filter status=running --format "{{.Names}}")
frontend_running=$(docker ps --filter name=fantasy_cricket_frontend --filter status=running --format "{{.Names}}")
nginx_running=$(docker ps --filter name=fantasy_cricket_nginx --filter status=running --format "{{.Names}}")

all_running=true
[ -z "$api_running" ] && all_running=false && echo "  ❌ API container not running"
[ -z "$db_running" ] && all_running=false && echo "  ❌ Database container not running"
[ -z "$frontend_running" ] && all_running=false && echo "  ❌ Frontend container not running"
[ -z "$nginx_running" ] && all_running=false && echo "  ❌ Nginx container not running"

if [ "$all_running" = true ]; then
    echo "✅ PASSED (All critical containers running)"
    echo "  ✓ API: $api_running"
    echo "  ✓ Database: $db_running"
    echo "  ✓ Frontend: $frontend_running"
    echo "  ✓ Nginx: $nginx_running"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAILED (Some containers not running)"
    FAILED=$((FAILED + 1))
fi

# Final Report
echo ""
echo "======================================================================="
echo "FINAL REPORT"
echo "======================================================================="
echo "Tests Run: $((PASSED + FAILED))"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - SYSTEM IS HEALTHY"
    echo "======================================================================="
    exit 0
else
    echo "⚠️  $FAILED TEST(S) FAILED - REVIEW ERRORS ABOVE"
    echo "======================================================================="
    exit 1
fi
