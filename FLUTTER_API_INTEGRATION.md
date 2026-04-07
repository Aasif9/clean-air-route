# 📱 Flutter API Integration Guide - Kolkata AQI Navigation

## 🌐 **Available APIs**

Your Kolkata AQI Navigation System provides these REST APIs:

### **1. Multi-Route API** ⭐ *Main API for Flutter App*
```
GET /routes/multi
```
**Purpose**: Get multiple route options with AQI analysis between two points

**Parameters**:
- `start_lat` (float, required): Starting latitude
- `start_lon` (float, required): Starting longitude  
- `end_lat` (float, required): Ending latitude
- `end_lon` (float, required): Ending longitude

**Example Request**:
```
https://kolkata-clean-air-route.onrender.com/routes/multi?start_lat=22.5878&start_lon=88.3747&end_lat=22.5174&end_lon=88.3668
```

**Response Format**:
```json
{
  "routes": [
    {
      "route_number": 1,
      "coordinates": [[22.5878, 88.3747], [22.5850, 88.3720], ...],
      "node_count": 150,
      "analysis": {
        "total_distance_km": 8.7,
        "total_travel_time_min": 32.5,
        "average_aqi": 52.9,
        "min_aqi": 48.0,
        "max_aqi": 56.0,
        "exposure_score": 26730.8,
        "sample_points_count": 9
      },
      "route_type": "route_1"
    },
    {
      "route_number": 2,
      "coordinates": [[22.5878, 88.3747], [22.5860, 88.3735], ...],
      "node_count": 120,
      "analysis": {
        "total_distance_km": 9.2,
        "total_travel_time_min": 28.3,
        "average_aqi": 65.4,
        "min_aqi": 58.0,
        "max_aqi": 72.0,
        "exposure_score": 31250.6,
        "sample_points_count": 8
      },
      "route_type": "route_2"
    }
  ],
  "total_routes": 2,
  "status": "success",
  "data_source": "google_multi_route",
  "cache_stats": {
    "cache_size": 5
  }
}
```

### **2. Health Check API**
```
GET /
```
**Purpose**: Check if the API is running
**Response**: `"Kolkata AQI Multi-Route System - Version 2.0"`

### **3. Test API**
```
GET /test
```
**Purpose**: Test the API with sample Kolkata coordinates
**Response**: Same as multi-route API with sample data

### **4. Legacy Clean Route API**
```
GET /routes/clean
```
**Purpose**: Legacy endpoint, redirects to multi-route
**Parameters**: Same as `/routes/multi`

---

## 🏗️ **Flutter Integration Process**

### **Step 1: Set Up Flutter Project**

#### **Create Project**
```bash
flutter create kolkata_aqi_navigation
cd kolkata_aqi_navigation
```

#### **Add Dependencies**
```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0          # For API calls
  google_maps_flutter: ^2.5.0  # For maps
  geolocator: ^10.1.0   # For GPS
  geocoding: ^2.1.0     # For address lookup
  provider: ^6.0.5      # For state management
  json_annotation: ^4.8.1  # For JSON parsing
```

### **Step 2: Create Data Models**

#### **Route Model** (`lib/models/route_model.dart`)
```dart
import 'package:json_annotation/json_annotation.dart';

part 'route_model.g.dart';

@JsonSerializable()
class RouteResponse {
  final List<Route> routes;
  final int total_routes;
  final String status;
  final String data_source;
  final CacheStats cache_stats;

  RouteResponse({
    required this.routes,
    required this.total_routes,
    required this.status,
    required this.data_source,
    required this.cache_stats,
  });

  factory RouteResponse.fromJson(Map<String, dynamic> json) =>
      _$RouteResponseFromJson(json);
  Map<String, dynamic> toJson() => _$RouteResponseToJson(this);
}

@JsonSerializable()
class Route {
  final int route_number;
  final List<List<double>> coordinates;
  final int node_count;
  final RouteAnalysis analysis;
  final String route_type;

  Route({
    required this.route_number,
    required this.coordinates,
    required this.node_count,
    required this.analysis,
    required this.route_type,
  });

  factory Route.fromJson(Map<String, dynamic> json) => _$RouteFromJson(json);
  Map<String, dynamic> toJson() => _$RouteToJson(this);

  // Helper methods
  String get routeLabel {
    switch (route_number) {
      case 1:
        return 'Cleanest';
      case 2:
        return 'Fastest';
      default:
        return 'Alternative ${route_number - 2}';
    }
  }

  Color get routeColor {
    switch (route_number) {
      case 1:
        return Colors.green;    // Cleanest
      case 2:
        return Colors.red;      // Fastest
      default:
        return Colors.blue;     // Alternative
    }
  }
}

@JsonSerializable()
class RouteAnalysis {
  final double total_distance_km;
  final double total_travel_time_min;
  final double average_aqi;
  final double min_aqi;
  final double max_aqi;
  final double exposure_score;
  final int sample_points_count;

  RouteAnalysis({
    required this.total_distance_km,
    required this.total_travel_time_min,
    required this.average_aqi,
    required this.min_aqi,
    required this.max_aqi,
    required this.exposure_score,
    required this.sample_points_count,
  });

  factory RouteAnalysis.fromJson(Map<String, dynamic> json) =>
      _$RouteAnalysisFromJson(json);
  Map<String, dynamic> toJson() => _$RouteAnalysisToJson(this);

  // Helper methods
  String get aqiCategory {
    if (average_aqi <= 50) return 'Good';
    if (average_aqi <= 100) return 'Moderate';
    if (average_aqi <= 150) return 'Unhealthy';
    return 'Very Unhealthy';
  }

  Color get aqiColor {
    if (average_aqi <= 50) return Colors.green;
    if (average_aqi <= 100) return Colors.yellow;
    if (average_aqi <= 150) return Colors.orange;
    return Colors.red;
  }
}

@JsonSerializable()
class CacheStats {
  final int cache_size;

  CacheStats({required this.cache_size});

  factory CacheStats.fromJson(Map<String, dynamic> json) =>
      _$CacheStatsFromJson(json);
  Map<String, dynamic> toJson() => _$CacheStatsToJson(this);
}
```

