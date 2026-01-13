# UI/UX Google Sheets Authentication Fix

## Problem
The UI/UX event was showing 0 responses even though the Google Sheet had data.

## Root Cause
The issue was caused by **JWT authentication errors** due to:
1. Using deprecated `oauth2client` library
2. Possible service account key expiration

## Solutions Implemented

### 1. ✅ Updated Sheet Name Configuration
- Changed from: `"Markus 2K25 - UI/UX  (Responses)"`
- Changed to: `"UI/UX  (Responses)"`
- File: `backend/admin_analytics.py`

### 2. ✅ Migrated to Modern Authentication Library
- Replaced: `oauth2client` (deprecated)
- With: `google-auth` (modern, actively maintained)
- Updated files:
  - `backend/admin_analytics.py`
  - `debug_sheet_columns.py`
  - `requirements.txt`

### 3. ⚠️ **ACTION REQUIRED: Regenerate Service Account Key**

The JWT error indicates that your Google Service Account credentials need to be regenerated.

## 🔧 How to Fix the Authentication Error

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Select your project: **markus-481709**
3. Navigate to: **IAM & Admin** → **Service Accounts**

### Step 2: Find Your Service Account
- Look for: `admin-186@markus-481709.iam.gserviceaccount.com`

### Step 3: Create New Key
1. Click on the service account email
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create** - this will download a new JSON file

### Step 4: Replace the Old Key
1. Rename the downloaded file to `markus.json`
2. Replace the file at: `e:\MarkUs\backend\markus.json`
3. **IMPORTANT:** If using environment variables for deployment (Render, Heroku, etc.):
   - Copy the entire content of the new JSON file
   - Update the `GOOGLE_CREDENTIALS_JSON` environment variable with the new content

### Step 5: Verify It Works
Run this command to test:
```bash
python backend/admin_analytics.py
```

You should see output like:
```
Using credentials from local file...
📊 Fetching: MARKUS 2K26 -  CODE ADAPT (Responses)...
   ✅ Found X responses, Y unique participants
📊 Fetching: UI/UX  (Responses)...
   ✅ Found X responses, Y unique participants
```

## Alternative: Check System Time Sync

If regenerating the key doesn't work, ensure your system clock is synchronized:

### Windows:
1. Open Settings → Time & Language → Date & time
2. Enable "Set time automatically"
3. Click "Sync now"

Or run PowerShell as Administrator:
```powershell
Start-Service W32Time
w32tm /resync
```

## Files Changed (Already Pushed to GitHub)

1. **backend/admin_analytics.py**
   - Updated UI/UX sheet name
   - Migrated from `oauth2client` to `google.oauth2.service_account`

2. **requirements.txt**
   - Removed: `oauth2client`
   - Added: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`

3. **debug_sheet_columns.py**
   - Updated authentication method

## Commits
- Commit 1: `ab85977` - "Fix: Update UI/UX sheet name to match Google Sheets"
- Commit 2: `f739995` - "Fix: Migrate to google-auth to resolve JWT authentication errors"

## Next Steps

1. **Regenerate the service account key** (see instructions above)
2. Test the analytics with: `python backend/admin_analytics.py`
3. Check admin dashboard to verify UI/UX data appears
4. If deploying to production (Render/Heroku):
   - Update the `GOOGLE_CREDENTIALS_JSON` environment variable
   - Restart the application

## Need Help?

If the issue persists after regenerating the key:
1. Check that the service account has "Editor" or "Viewer" access to your Google Sheets
2. Verify the sheet name is exactly: `UI/UX  (Responses)` (note: two spaces before "(Responses)")
3. Share the error message from `python backend/admin_analytics.py`
