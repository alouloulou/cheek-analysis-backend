# Redeploy Backend to Render

The backend code has been updated to fix the database column name issues. You need to redeploy to Render.

## Quick Redeploy Steps:

### Option 1: Auto-Deploy (if connected to GitHub)
1. **Commit changes** to your GitHub repository:
   ```bash
   git add .
   git commit -m "Fix database column names for Supabase"
   git push
   ```

2. **Render will auto-deploy** (if auto-deploy is enabled)
   - Check your Render dashboard
   - Should see "Deploying..." status
   - Wait for "Live" status

### Option 2: Manual Deploy
1. **Go to your Render dashboard**
2. **Find your service**: `cheek-analysis-backend`
3. **Click "Manual Deploy"** → "Deploy latest commit"
4. **Wait for deployment** (2-3 minutes)

## What Was Fixed:

- ✅ **Backend**: Fixed `analysis_limit` → `max_analyses` in supabase_client.py
- ✅ **Flutter**: Fixed `analysis_limit` → `max_analyses` in app_state.dart
- ✅ **Backend**: Fixed table structure to match actual Supabase schema

## Test After Redeploy:

1. **Test backend connection**:
   - Open Flutter app
   - Profile → Backend Test
   - Should show "Connected ✅"

2. **Test full analysis flow**:
   - Camera → Take photo → Confirm
   - Should complete without database errors
   - Should save analysis results to Supabase

The error `Could not find the 'analysis_limit' column` should now be resolved! 🎉
