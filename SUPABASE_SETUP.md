# Supabase Setup Guide for Clean Air Project

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step 1: Create Supabase Project](#step-1-create-supabase-project)
3. [Step 2: Database Schema Setup](#step-2-database-schema-setup)
4. [Step 3: Environment Configuration](#step-3-environment-configuration)
5. [Step 4: Backend Integration](#step-4-backend-integration)
6. [Step 5: Frontend Integration](#step-5-frontend-integration)
7. [Step 6: Testing the Integration](#step-6-testing-the-integration)
8. [Step 7: Deployment](#step-7-deployment)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

### Required Software:
- **Python 3.8+** (for backend)
- **Flutter 3.0+** (for mobile app)
- **Git** (for version control)
- **Node.js 16+** (for Supabase CLI - optional)

### Required Accounts:
- **Supabase Account** (free at https://supabase.com)
- **Render Account** (for backend deployment)
- **Vercel Account** (for frontend deployment)
- **Google Cloud Console** (for Maps API keys)

---

## 🚀 Step 1: Create Supabase Project

### 1.1 Sign Up for Supabase
```bash
# Go to https://supabase.com
# Click "Sign Up" 
# Use email or GitHub OAuth
```

### 1.2 Create New Project
```bash
# After login, click "New Project"
# Choose your organization (or create one)
# Fill in project details:
#   - Project Name: clean-air-navigation
#   - Database Password: [create strong password]
#   - Region: Choose closest to your users
#   - Pricing Plan: Free tier to start
```

### 1.3 Get Project Credentials
```bash
# After project creation, go to Settings > API
# Copy these credentials (you'll need them later):
#   - Project URL: https://your-project-id.supabase.co
#   - anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
#   - service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🗄️ Step 2: Database Schema Setup

### 2.1 Access SQL Editor
```bash
# In Supabase Dashboard:
# 1. Click "SQL Editor" in left sidebar
# 2. Click "New query"
# 3. Copy and paste the SQL below
```

### 2.2 Create Database Schema
```sql
-- Create users table (extends Supabase auth.users)
CREATE TABLE public.user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create routes table
CREATE TABLE public.navigation_routes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
  start_lat DECIMAL(10, 8) NOT NULL,
  start_lon DECIMAL(11, 8) NOT NULL,
  end_lat DECIMAL(10, 8) NOT NULL,
  end_lon DECIMAL(11, 8) NOT NULL,
  start_address TEXT,
  end_address TEXT,
  route_type TEXT NOT NULL, -- 'cleanest', 'fastest', 'alternative'
  total_distance_km DECIMAL(8, 2),
  total_time_min DECIMAL(8, 2),
  average_aqi DECIMAL(5, 1),
  min_aqi DECIMAL(5, 1),
  max_aqi DECIMAL(5, 1),
  exposure_score DECIMAL(10, 2),
  coordinates JSONB NOT NULL, -- Store route path as GeoJSON
  route_metadata JSONB, -- Additional route data
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- Create route analytics table
CREATE TABLE public.route_analytics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  route_id UUID REFERENCES public.navigation_routes(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
  action_type TEXT NOT NULL, -- 'calculated', 'started', 'completed', 'cancelled'
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB
);

-- Create AQI measurements table for historical data
CREATE TABLE public.aqi_measurements (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL,
  aqi_value DECIMAL(5, 1) NOT NULL,
  pm25 DECIMAL(6, 2),
  pm10 DECIMAL(6, 2),
  no2 DECIMAL(6, 2),
  o3 DECIMAL(6, 2),
  so2 DECIMAL(6, 2),
  co DECIMAL(6, 2),
  source TEXT, -- 'google_api', 'manual', 'sensor'
  measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_navigation_routes_user_id ON public.navigation_routes(user_id);
CREATE INDEX idx_navigation_routes_created_at ON public.navigation_routes(created_at DESC);
CREATE INDEX idx_navigation_routes_coordinates ON public.navigation_routes USING GIN(coordinates);
CREATE INDEX idx_aqi_measurements_location ON public.aqi_measurements USING GIST(point(longitude, latitude));
CREATE INDEX idx_aqi_measurements_measured_at ON public.aqi_measurements(measured_at DESC);
```

### 2.3 Enable Row Level Security (RLS)
```sql
-- Enable RLS on all tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.navigation_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.route_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.aqi_measurements ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies
CREATE POLICY "Users can view own profile" ON public.user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.user_profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own routes" ON public.navigation_routes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own routes" ON public.navigation_routes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own routes" ON public.navigation_routes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own routes" ON public.navigation_routes FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own analytics" ON public.route_analytics FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own analytics" ON public.route_analytics FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Everyone can view AQI data" ON public.aqi_measurements FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert AQI data" ON public.aqi_measurements FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

### 2.4 Create Storage Bucket
```sql
-- Create storage bucket for route exports
INSERT INTO storage.buckets (id, name, public) VALUES ('route-exports', 'route-exports', false);

-- Storage policies
CREATE POLICY "Users can upload own route exports" ON storage.objects FOR INSERT WITH CHECK (
  bucket_id = 'route-exports' AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can view own route exports" ON storage.objects FOR SELECT USING (
  bucket_id = 'route-exports' AND auth.uid()::text = (storage.foldername(name))[1]
);
```

### 2.5 Execute the SQL
```bash
# Click "Run" button in SQL Editor
# Verify all tables were created successfully
# Check Tables section in Database menu
```

---

## ⚙️ Step 3: Environment Configuration

### 3.1 Update Backend .env File
```bash
# Navigate to your backend directory
cd /Users/asifali/Desktop/web-projects/clean-air/backend

# Open or create .env file
nano .env
```

### 3.2 Add Supabase Configuration
```env
# Existing Google Maps API key
Maps_API_KEY=your_google_maps_api_key_here

# Supabase Configuration (replace with your actual values)
SUPABASE_URL=https://bnlcnefcjngoapdcijer.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.bnlcnefcjngoapdcijer.supabase.co:5432/postgres
```

### 3.3 Install Python Dependencies
```bash
# Install Supabase Python client
pip install supabase python-dotenv

# Update requirements.txt
echo "supabase==2.3.0" >> requirements.txt
```

---

## 🔧 Step 4: Backend Integration

### 4.1 Create Supabase Service File
```bash
# Create new file in backend directory
touch supabase_service.py
```

### 4.2 Add Supabase Service Code
```python
# File: backend/supabase_service.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

load_dotenv()

class SupabaseService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def save_route(self, user_id: str, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a navigation route to Supabase"""
        try:
            route_record = {
                "user_id": user_id,
                "start_lat": route_data["start_lat"],
                "start_lon": route_data["start_lon"],
                "end_lat": route_data["end_lat"],
                "end_lon": route_data["end_lon"],
                "start_address": route_data.get("start_address"),
                "end_address": route_data.get("end_address"),
                "route_type": route_data["route_type"],
                "total_distance_km": route_data["analysis"]["total_distance_km"],
                "total_time_min": route_data["analysis"]["total_travel_time_min"],
                "average_aqi": route_data["analysis"]["average_aqi"],
                "min_aqi": route_data["analysis"]["min_aqi"],
                "max_aqi": route_data["analysis"]["max_aqi"],
                "exposure_score": route_data["analysis"]["exposure_score"],
                "coordinates": json.dumps(route_data["coordinates"]),
                "route_metadata": json.dumps({
                    "node_count": route_data["node_count"],
                    "sample_points_count": route_data["analysis"]["sample_points_count"],
                    "calculated_at": datetime.now().isoformat()
                })
            }
            
            result = self.supabase.table("navigation_routes").insert(route_record).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"Error saving route to Supabase: {e}")
            return None
    
    def get_user_routes(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all routes for a user"""
        try:
            result = self.supabase.table("navigation_routes")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error fetching user routes: {e}")
            return []

# Global instance
supabase_service = SupabaseService()
```

### 4.3 Update Main API File
```bash
# Open your main API file
nano api.py
```

### 4.4 Add Supabase Integration to API
```python
# Add to existing imports in api.py
from supabase_service import supabase_service

# Add new endpoints after existing routes
@app.route('/routes/save', methods=['POST'])
def save_route():
    """Save a calculated route to Supabase"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')  # You'll get this from auth token
        route_data = data.get('route_data')
        
        if not user_id or not route_data:
            return jsonify({'error': 'Missing user_id or route_data'}), 400
        
        # Save to Supabase
        saved_route = supabase_service.save_route(user_id, route_data)
        
        if saved_route:
            return jsonify({'success': True, 'route_id': saved_route['id']})
        else:
            return jsonify({'error': 'Failed to save route'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/routes/history/<user_id>')
def get_route_history(user_id):
    """Get user's route history"""
    try:
        routes = supabase_service.get_user_routes(user_id)
        return jsonify({'routes': routes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 4.5 Test Backend Integration
```bash
# Start your backend server
python3 api.py

# Test the endpoint (in another terminal)
curl -X POST http://localhost:5002/routes/save \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "route_data": {"test": "data"}}'
```

---

## 📱 Step 5: Frontend Integration

### 5.1 Navigate to Flutter Project
```bash
# Go to your Flutter project directory
cd /path/to/your/flutter/project
```

### 5.2 Update pubspec.yaml
```yaml
# Add to dependencies in pubspec.yaml
dependencies:
  # ... existing dependencies
  supabase_flutter: ^1.10.4
```

### 5.3 Install Flutter Dependencies
```bash
# Get new dependencies
flutter pub get
```

### 5.4 Create Supabase Configuration
```dart
// File: lib/utils/supabase_config.dart
import 'package:supabase_flutter/supabase_flutter.dart';

class SupabaseConfig {
  static const String url = 'https://bnlcnefcjngoapdcijer.supabase.co';
  static const String anonKey = 'your_supabase_anon_key_here';
  
  static Future<void> initialize() async {
    await Supabase.initialize(
      url: url,
      anonKey: anonKey,
    );
  }
}
```

### 5.5 Update Main.dart
```dart
// File: lib/main.dart
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'utils/supabase_config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Supabase
  await SupabaseConfig.initialize();
  
  runApp(const MyApp());
}

// ... rest of your main.dart
```

### 5.6 Create Authentication Service
```dart
// File: lib/services/auth_service.dart
import 'package:supabase_flutter/supabase_flutter.dart';

class AuthService {
  final SupabaseClient _supabase = Supabase.instance.client;
  
  Future<AuthResponse> signInWithEmail(String email, String password) async {
    return await _supabase.auth.signInWithPassword(
      email: email,
      password: password,
    );
  }
  
  Future<AuthResponse> signUpWithEmail(String email, String password, String fullName) async {
    final response = await _supabase.auth.signUp(
      email: email,
      password: password,
      data: {'full_name': fullName},
    );
    
    // Create user profile
    if (response.user != null) {
      await _supabase.from('user_profiles').insert({
        'id': response.user!.id,
        'email': email,
        'full_name': fullName,
      });
    }
    
    return response;
  }
  
  Future<void> signOut() async {
    await _supabase.auth.signOut();
  }
  
  User? get currentUser => _supabase.auth.currentUser;
  
  Stream<AuthState> get authStateChanges => _supabase.auth.onAuthStateChange;
}
```

### 5.7 Create Route Service
```dart
// File: lib/services/route_service.dart
import 'package:supabase_flutter/supabase_flutter.dart';
import 'dart:convert';

class SupabaseRouteService {
  final SupabaseClient _supabase = Supabase.instance.client;
  
  Future<Map<String, dynamic>?> saveRoute({
    required String userId,
    required Map<String, dynamic> routeData,
  }) async {
    try {
      final response = await _supabase.from('navigation_routes').insert({
        'user_id': userId,
        'start_lat': routeData['start_lat'],
        'start_lon': routeData['start_lon'],
        'end_lat': routeData['end_lat'],
        'end_lon': route_data['end_lon'],
        'route_type': routeData['route_type'],
        'total_distance_km': routeData['analysis']['total_distance_km'],
        'total_time_min': routeData['analysis']['total_travel_time_min'],
        'average_aqi': routeData['analysis']['average_aqi'],
        'coordinates': jsonEncode(routeData['coordinates']),
      }).select().single();
      
      return response;
    } catch (e) {
      print('Error saving route: $e');
      return null;
    }
  }
  
  Future<List<Map<String, dynamic>>> getUserRoutes(String userId) async {
    try {
      final response = await _supabase
          .from('navigation_routes')
          .select('*')
          .eq('user_id', userId)
          .order('created_at', ascending: false)
          .limit(50);
      
      return List<Map<String, dynamic>>.from(response);
    } catch (e) {
      print('Error fetching routes: $e');
      return [];
    }
  }
}
```

---

## 🧪 Step 6: Testing the Integration

### 6.1 Test Backend Connection
```bash
# Test Supabase connection from backend
python3 -c "
from supabase_service import supabase_service
print('Testing Supabase connection...')
try:
    # Test with a simple query
    result = supabase_service.supabase.table('user_profiles').select('count').execute()
    print('✅ Supabase connection successful!')
    print(f'Data: {result.data}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### 6.2 Test Flutter Integration
```bash
# Run your Flutter app
flutter run

# Check console for Supabase initialization logs
# Test authentication flow
# Test route saving functionality
```

### 6.3 Create Test Data
```sql
-- In Supabase SQL Editor, create test data
INSERT INTO public.user_profiles (id, email, full_name) 
VALUES ('test-user-id', 'test@example.com', 'Test User');

-- Test route data
INSERT INTO public.navigation_routes (
  user_id, start_lat, start_lon, end_lat, end_lon, 
  route_type, total_distance_km, total_time_min, average_aqi,
  coordinates
) VALUES (
  'test-user-id', 22.5726, 88.3639, 22.5800, 88.3800,
  'cleanest', 5.2, 20.5, 38.5,
  '[[22.5726, 88.3639], [22.5800, 88.3800]]'
);
```

---

## 🚀 Step 7: Deployment

### 7.1 Deploy Backend to Render
```bash
# Commit your changes
git add .
git commit -m "Add Supabase integration"
git push

# Render will automatically deploy
# Check deployment logs
```

### 7.2 Update Environment Variables on Render
```bash
# In Render Dashboard:
# 1. Go to your service
# 2. Click "Environment"
# 3. Add Supabase environment variables:
#    - SUPABASE_URL
#    - SUPABASE_ANON_KEY
#    - SUPABASE_SERVICE_ROLE_KEY
```

### 7.3 Deploy Frontend to Vercel
```bash
# Deploy Flutter web app
flutter build web

# Deploy to Vercel (if using web version)
# Or deploy mobile app to app stores
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. **Supabase Connection Failed**
```bash
# Check your environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Verify URL format (should include https://)
# Check if keys are correct from Supabase dashboard
```

#### 2. **RLS Policy Errors**
```sql
-- Check if RLS is enabled correctly
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Check existing policies
SELECT * FROM pg_policies;
```

#### 3. **Flutter Build Errors**
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter run

# Check for version conflicts
flutter pub deps
```

#### 4. **Authentication Issues**
```dart
// Check user session
final user = Supabase.instance.client.auth.currentUser;
print('Current user: $user');

// Check auth state
Supabase.instance.client.auth.onAuthStateChange.listen((data) {
  print('Auth state changed: ${data.event}');
});
```

#### 5. **Database Permission Errors**
```sql
-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated, anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated, anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated, anon;
```

---

## 📚 Additional Resources

### Documentation Links:
- [Supabase Python Docs](https://supabase.com/docs/reference/python)
- [Supabase Flutter Docs](https://supabase.com/docs/reference/dart)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Realtime Subscriptions](https://supabase.com/docs/guides/realtime)

### Video Tutorials:
- [Supabase Crash Course](https://www.youtube.com/watch?v=K6J2_zAqELk)
- [Flutter Supabase Integration](https://www.youtube.com/watch?v=K6J2_zAqELk)

### Community Support:
- [Supabase Discord](https://discord.supabase.com)
- [GitHub Discussions](https://github.com/supabase/supabase/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/supabase)

---

## ✅ Success Checklist

After completing this setup, you should have:

- [ ] Supabase project created and configured
- [ ] Database schema with tables and RLS policies
- [ ] Backend integrated with Supabase Python client
- [ ] Frontend integrated with Supabase Flutter client
- [ ] Authentication system working
- [ ] Route storage and retrieval functional
- [ ] Real-time subscriptions configured
- [ ] Environment variables properly set
- [ ] Testing completed successfully
- [ ] Deployment updated with new features

---

## 🎯 Next Steps

1. **Add Real-time Features**: Implement live route updates
2. **Add File Storage**: Store route maps and exports
3. **Implement Analytics**: Track user behavior and AQI trends
4. **Add Offline Support**: Cache routes for offline access
5. **Performance Optimization**: Implement caching strategies
6. **Security Hardening**: Add additional security measures

---

*This setup guide is part of the Clean Air Route Navigation project documentation.*