### **Step 3: Create API Service**

#### **API Service** (`lib/services/api_service.dart`)
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/route_model.dart';

class ApiService {
  static const String baseUrl = 'https://kolkata-clean-air-route.onrender.com';
  static const Duration timeout = Duration(seconds: 60);

  static Future<RouteResponse> getMultiRoutes({
    required double startLat,
    required double startLon,
    required double endLat,
    required double endLon,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/routes/multi').replace(queryParameters: {
        'start_lat': startLat.toString(),
        'start_lon': startLon.toString(),
        'end_lat': endLat.toString(),
        'end_lon': endLon.toString(),
      });

      print('API Request: $uri');

      final response = await http
          .get(uri)
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['error'] != null) {
          throw Exception(data['error']);
        }

        return RouteResponse.fromJson(data);
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.reasonPhrase}');
      }
    } catch (e) {
      print('API Error: $e');
      throw Exception('Failed to fetch routes: $e');
    }
  }

  static Future<bool> checkApiHealth() async {
    try {
      final response = await http.get(Uri.parse(baseUrl)).timeout(timeout);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  static Future<RouteResponse> getTestRoutes() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/test'))
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return RouteResponse.fromJson(data);
      } else {
        throw Exception('HTTP ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get test routes: $e');
    }
  }
}
```

### **Step 4: Create Location Service**

#### **Location Service** (`lib/services/location_service.dart`)
```dart
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

class LocationService {
  static Future<Position> getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('Location services are disabled.');
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Location permissions are denied');
      }
    }

    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permissions are permanently denied');
    }

    return await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
  }

  static Future<String> getAddressFromCoordinates(double lat, double lon) async {
    try {
      final placemarks = await placemarkFromCoordinates(lat, lon);
      final placemark = placemarks[0];
      return '${placemark.name}, ${placemark.locality}, ${placemark.administrativeArea}';
    } catch (e) {
      return 'Location: $lat, $lon';
    }
  }

  static Future<LocationCoordinates> searchLocation(String query) async {
    try {
      final locations = await locationFromAddress(query);
      if (locations.isNotEmpty) {
        final location = locations[0];
        return LocationCoordinates(
          latitude: location.latitude,
          longitude: location.longitude,
        );
      }
      throw Exception('Location not found');
    } catch (e) {
      throw Exception('Failed to search location: $e');
    }
  }
}

class LocationCoordinates {
  final double latitude;
  final double longitude;

