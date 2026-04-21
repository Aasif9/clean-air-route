# Supabase Transaction Pooler Setup Guide

## Overview
This guide will help you configure your Kolkata Clean Air Route project to use Supabase's Transaction Pooler for optimal performance with serverless deployments (Vercel frontend + Render backend).

## Why Transaction Pooler?
- **Ideal for serverless applications** like your Render backend
- **Stateless connections** - perfect for API endpoints
- **IPv4 compatible** - works with all hosting providers
- **Better resource utilization** - connection pooling reduces overhead

## Step 1: Get Your Supabase Credentials

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Select your project: `bnlcnefcjngoapdcijer`
3. Navigate to **Settings** → **Database**
4. Copy the **Connection string** for Transaction pooler:
   ```
   postgresql://postgres.bnlcnefcjngoapdcijer:[YOUR-PASSWORD]@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres
   ```

5. Navigate to **Settings** → **API**
6. Copy these keys:
   - **Project URL**: `https://bnlcnefcjngoapdcijer.supabase.co`
   - **service_role** key (for backend)
   - **anon** key (for frontend)

## Step 2: Configure Backend Environment

Create/update your `backend/.env` file:

```bash
# Google Maps API Key
Maps_API_KEY=your_google_maps_api_key

# Supabase Configuration
SUPABASE_URL=https://bnlcnefcjngoapdcijer.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database Connection - Transaction Pooler
DATABASE_URL=postgresql://postgres.bnlcnefcjngoapdcijer:YOUR_PASSWORD@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres

# Transaction Pooler Details (for reference)
DB_HOST=aws-1-ap-northeast-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.bnlcnefcjngoapdcijer
DB_PASSWORD=YOUR_PASSWORD

# Render Configuration
PORT=5002
```

## Step 3: Configure Frontend Environment

Update your `frontend/config.js` file:

```javascript
// Supabase configuration
const SUPABASE_CONFIG = {
    development: {
        url: 'https://bnlcnefcjngoapdcijer.supabase.co',
        anonKey: 'your_supabase_anon_key_here'
    },
    production: {
        url: 'https://bnlcnefcjngoapdcijer.supabase.co',
        anonKey: 'your_supabase_anon_key_here'
    }
};
```

## Step 4: Update Environment Variables on Render

1. Go to your Render dashboard
2. Select your backend service
3. Navigate to **Environment** tab
4. Add/update these environment variables:
   ```
   Maps_API_KEY=your_google_maps_api_key
   SUPABASE_URL=https://bnlcnefcjngoapdcijer.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   DATABASE_URL=postgresql://postgres.bnlcnefcjngoapdcijer:YOUR_PASSWORD@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres
   ```

## Step 5: Update Environment Variables on Vercel

1. Go to your Vercel dashboard
2. Select your frontend project
3. Navigate to **Settings** → **Environment Variables**
4. Add these variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://bnlcnefcjngoapdcijer.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
   ```

## Step 6: Verify Database Schema

Ensure your Supabase database has the required tables:

```sql
-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY,
    email TEXT,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Navigation routes table
CREATE TABLE IF NOT EXISTS navigation_routes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id),
    start_lat DECIMAL,
    start_lon DECIMAL,
    end_lat DECIMAL,
    end_lon DECIMAL,
    start_address TEXT,
    end_address TEXT,
    route_type TEXT,
    total_distance_km DECIMAL,
    total_time_min DECIMAL,
    average_aqi DECIMAL,
    min_aqi DECIMAL,
    max_aqi DECIMAL,
    exposure_score DECIMAL,
    coordinates JSONB,
    route_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE navigation_routes ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profiles" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can insert own profiles" ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can view own routes" ON navigation_routes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own routes" ON navigation_routes FOR INSERT WITH CHECK (auth.uid() = user_id);
```

## Step 7: Test the Connection

### Backend Test
```bash
cd backend
python api.py
```
You should see:
```
✅ Supabase connection established successfully
Starting Google Live API server on http://localhost:5002
```

### Frontend Test
1. Start frontend locally
2. Open browser console
3. Make a route request
4. Check for successful route saving messages

## Step 8: Deploy and Monitor

1. **Deploy to Render**: Push changes to trigger automatic deployment
2. **Deploy to Vercel**: Push changes to trigger automatic deployment
3. **Monitor logs**: Check both Render and Vercel logs for any connection issues

## Troubleshooting

### Common Issues:

1. **Connection Timeout**
   - Transaction pooler has a 30-second timeout
   - Ensure your API responses are faster than this

2. **Authentication Issues**
   - Verify your service_role key is correct
   - Check that the anon key is properly set for frontend

3. **Route Storage Issues**
   - Check backend logs for save attempts
   - Verify user_id is being passed correctly
   - Ensure database schema matches expected fields

### Debug Commands:

```bash
# Test database connection
curl -X POST https://your-backend.onrender.com/routes/save \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "route_data": {...}}'

# Check route history
curl https://your-backend.onrender.com/routes/history/test-user
```

## Performance Benefits

With the transaction pooler:
- ✅ **Reduced connection overhead**
- ✅ **Better scalability** for serverless
- ✅ **Automatic connection management**
- ✅ **IPv4 compatibility**
- ✅ **Improved route storage reliability**

## Monitoring

Monitor your Supabase usage in the dashboard:
- **Database**: Connection pool usage
- **API**: Request counts and errors
- **Storage**: Route data growth

Your route storage issue should now be resolved with the transaction pooler's improved connection handling!
