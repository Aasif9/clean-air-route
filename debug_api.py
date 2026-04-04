#!/usr/bin/env python3
"""
Debug script to test Google API integration
"""
import requests
import json
import sys
import os

# Add backend to path
sys.path.append('backend')

def test_api_key():
    """Test if the API key is loaded correctly"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("Maps_API_KEY")
    print(f"🔑 API Key loaded: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
    
    if not api_key or api_key == "YOUR_KEY_HERE":
        print("❌ API key not properly configured!")
        return False
    
    print("✅ API key configured correctly")
    return True

def test_backend():
    """Test backend API endpoints"""
    base_url = "http://localhost:5002"
    
    print("\n🧪 Testing Backend API...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.text}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test route calculation with your coordinates
    try:
        url = f"{base_url}/routes/clean?start_lat=22.5878&start_lon=88.3747&end_lat=22.5174&end_lon=88.3668"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Route calculation successful!")
            print(f"📊 Data Source: {data.get('data_source', 'unknown')}")
            print(f"🛣️  Fast Route: {data['fast_route']['analysis']['total_distance_km']:.1f}km, AQI {data['fast_route']['analysis']['average_aqi']:.1f}")
            print(f"🌱 Clean Route: {data['clean_route']['analysis']['total_distance_km']:.1f}km, AQI {data['clean_route']['analysis']['average_aqi']:.1f}")
            print(f"📈 AQI Improvement: {data['comparison']['aqi_improvement']:.1f} points")
            return True
        else:
            print(f"❌ Route calculation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Route calculation error: {e}")
        return False

def test_google_apis_directly():
    """Test Google APIs directly (for debugging)"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("Maps_API_KEY")
    
    print("\n🔍 Testing Google APIs directly...")
    
    # Test Routes API
    try:
        routes_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
            "Content-Type": "application/json"
        }
        data = {
            "origin": {"location": {"latLng": {"latitude": 22.5878, "longitude": 88.3747}}},
            "destination": {"location": {"latLng": {"latitude": 22.5174, "longitude": 88.3668}}},
            "travelMode": "DRIVE",
            "computeAlternativeRoutes": True,
            "routingPreference": "TRAFFIC_AWARE"
        }
        
        response = requests.post(routes_url, params={"key": api_key}, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            routes = response.json().get("routes", [])
            print(f"✅ Routes API working! Found {len(routes)} routes")
        else:
            print(f"❌ Routes API failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Routes API error: {e}")
    
    # Test Air Quality API
    try:
        aqi_url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
        data = {
            "location": {"latitude": 22.5878, "longitude": 88.3747},
            "universalAqi": True,
            "extraComputations": ["LOCAL_AQI"]
        }
        
        response = requests.post(aqi_url, params={"key": api_key}, json=data, timeout=10)
        
        if response.status_code == 200:
            aqi = response.json()["indexes"][0]["aqi"]
            print(f"✅ Air Quality API working! AQI: {aqi}")
        else:
            print(f"❌ Air Quality API failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Air Quality API error: {e}")

def main():
    """Main test function"""
    print("🚀 Kolkata AQI Google API Debug Tool")
    print("=" * 50)
    
    # Test 1: API Key Configuration
    if not test_api_key():
        print("\n❌ Please fix API key configuration first!")
        return
    
    # Test 2: Backend API
    if not test_backend():
        print("\n❌ Backend API issues detected!")
        print("Make sure the backend is running: cd backend && python api.py")
        return
    
    # Test 3: Direct Google APIs (optional, for debugging)
    test_google_apis_directly()
    
    print("\n🎉 Testing complete!")
    print("\n📋 Next Steps:")
    print("1. Open your browser to http://localhost:8001")
    print("2. Clear browser cache (Ctrl+Shift+R)")
    print("3. Try calculating routes again")

if __name__ == "__main__":
    main()