  LocationCoordinates({required this.latitude, required this.longitude});
}
```

### **Step 5: Create Main Screen**

#### **Main Screen** (`lib/screens/home_screen.dart`)
```dart
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';
import '../models/route_model.dart';
import '../widgets/route_card.dart';
import '../widgets/map_widget.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = false;
  bool _isApiOnline = false;
  Position? _currentPosition;
  LatLng? _startLocation;
  LatLng? _endLocation;
  List<Route> _routes = [];
  int? _selectedRouteIndex;

  @override
  void initState() {
    super.initState();
    _checkApiStatus();
    _getCurrentLocation();
  }

  Future<void> _checkApiStatus() async {
    final isOnline = await ApiService.checkApiHealth();
    setState(() {
      _isApiOnline = isOnline;
    });
  }

  Future<void> _getCurrentLocation() async {
    try {
      final position = await LocationService.getCurrentLocation();
      setState(() {
        _currentPosition = position;
        _startLocation = LatLng(position.latitude, position.longitude);
      });
    } catch (e) {
      _showError('Failed to get location: $e');
    }
  }

  Future<void> _calculateRoutes() async {
    if (_startLocation == null || _endLocation == null) {
      _showError('Please select start and end locations');
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final response = await ApiService.getMultiRoutes(
        startLat: _startLocation!.latitude,
        startLon: _startLocation!.longitude,
        endLat: _endLocation!.latitude,
        endLon: _endLocation!.longitude,
      );

      setState(() {
        _routes = response.routes;
        _selectedRouteIndex = 0;
      });
    } catch (e) {
      _showError('Failed to calculate routes: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Kolkata AQI Navigation'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          Icon(
            _isApiOnline ? Icons.cloud_done : Icons.cloud_off,
            color: _isApiOnline ? Colors.white : Colors.red,
          ),
        ],
      ),
      body: Column(
        children: [
          // Map Section
          Expanded(
            flex: 2,
            child: MapWidget(
              routes: _routes,
              startLocation: _startLocation,
              endLocation: _endLocation,
              onRouteSelected: (route) {
                setState(() {
                  _selectedRouteIndex = _routes.indexOf(route);
                });
              },
            ),
          ),
          
          // Route Cards Section
          Expanded(
            flex: 1,
            child: _buildRouteCards(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _calculateRoutes,
        backgroundColor: Colors.green,
        child: _isLoading
            ? CircularProgressIndicator(color: Colors.white)
            : Icon(Icons.route),
      ),
    );
  }

  Widget _buildRouteCards() {
    if (_isLoading) {
      return Center(child: CircularProgressIndicator());
    }

    if (_routes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Select locations and tap route button',
              style: TextStyle(fontSize: 16),
            ),
            SizedBox(height: 16),
            if (!_isApiOnline)
              Text(
                'API is offline',
                style: TextStyle(color: Colors.red),
              ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: _routes.length,
      itemBuilder: (context, index) {
        return RouteCard(
          route: _routes[index],
          isSelected: _selectedRouteIndex == index,
          onTap: () {
            setState(() {
              _selectedRouteIndex = index;
            });
          },
        );
      },
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }
}
```

---

## 🎯 **Flutter App Features**

### **Core Functionality**
1. **Interactive Map** - Google Maps with route polylines
2. **Route Selection** - Click to select different routes
3. **AQI Analysis** - Detailed air quality metrics
4. **Location Services** - GPS integration
5. **Real-time API** - Live route calculation

### **UI Components**
1. **Route Cards** - Detailed route information
2. **Map Widget** - Interactive map display
3. **Loading States** - Progress indicators
4. **Error Handling** - User-friendly messages
5. **Status Indicators** - API connectivity

### **Data Display**
- Distance (km)
- Travel time (minutes)
- Average AQI with color coding
- AQI range (min-max)
- Exposure score
- Sample points count

---

## 📱 **App Screens Architecture**

### **1. Home Screen**
- Interactive map view
- Route selection cards
- Floating action button for calculation

### **2. Location Search Screen**
- Search for addresses
- Recent locations
- Favorites

### **3. Settings Screen**
- AQI sensitivity preferences
- Map preferences
- About section

---

## 🔧 **Build Process**

### **1. Generate JSON Models**
```bash
flutter packages pub run build_runner build
```

### **2. Run App**
```bash
flutter run
```

### **3. Build for Production**
```bash
# Android
flutter build apk --release

# iOS
flutter build ios --release
```

---

## 🚀 **Deployment**

### **Google Play Store**
1. Create signing key
2. Build release APK/AAB
3. Upload to Play Console
4. Complete store listing

### **App Store**
1. Configure Xcode project
2. Build iOS release
3. Upload to App Store Connect
4. Submit for review

---

## 📊 **API Usage & Costs**

### **Expected Usage**
- Route calculations: 15-30 API calls per route
- User sessions: 3-5 routes per session
- Monthly active users: 100-1000

### **Cost Estimation**
- **Google Maps API**: $20-50/month
- **Render Backend**: $0-7/month
- **Total**: $20-57/month

---

## 🎉 **Success Metrics**

### **Technical**
- API response time < 5 seconds
- 99.9% uptime
- Crash-free rate > 95%

### **User Experience**
- Route calculation success > 95%
- User rating > 4.0 stars
- Daily active users > 50

---

**Your Flutter app will be a fully functional mobile version of your Kolkata AQI Navigation System! 🌿📱**
