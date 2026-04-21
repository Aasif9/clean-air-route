# 🚀 Deployment Guide: Render + Vercel with Supabase Transaction Pooler

## 📋 Step-by-Step Instructions

### 1️⃣ Push Changes to GitHub

First, let's commit and push all your changes:

```bash
# Add all changes
git add .

# Commit changes
git commit -m "Configure Supabase transaction pooler with retry logic and improved error handling"

# Push to GitHub
git push origin main
```

### 2️⃣ Configure Render (Backend)

#### Environment Variables Setup:

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Select your backend service: `kolkata-clean-air-route`
3. Navigate to **Environment** tab
4. Add/update these environment variables:

```
Maps_API_KEY=your_google_maps_api_key_here
SUPABASE_URL=https://bnlcnefcjngoapdcijer.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJubGNuZWZjam5nb2FwZGNpamVyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMzNjMwNCwiZXhwIjoyMDkxOTEyMzA0fQ.wUzgp7WlR2B_TVGy3HT70z91SRZIx68ZEkgZE0mDJJo
DATABASE_URL=postgresql://postgres.bnlcnefcjngoapdcijer:KCoxhMjHBo0Aszq8@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres
DB_HOST=aws-1-ap-northeast-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.bnlcnefcjngoapdcijer
DB_PASSWORD=KCoxhMjHBo0Aszq8
PORT=5002
```

5. Click **Save Changes**
6. **Manual Deploy** → **Deploy Latest Commit** to trigger deployment with new environment variables

### 3️⃣ Configure Vercel (Frontend)

#### Environment Variables Setup:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your frontend project
3. Navigate to **Settings** → **Environment Variables**
4. Add these variables:

```
NEXT_PUBLIC_SUPABASE_URL=https://bnlcnefcjngoapdcijer.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJubGNuZWZjam5nb2FwZGNpamVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzYzMDQsImV4cCI6MjA5MTkxMjMwNH0.wvUyDePWbUvGvksin82JhVIxbDXUuV1Y4O0N2FvwpCQ
```

5. Click **Save**
6. **Redeploy** → **Redeploy** to trigger deployment with new environment variables

### 4️⃣ Verify Deployment

#### Backend Verification:
```bash
# Test backend health
curl https://kolkata-clean-air-route.onrender.com/

# Test route endpoint
curl "https://kolkata-clean-air-route.onrender.com/routes/clean?start_lat=22.5750&start_lon=88.3500&end_lat=22.5800&end_lon=88.3800"
```

#### Frontend Verification:
1. Open your Vercel frontend URL
2. Open browser console (F12)
3. Try creating a route
4. Check console for success messages like:
   ```
   [API] Saved route 1 to Supabase: 12345678-1234-1234-1234-123456789012
   [API] Successfully saved 3/3 routes to Supabase
   ```

### 5️⃣ Test Route Storage

1. **Create a test user**:
   ```bash
   curl -X POST https://kolkata-clean-air-route.onrender.com/users/create \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user-123", "email": "test@example.com", "full_name": "Test User"}'
   ```

2. **Test multi-route with user ID**:
   ```bash
   curl "https://kolkata-clean-air-route.onrender.com/routes/multi?start_lat=22.5750&start_lon=88.3500&end_lat=22.5800&end_lon=88.3800&user_id=test-user-123"
   ```

3. **Check route history**:
   ```bash
   curl https://kolkata-clean-air-route.onrender.com/routes/history/test-user-123
   ```

### 6️⃣ Monitor Logs

#### Render Logs:
1. Go to Render Dashboard → Your Service → **Logs**
2. Look for:
   ```
   ✅ Supabase connection established successfully
   [API] Saved route 1 to Supabase (attempt 1): uuid-here
   [API] Successfully saved 3/3 routes to Supabase
   ```

#### Vercel Logs:
1. Go to Vercel Dashboard → Your Project → **Logs**
2. Check for any frontend errors

## 🔧 Troubleshooting

### Common Issues & Solutions:

#### ❌ "Supabase connection failed"
- **Solution**: Verify environment variables in Render dashboard
- **Check**: Service role key and database URL are correct

#### ❌ "Route not saving to database"
- **Solution**: Check user_id is being passed correctly
- **Check**: Backend logs for save attempts and errors

#### ❌ "CORS errors"
- **Solution**: Ensure frontend URL is added to Supabase CORS settings
- **Check**: Supabase Dashboard → Settings → API → CORS

#### ❌ "Environment variables not working"
- **Solution**: Redeploy both services after adding variables
- **Check**: Variables are correctly copied (no extra spaces)

### 📞 Support Commands:

```bash
# Test database connection directly
curl -X POST https://kolkata-clean-air-route.onrender.com/routes/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "route_data": {
      "start_lat": 22.5750,
      "start_lon": 88.3500,
      "end_lat": 22.5800,
      "end_lon": 88.3800,
      "route_type": "test_route",
      "analysis": {"total_distance_km": 5.2, "average_aqi": 120}
    }
  }'

# Check all routes (admin endpoint)
curl https://kolkata-clean-air-route.onrender.com/routes/history
```

## ✅ Success Indicators

You'll know everything is working when you see:

1. **Backend**: `✅ Supabase connection established successfully` in logs
2. **Frontend**: No console errors, routes display correctly
3. **Route Storage**: `[API] Successfully saved X/Y routes to Supabase` messages
4. **Database**: Routes appear in Supabase dashboard → Table Editor

## 🎯 Next Steps

Once deployed and working:
- Monitor route storage in Supabase dashboard
- Check Render logs for any connection issues
- Test with multiple users to ensure isolation
- Scale up if needed (transaction pooler handles load well)

Your route storage issue should now be completely resolved! 🎉
