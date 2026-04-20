# Supabase Integration Troubleshooting Guide

## 📋 Table of Contents
1. [Common Connection Issues](#common-connection-issues)
2. [Database & Schema Problems](#database--schema-problems)
3. [Authentication Issues](#authentication-issues)
4. [Flutter Integration Problems](#flutter-integration-problems)
5. [Backend Integration Issues](#backend-integration-issues)
6. [Performance & Optimization](#performance--optimization)
7. [Debugging Tools](#debugging-tools)
8. [Best Practices](#best-practices)

---

## 🔌 Common Connection Issues

### Issue: "Connection refused" or "Unable to connect to Supabase"

#### **Symptoms:**
- Backend crashes on startup
- Flutter app shows connection errors
- API calls timeout

#### **Solutions:**

1. **Check Environment Variables**
```bash
# Verify your .env file
cat .env

# Should contain:
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

2. **Test Connection Manually**
```bash
# Test with curl
curl -H "apikey: YOUR_ANON_KEY" \
     -H "Authorization: Bearer YOUR_ANON_KEY" \
     https://your-project-id.supabase.co/rest/v1/user_profiles

# Should return: [] (empty array) or data
```

3. **Check Project URL Format**
```bash
# Correct format: https://project-id.supabase.co
# Incorrect formats:
# - http://project-id.supabase.co (missing https)
# - https://project-id.supabase.co/ (trailing slash)
# - project-id.supabase.co (missing protocol)
```

4. **Verify API Keys**
```bash
# In Supabase Dashboard:
# Settings > API > Copy the anon key
# Ensure no extra spaces or characters
```

---

## 🗄️ Database & Schema Problems

### Issue: "Relation does not exist" or "Table not found"

#### **Symptoms:**
- SQL queries fail
- API returns 404 errors
- Flutter app crashes on data fetch

#### **Solutions:**

1. **Check Table Existence**
```sql
-- In Supabase SQL Editor:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'navigation_routes';

-- Should return your table name
```

2. **Verify Schema Permissions**
```sql
-- Check if tables are in public schema
SELECT schemaname, tablename FROM pg_tables 
WHERE tablename = 'navigation_routes';

-- Should show: public | navigation_routes
```

3. **Recreate Tables if Needed**
```sql
-- Drop and recreate if corrupted
DROP TABLE IF EXISTS navigation_routes CASCADE;

-- Recreate with proper schema
CREATE TABLE public.navigation_routes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  -- ... rest of columns
);
```

### Issue: Row Level Security (RLS) Policy Errors

#### **Symptoms:**
- "Permission denied" errors
- Can't insert/update data
- Empty results from queries

#### **Solutions:**

1. **Check RLS Status**
```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables 
WHERE schemaname = 'public';

-- Should show: navigation_routes | true
```

2. **Verify Policies Exist**
```sql
-- List all policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'navigation_routes';
```

3. **Fix Common Policy Issues**
```sql
-- Enable RLS if disabled
ALTER TABLE navigation_routes ENABLE ROW LEVEL SECURITY;

-- Add missing policies
CREATE POLICY "Users can view own routes" 
ON navigation_routes FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own routes" 
ON navigation_routes FOR INSERT 
WITH CHECK (auth.uid() = user_id);
```

---

## 🔐 Authentication Issues

### Issue: "Invalid JWT" or "Authentication failed"

#### **Symptoms:**
- Login attempts fail
- API returns 401 errors
- User session problems

#### **Solutions:**

1. **Check JWT Configuration**
```bash
# In Supabase Dashboard:
# Settings > Auth > JWT Settings
# Verify issuer and audience
```

2. **Test Authentication Flow**
```dart
// In Flutter, debug auth state
Supabase.instance.client.auth.onAuthStateChange.listen((data) {
  print('Auth event: ${data.event}');
  print('Session: ${data.session?.accessToken}');
});
```

3. **Verify User Profile Creation**
```sql
-- Check if user profile exists
SELECT * FROM user_profiles WHERE id = 'your-user-id';

-- Manually create if missing
INSERT INTO user_profiles (id, email, full_name) 
VALUES ('user-id', 'email@example.com', 'User Name');
```

### Issue: CORS Errors

#### **Symptoms:**
- Browser blocks requests
- "Access-Control-Allow-Origin" errors
- Flutter web app fails

#### **Solutions:**

1. **Configure CORS in Supabase**
```sql
-- In Supabase SQL Editor:
-- Add your domains to allowed origins
-- This is typically done in dashboard settings
```

2. **Check Request Headers**
```bash
# Verify your requests include proper headers
curl -H "apikey: YOUR_ANON_KEY" \
     -H "Authorization: Bearer YOUR_ANON_KEY" \
     -H "Content-Type: application/json" \
     https://your-project-id.supabase.co/rest/v1/your-table
```

---

## 📱 Flutter Integration Problems

### Issue: "Supabase not initialized" Error

#### **Symptoms:**
- App crashes on startup
- Supabase.instance is null
- Initialization errors

#### **Solutions:**

1. **Check Initialization Order**
```dart
// main.dart - ensure proper initialization
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Supabase FIRST
  await Supabase.initialize(
    url: SupabaseConfig.url,
    anonKey: SupabaseConfig.anonKey,
  );
  
  runApp(MyApp());
}
```

2. **Verify Configuration**
```dart
// Check if configuration is correct
class SupabaseConfig {
  static const String url = 'https://your-project-id.supabase.co';
  static const String anonKey = 'your-exact-anon-key';
  
  // Test initialization
  static Future<void> testConnection() async {
    try {
      final client = Supabase.instance.client;
      final response = await client.from('user_profiles').select('count');
      print('✅ Supabase connection successful');
    } catch (e) {
      print('❌ Supabase connection failed: $e');
    }
  }
}
```

3. **Handle Platform-Specific Issues**
```bash
# For iOS, check Info.plist
# For Android, check AndroidManifest.xml
# Ensure internet permissions are present

# Clean and rebuild
flutter clean
flutter pub get
flutter run
```

### Issue: Real-time Subscriptions Not Working

#### **Symptoms:**
- No live updates
- Subscription errors
- Connection drops

#### **Solutions:**

1. **Check Real-time Setup**
```dart
// Enable real-time for table
final subscription = Supabase.instance.client
    .channel('public:navigation_routes')
    .onPostgresChanges(
      event: PostgresChangeEvent.all,
      schema: 'public',
      table: 'navigation_routes',
      callback: (payload) {
        print('Change received: ${payload}');
      },
    )
    .subscribe();

// Check subscription status
print('Subscription status: ${subscription.status}');
```

2. **Verify Real-time Permissions**
```sql
-- Check real-time policies
SELECT * FROM pg_policies 
WHERE tablename = 'navigation_routes';

-- Ensure real-time is enabled
ALTER TABLE navigation_routes REPLICA IDENTITY FULL;
```

---

## 🔧 Backend Integration Issues

### Issue: Python Supabase Client Errors

#### **Symptoms:**
- Import errors
- Connection timeouts
- Authentication failures

#### **Solutions:**

1. **Check Python Dependencies**
```bash
# Verify installation
pip list | grep supabase

# Reinstall if needed
pip uninstall supabase
pip install supabase

# Check requirements.txt
cat requirements.txt | grep supabase
```

2. **Test Python Connection**
```python
# Create test script
test_supabase.py:
from supabase import create_client
import os

def test_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    try:
        client = create_client(url, key)
        result = client.table('user_profiles').select('count').execute()
        print(f"✅ Connection successful: {result.data}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

3. **Debug Environment Variables**
```python
# Add to your supabase_service.py
import os
from dotenv import load_dotenv

load_dotenv()

def debug_env():
    print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
    print("SUPABASE_ANON_KEY:", os.getenv("SUPABASE_ANON_KEY")[:20] + "...")
    
    if not os.getenv("SUPABASE_URL"):
        print("❌ SUPABASE_URL not set")
    if not os.getenv("SUPABASE_ANON_KEY"):
        print("❌ SUPABASE_ANON_KEY not set")

# Call this during initialization
debug_env()
```

---

## ⚡ Performance & Optimization

### Issue: Slow Queries or Timeouts

#### **Symptoms:**
- API responses take >10 seconds
- Database queries timeout
- Poor user experience

#### **Solutions:**

1. **Add Database Indexes**
```sql
-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename = 'navigation_routes';

-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_routes_user_created 
ON navigation_routes(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_routes_location 
ON navigation_routes USING GIN(coordinates);
```

2. **Optimize Queries**
```python
# Bad: Fetching all data
routes = supabase.table('navigation_routes').select('*').execute()

# Good: Selecting specific columns
routes = supabase.table('navigation_routes')\
    .select('id, start_lat, start_lon, end_lat, end_lon, created_at')\
    .eq('user_id', user_id)\
    .limit(10)\
    .execute()
```

3. **Implement Caching**
```python
# Add caching to your service
from functools import lru_cache
import time

class CachedSupabaseService:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    @lru_cache(maxsize=100)
    def get_user_routes_cached(self, user_id, cache_key):
        # Implementation with caching
        pass
```

---

## 🛠️ Debugging Tools

### 1. Supabase Dashboard Tools

#### **Logs Explorer**
```bash
# In Supabase Dashboard:
# 1. Click "Logs" in sidebar
# 2. Filter by: edge_logs, database, auth
# 3. Search for errors or specific time ranges
# 4. Export logs for analysis
```

#### **Query Performance**
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 100;

-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 2. Flutter Debugging

#### **Debug Logging**
```dart
// Add comprehensive logging
class SupabaseLogger {
  static void log(String message, {dynamic error}) {
    print('[Supabase] $message');
    if (error != null) {
      print('[Supabase] Error: $error');
    }
  }
}

// Use in your services
SupabaseLogger.log('Saving route...');
final result = await saveRoute(routeData);
SupabaseLogger.log('Route saved successfully');
```

#### **Network Inspector**
```bash
# Use Flutter DevTools
flutter pub global activate devtools
flutter pub global run devtools

# Check network tab for API calls
# Verify request/response data
```

### 3. Backend Debugging

#### **Python Logging**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Add to your service
def save_route(self, user_id, route_data):
    logger.info(f"Saving route for user {user_id}")
    try:
        result = self.supabase.table("navigation_routes").insert(route_record).execute()
        logger.info(f"Route saved successfully: {result.data[0]['id']}")
        return result.data[0]
    except Exception as e:
        logger.error(f"Failed to save route: {e}")
        return None
```

---

## 📋 Best Practices

### 1. **Environment Management**
```bash
# Use different environments
# .env.development
# .env.production
# .env.testing

# Load appropriate environment
load_dotenv('.env.' + os.getenv('ENVIRONMENT', 'development'))
```

### 2. **Error Handling**
```python
# Implement robust error handling
class SupabaseError(Exception):
    pass

def safe_database_operation(operation):
    def wrapper(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise SupabaseError(f"Database error: {e}")
    return wrapper
```

### 3. **Connection Pooling**
```python
# Use connection pooling for better performance
from supabase import create_client, ClientOptions

client = create_client(
    url=url,
    key=key,
    options=ClientOptions(
        postgrest_client_timeout=30,
        storage_client_timeout=30,
        schema='public'
    )
)
```

### 4. **Security Best Practices**
```sql
-- Always use parameterized queries
-- Never expose service role key to clients
-- Implement proper RLS policies
-- Regularly rotate API keys
-- Monitor access logs
```

### 5. **Monitoring Setup**
```python
# Add health checks
def health_check():
    try:
        result = supabase.table('user_profiles').select('count').execute()
        return {"status": "healthy", "timestamp": datetime.now()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## 🚨 Emergency Recovery

### If Everything Breaks:

1. **Backup Current Data**
```sql
-- Export all data
COPY navigation_routes TO 'routes_backup.csv' WITH CSV HEADER;
COPY user_profiles TO 'users_backup.csv' WITH CSV HEADER;
```

2. **Reset Supabase Project**
```bash
# In Supabase Dashboard:
# Settings > General > Reset project password
# Or create new project and migrate data
```

3. **Restore from Backup**
```sql
-- Restore data
COPY navigation_routes FROM 'routes_backup.csv' WITH CSV HEADER;
COPY user_profiles FROM 'users_backup.csv' WITH CSV HEADER;
```

---

## 📞 Getting Help

### **Community Resources:**
- [Supabase Discord](https://discord.supabase.com)
- [GitHub Issues](https://github.com/supabase/supabase/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/supabase)

### **Official Support:**
- [Supabase Docs](https://supabase.com/docs)
- [Support Tickets](https://supabase.com/support)
- [Status Page](https://status.supabase.com)

### **Project-Specific Help:**
- Check project logs
- Review environment configuration
- Test with minimal example
- Contact project maintainers

---

*This troubleshooting guide is part of the Clean Air Route Navigation project documentation.*
