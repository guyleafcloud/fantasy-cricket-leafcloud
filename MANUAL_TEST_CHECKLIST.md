# Manual Testing Checklist
## Frontend Complete Workflow Test

### What Has Been Fixed (Backend)
✅ **Leagues endpoint** - No longer returns 500 errors
✅ **Clubs endpoint** - No longer returns 500 errors
✅ **Database schema** - leagues table now has all required columns
✅ **Player roster** - All 513 players with rl_team and multipliers

### Manual Testing Steps

---

## Step 1: Login as Admin
1. Navigate to: **https://fantcric.fun**
2. Click **Login** button
3. Enter credentials:
   - Email: `admin@fantcric.fun`
   - Password: `FantasyTest2025!`
4. Click **Submit/Login**

**Expected Result:** ✅ Successfully logged in, redirected to dashboard/admin panel

**If Failed:** Check browser console (F12) for errors, screenshot the error

---

## Step 2: View Seasons
1. Navigate to **Admin** → **Seasons** (or similar menu)
2. Verify you can see the list of seasons

**Expected Result:** ✅ Shows 2 seasons (2025 active, 2026 inactive)

**If Failed:** Screenshot error, check if 500 error appears

---

## Step 3: Create a League
1. Click **Create League** or **New League** button
2. Fill in the form:
   - League Name: `Test League [your name]`
   - Description: `Test league for verification`
   - Select Season: **2025**
   - Select Club: **ACC**
   - Squad Size: **11**
   - Budget: **500** (or default)
   - Transfers per season: **4** (or default)
   - Public: **Yes** ✓
   - Max participants: **100** (or default)
3. Click **Create** or **Save**

**Expected Result:** ✅ League created successfully, shows league code (e.g., "ABC123")

**If Failed:**
- Screenshot the error
- Check browser console for 500 errors
- Note the exact error message

---

## Step 4: Confirm Roster Loads
1. After creating league, navigate to **Roster** or **Players** view
2. Verify the player list loads

**Expected Result:** ✅ Shows **513 players** from ACC
- Each player should have:
  - Name
  - RL Team (ACC 1-6, ZAMI 1, U13, U15, U17)
  - Role (BATSMAN, BOWLER, ALL_ROUNDER, WICKET_KEEPER)
  - Multiplier (0.69 - 5.0)
  - Price

**If Failed:**
- Screenshot the error
- Check if players = 0 or if endpoint returns 500

---

## Step 5: Switch to User Mode
1. Look for **User Mode** or **Exit Admin** button/link
2. Click it
3. Navigate to **Leagues** or **My Leagues**
4. Join the league you just created using the league code

**Expected Result:** ✅ Successfully joined league, can view league details

**If Failed:** Note what happens when trying to join

---

## Step 6: Create Fantasy Team
1. Click **Create Team** or **Build Team**
2. Enter team name: `Test Team [your name]`
3. Start selecting players

**Player Selection Rules to Test:**
- ✅ Must select exactly **11 players**
- ✅ Budget must not exceed **500 credits** (or configured budget)
- ✅ Must have players from all 10 RL teams (ACC 1-6, ZAMI 1, U13, U15, U17 = 10 teams)
- ✅ Min **3 batsmen** required
- ✅ Min **3 bowlers** required
- ✅ Must have **1 wicket-keeper**
- ✅ Max **2 players** from any single RL team
- ✅ Must select **1 captain** (2× points)
- ✅ Must select **1 vice-captain** (1.5× points)

**Test Invalid Selections:**
Try to violate rules and confirm the UI prevents it:
- ❌ Select 3 players from same RL team → Should show error
- ❌ Select less than 3 batsmen → Should show error
- ❌ Exceed budget → Should show error
- ❌ Miss a wicket-keeper → Should show error

**Expected Result:** ✅ UI validates rules and prevents invalid teams

**If Failed:** Note which rule is NOT being enforced

---

## Step 7: Register Team
1. After selecting valid 11 players
2. Assign captain (click star icon or similar)
3. Assign vice-captain
4. Click **Register Team** or **Save Team**

**Expected Result:** ✅ Team registered successfully
- Shows confirmation message
- Team appears in "My Teams" or league standings
- Can view team details

**If Failed:**
- Screenshot error
- Check if 500 error or validation error
- Note exact error message

---

## Step 8: Verify Team is Saved
1. Navigate to **My Teams** or **League** view
2. Confirm your team appears
3. Click on team to view details
4. Verify all 11 players are shown correctly

**Expected Result:** ✅ Team persists and displays correctly

---

## Common Issues to Check

### API Errors (500)
If you see any 500 errors:
1. Open browser console (F12)
2. Go to **Network** tab
3. Click on the failing request
4. Screenshot the error response
5. Send me the endpoint URL and error message

### Validation Not Working
If rules aren't enforced:
1. Note which specific rule fails
2. Try to register an invalid team
3. Screenshot what happens

### Players Not Loading
If roster shows 0 players or errors:
1. Check browser console
2. Check if `/api/admin/clubs/{club_id}/players` returns 500
3. Send screenshot

---

## Testing Summary Template

After testing, please report:

```
STEP 1 - Login: ✅ / ❌ [error details]
STEP 2 - View Seasons: ✅ / ❌ [error details]
STEP 3 - Create League: ✅ / ❌ [error details]
STEP 4 - Roster Loads: ✅ / ❌ [error details if any]
STEP 5 - User Mode: ✅ / ❌ [error details]
STEP 6 - Create Team: ✅ / ❌ [error details]
STEP 7 - Register Team: ✅ / ❌ [error details]
STEP 8 - Verify Team: ✅ / ❌ [error details]

Rule Validation Tests:
- Max 2 per RL team: ✅ / ❌
- Min 3 batsmen: ✅ / ❌
- Min 3 bowlers: ✅ / ❌
- Wicket-keeper required: ✅ / ❌
- Budget enforcement: ✅ / ❌
- 11 players required: ✅ / ❌
```

---

## Database Verification (Already Completed)

I've verified the backend is healthy:
- ✅ 513 players in database with multipliers (0.69-5.0)
- ✅ All players have rl_team assigned
- ✅ Leagues table schema fixed
- ✅ Clubs endpoint returns proper data
- ✅ 0 API 500 errors in last 5 minutes
- ✅ All containers running healthy

Now you need to test the frontend workflow manually.
