# Kolkata AQI Routing System - Flutter Integration Guide

## 📱 **Flutter App Development Guide**

### **Overview**
This guide provides complete instructions for building a Flutter mobile app that integrates with the Kolkata AQI Routing backend API. The app will display 2 routes (Cleanest and Fastest) with full AQI analysis.

---

## 🏗️ **Flutter Project Architecture**

### **Project Structure**
```
aqi_routing_app/
├── lib/
│   ├── main.dart
│   ├── models/
│   │   ├── route_model.dart
│   │   ├── aqi_analysis.dart
│   │   └── api_response.dart
│   ├── services/
│   │   ├── api_service.dart
│   │   └── location_service.dart
│   ├── screens/
│   │   ├── home_screen.dart
│   │   ├── map_screen.dart
│   │   └── route_selection_screen.dart
│   ├── widgets/
│   │   ├── route_card.dart
│   │   ├── aqi_indicator.dart
│   │   ├── map_widget.dart
│   │   └── loading_widget.dart
│   └── utils/
│       ├── constants.dart
│       ├── colors.dart
│       └── helpers.dart
├── assets/
│   ├── images/
│   └── icons/
└── pubspec.yaml
```

---

## 🎨 **UI/UX Design Specifications**

### **Design Philosophy**
- **Clean, Minimal Interface** - Focus on route information
- **Color-Coded Routes** - Green for cleanest, Red for fastest
- **Card-Based Layout** - Easy comparison of routes
- **Interactive Map** - Visual route representation
- **AQI Indicators** - Clear air quality visualization

### **Color Scheme**
```dart
class AppColors {
  // Primary Colors
  static const Color primaryGreen = Color(0xFF2ECC71);    // Cleanest Route
  static const Color primaryRed = Color(0xFFE74C3C);      // Fastest Route
  static const Color background = Color(0xFFF8F9FA);      // Light Background
  static const Color surface = Color(0xFFFFFFFF);         // White Cards
  
  // AQI Colors
  static const Color aqiGood = Color(0xFF27AE60);         // 0-50 AQI
  static const Color aqiModerate = Color(0xFFF39C12);     // 51-100 AQI
  static const Color aqiUnhealthy = Color(0xFFE74C3C);    // 101-150 AQI
  static const Color aqiVeryUnhealthy = Color(0xFF9B59B6); // 151+ AQI
  
  // Text Colors
  static const Color textPrimary = Color(0xFF2C3E50);
  static const Color textSecondary = Color(0xFF7F8C8D);
}
```

### **Typography**
```dart
class AppTextStyles {
  static const TextStyle headline1 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    color: AppColors.textPrimary,
  );
  
  static const TextStyle headline2 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
  );
  
  static const TextStyle bodyText1 = TextStyle(
    fontSize: 16,
    color: AppColors.textPrimary,
  );
  
  static const TextStyle bodyText2 = TextStyle(
    fontSize: 14,
    color: AppColors.textSecondary,
  );
}
```

---

## 📊 **Data Models**

### **Route Model**
```dart
// lib/models/route_model.dart
class RouteModel {
  final int routeNumber;
  final List<List<double>> coordinates;
  final int nodeCount;
  final RouteAnalysis analysis;
  final String routeType;

  RouteModel({
    required this.routeNumber,
    required this.coordinates,
    required this.nodeCount,
    required this.analysis,
    required this.routeType,
  });

  factory RouteModel.fromJson(Map<String, dynamic> json) {
    return RouteModel(
      routeNumber: json['route_number'],
      coordinates: List<List<double>>.from(
        json['coordinates'].map((coord) => List<double>.from(coord))
      ),
      nodeCount: json['node_count'],
      analysis: RouteAnalysis.fromJson(json['analysis']),
      routeType: json['route_type'],
    );
  }

  String get routeLabel {
    switch (routeNumber) {
      case 1:
        return 'Cleanest';
      case 2:
        return 'Fastest';
      default:
        return 'Alternative ${routeNumber - 2}';
    }
  }

  Color get routeColor {
    switch (routeNumber) {
      case 1:
        return AppColors.primaryGreen;
      case 2:
        return AppColors.primaryRed;
      default:
        return AppColors.primaryRed;
    }
  }
}
```

### **AQI Analysis Model**
```dart
// lib/models/aqi_analysis.dart
class RouteAnalysis {
  final double totalDistanceKm;
  final double totalTravelTimeMin;
  final double averageAqi;
  final double minAqi;
  final double maxAqi;
  final double exposureScore;
  final int samplePointsCount;

  RouteAnalysis({
    required this.totalDistanceKm,
    required this.totalTravelTimeMin,
    required this.averageAqi,
    required this.minAqi,
    required this.maxAqi,
    required this.exposureScore,
    required this.samplePointsCount,
  });

  factory RouteAnalysis.fromJson(Map<String, dynamic> json) {
    return RouteAnalysis(
      totalDistanceKm: json['total_distance_km'].toDouble(),
      totalTravelTimeMin: json['total_travel_time_min'].toDouble(),
      averageAqi: json['average_aqi'].toDouble(),
      minAqi: json['min_aqi'].toDouble(),
      maxAqi: json['max_aqi'].toDouble(),
      exposureScore: json['exposure_score'].toDouble(),
      samplePointsCount: json['sample_points_count'],
    );
  }

  String get aqiCategory {
    if (averageAqi <= 50) return 'Good';
    if (averageAqi <= 100) return 'Moderate';
    if (averageAqi <= 150) return 'Unhealthy';
    return 'Very Unhealthy';
  }

  Color get aqiColor {
    if (averageAqi <= 50) return AppColors.aqiGood;
    if (averageAqi <= 100) return AppColors.aqiModerate;
    if (averageAqi <= 150) return AppColors.aqiUnhealthy;
    return AppColors.aqiVeryUnhealthy;
  }
}
```

### **API Response Model**
```dart
// lib/models/api_response.dart
class RouteApiResponse {
  final List<RouteModel> routes;
  final int totalRoutes;
  final String status;
  final String dataSource;
  final CacheStats cacheStats;

  RouteApiResponse({
    required this.routes,
    required this.totalRoutes,
    required this.status,
    required this.dataSource,
    required this.cacheStats,
  });

  factory RouteApiResponse.fromJson(Map<String, dynamic> json) {
    return RouteApiResponse(
      routes: (json['routes'] as List)
          .map((route) => RouteModel.fromJson(route))
          .toList(),
      totalRoutes: json['total_routes'],
      status: json['status'],
      dataSource: json['data_source'],
      cacheStats: CacheStats.fromJson(json['cache_stats']),
    );
  }

  List<RouteModel> get displayRoutes {
    return routes.take(2).toList(); // Only show first 2 routes
  }
}

class CacheStats {
  final int cacheSize;

  CacheStats({required this.cacheSize});

  factory CacheStats.fromJson(Map<String, dynamic> json) {
    return CacheStats(cacheSize: json['cache_size']);
  }
}
```

---

## 🔌 **API Service Integration**

### **API Service**
```dart
// lib/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/api_response.dart';
import '../utils/constants.dart';

class ApiService {
  static const String _baseUrl = 'https://your-backend-url.railway.app';
  static const Duration _timeout = Duration(seconds: 60);

  static Future<RouteApiResponse> getMultiRoutes({
    required double startLat,
    required double startLon,
    required double endLat,
    required double endLon,
  }) async {
    try {
      final uri = Uri.parse('$_baseUrl/routes/multi').replace(queryParameters: {
        'start_lat': startLat.toString(),
        'start_lon': startLon.toString(),
        'end_lat': endLat.toString(),
        'end_lon': endLon.toString(),
      });

      print('API Request: $uri');

      final response = await http
          .get(uri)
          .timeout(_timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['error'] != null) {
          throw Exception(data['error']);
        }

        return RouteApiResponse.fromJson(data);
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.reasonPhrase}');
      }
    } catch (e) {
      print('API Error: $e');
      throw Exception('Failed to fetch routes: $e');
    }
  }

  static Future<bool> checkBackendStatus() async {
    try {
      final response = await http.get(Uri.parse('$_baseUrl/')).timeout(_timeout);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
```

### **Location Service**
```dart
// lib/services/location_service.dart
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
}
```

---

## 🗺️ **Map Integration**

### **Map Widget**
```dart
// lib/widgets/map_widget.dart
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../models/route_model.dart';
import '../utils/colors.dart';

class RouteMapWidget extends StatefulWidget {
  final List<RouteModel> routes;
  final LatLng? startLocation;
  final LatLng? endLocation;
  final Function(RouteModel)? onRouteSelected;

  const RouteMapWidget({
    Key? key,
    required this.routes,
    this.startLocation,
    this.endLocation,
    this.onRouteSelected,
  }) : super(key: key);

  @override
  _RouteMapWidgetState createState() => _RouteMapWidgetState();
}

class _RouteMapWidgetState extends State<RouteMapWidget> {
  GoogleMapController? _mapController;
  final Set<Marker> _markers = {};
  final Set<Polyline> _polylines = {};
  int? _selectedRouteIndex;

  @override
  void initState() {
    super.initState();
    _initializeMap();
  }

  void _initializeMap() {
    _addMarkers();
    _addPolylines();
  }

  void _addMarkers() {
    if (widget.startLocation != null) {
      _markers.add(
        Marker(
          markerId: MarkerId('start'),
          position: widget.startLocation!,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
          infoWindow: InfoWindow(title: 'Start Point'),
        ),
      );
    }

    if (widget.endLocation != null) {
      _markers.add(
        Marker(
          markerId: MarkerId('end'),
          position: widget.endLocation!,
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          infoWindow: InfoWindow(title: 'End Point'),
        ),
      );
    }
  }

  void _addPolylines() {
    for (int i = 0; i < widget.routes.length; i++) {
      final route = widget.routes[i];
      final coordinates = route.coordinates
          .map((coord) => LatLng(coord[0], coord[1]))
          .toList();

      _polylines.add(
        Polyline(
          polylineId: PolylineId('route_$i'),
          points: coordinates,
          color: route.routeColor,
          width: _selectedRouteIndex == i ? 8 : 4,
          onTap: () {
            setState(() {
              _selectedRouteIndex = i;
            });
            widget.onRouteSelected?.call(route);
          },
        ),
      );
    }
  }

  void _fitMapToRoutes() {
    if (_mapController == null || widget.routes.isEmpty) return;

    final bounds = _calculateBounds();
    _mapController!.animateCamera(
      CameraUpdate.newLatLngBounds(bounds, 100.0),
    );
  }

  LatLngBounds _calculateBounds() {
    double minLat = widget.startLocation?.latitude ?? 0;
    double maxLat = widget.startLocation?.latitude ?? 0;
    double minLon = widget.startLocation?.longitude ?? 0;
    double maxLon = widget.startLocation?.longitude ?? 0;

    for (final route in widget.routes) {
      for (final coord in route.coordinates) {
        minLat = math.min(minLat, coord[0]);
        maxLat = math.max(maxLat, coord[0]);
        minLon = math.min(minLon, coord[1]);
        maxLon = math.max(maxLon, coord[1]);
      }
    }

    return LatLngBounds(
      southwest: LatLng(minLat, minLon),
      northeast: LatLng(maxLat, maxLon),
    );
  }

  @override
  Widget build(BuildContext context) {
    return GoogleMap(
      onMapCreated: (controller) {
        _mapController = controller;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _fitMapToRoutes();
        });
      },
      initialCameraPosition: CameraPosition(
        target: widget.startLocation ?? LatLng(22.5726, 88.3639), // Kolkata
        zoom: 12,
      ),
      markers: _markers,
      polylines: _polylines,
      myLocationEnabled: true,
      myLocationButtonEnabled: true,
      zoomControlsEnabled: true,
    );
  }
}
```

---

## 🎴 **UI Components**

### **Route Card Widget**
```dart
// lib/widgets/route_card.dart
import 'package:flutter/material.dart';
import '../models/route_model.dart';
import '../utils/colors.dart';
import '../utils/helpers.dart';

class RouteCard extends StatelessWidget {
  final RouteModel route;
  final bool isSelected;
  final VoidCallback? onTap;

  const RouteCard({
    Key? key,
    required this.route,
    this.isSelected = false,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: isSelected ? 8 : 2,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isSelected ? route.routeColor : Colors.transparent,
          width: 2,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: route.routeColor,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      route.routeLabel,
                      style: AppTextStyles.headline2.copyWith(
                        color: route.routeColor,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: route.routeColor,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '#${route.routeNumber}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              
              // Metrics Grid
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                childAspectRatio: 2.5,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                children: [
                  _buildMetric(
                    'Distance',
                    '${route.analysis.totalDistanceKm.toStringAsFixed(1)} km',
                    Icons.straighten,
                  ),
                  _buildMetric(
                    'Time',
                    '${route.analysis.totalTravelTimeMin.toStringAsFixed(0)} min',
                    Icons.access_time,
                  ),
                  _buildAQIMetric(),
                  _buildMetric(
                    'AQI Range',
                    '${route.analysis.minAqi.toStringAsFixed(0)} - ${route.analysis.maxAqi.toStringAsFixed(0)}',
                    Icons.air,
                  ),
                ],
              ),
              
              const SizedBox(height: 12),
              
              // Exposure Score
              Row(
                children: [
                  Icon(Icons.trending_up, size: 16, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    'Exposure Score: ${route.analysis.exposureScore.toStringAsFixed(0)}',
                    style: AppTextStyles.bodyText2,
                  ),
                  const Spacer(),
                  Text(
                    '${route.analysis.samplePointsCount} samples',
                    style: AppTextStyles.bodyText2,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetric(String label, String value, IconData icon) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 16, color: AppColors.textSecondary),
            const SizedBox(width: 4),
            Text(
              label,
              style: AppTextStyles.bodyText2,
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: AppTextStyles.bodyText1.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  Widget _buildAQIMetric() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.air, size: 16, color: AppColors.textSecondary),
            const SizedBox(width: 4),
            Text(
              'Avg AQI',
              style: AppTextStyles.bodyText2,
            ),
          ],
        ),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color: route.analysis.aqiColor.withOpacity(0.2),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: route.analysis.aqiColor),
          ),
          child: Text(
            route.analysis.averageAqi.toStringAsFixed(1),
            style: AppTextStyles.bodyText1.copyWith(
              fontWeight: FontWeight.bold,
              color: route.analysis.aqiColor,
            ),
          ),
        ),
      ],
    );
  }
}
```

---

## 📱 **Main Screens**

### **Home Screen**
```dart
// lib/screens/home_screen.dart
class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = false;
  bool _isBackendOnline = false;
  Position? _currentPosition;
  LatLng? _startLocation;
  LatLng? _endLocation;
  List<RouteModel> _routes = [];
  int? _selectedRouteIndex;

  @override
  void initState() {
    super.initState();
    _checkBackendStatus();
    _getCurrentLocation();
  }

  Future<void> _checkBackendStatus() async {
    final isOnline = await ApiService.checkBackendStatus();
    setState(() {
      _isBackendOnline = isOnline;
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
        _routes = response.displayRoutes;
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
        title: const Text('AQI Route Navigator'),
        backgroundColor: AppColors.primaryGreen,
        foregroundColor: Colors.white,
        actions: [
          Icon(
            _isBackendOnline ? Icons.cloud_done : Icons.cloud_off,
            color: _isBackendOnline ? Colors.white : Colors.red,
          ),
        ],
      ),
      body: Column(
        children: [
          // Map Section
          Expanded(
            flex: 2,
            child: RouteMapWidget(
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
        backgroundColor: AppColors.primaryGreen,
        child: _isLoading
            ? const CircularProgressIndicator(color: Colors.white)
            : const Icon(Icons.route),
      ),
    );
  }

  Widget _buildRouteCards() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_routes.isEmpty) {
      return const Center(
        child: Text(
          'Select locations and tap route button',
          style: AppTextStyles.bodyText2,
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
        backgroundColor: AppColors.primaryRed,
      ),
    );
  }
}
```

---

## 📦 **Dependencies**

### **pubspec.yaml**
```yaml
name: aqi_routing_app
description: AQI-based route navigation app

version: 1.0.0+1

environment:
  sdk: ">=2.17.0 <3.0.0"

dependencies:
  flutter:
    sdk: flutter
  
  # UI & Navigation
  cupertino_icons: ^1.0.2
  
  # Maps & Location
  google_maps_flutter: ^2.2.5
  geolocator: ^9.0.2
  geocoding: ^2.1.0
  
  # HTTP & API
  http: ^0.13.5
  
  # State Management
  provider: ^6.0.5
  
  # Utilities
  intl: ^0.17.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
  
  assets:
    - assets/images/
    - assets/icons/
```

---

## 🔧 **Configuration**

### **Android Configuration**
```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

<application>
    <meta-data android:name="com.google.android.geo.API_KEY"
               android:value="YOUR_GOOGLE_MAPS_API_KEY"/>
</application>
```

### **iOS Configuration**
```xml
<!-- ios/Runner/Info.plist -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>This app needs location access to calculate routes</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>This app needs location access to calculate routes</string>
```

---

## 🚀 **Step-by-Step Implementation**

### **Step 1: Project Setup**
```bash
flutter create aqi_routing_app
cd aqi_routing_app
```

### **Step 2: Add Dependencies**
```bash
flutter pub add google_maps_flutter geolocator geocoding http provider intl
```

### **Step 3: Create Folder Structure**
```bash
mkdir -p lib/{models,services,screens,widgets,utils}
mkdir -p assets/{images,icons}
```

### **Step 4: Implement Models**
- Create `route_model.dart`
- Create `aqi_analysis.dart`
- Create `api_response.dart`

### **Step 5: Implement Services**
- Create `api_service.dart`
- Create `location_service.dart`

### **Step 6: Create Widgets**
- Create `route_card.dart`
- Create `map_widget.dart`
- Create `aqi_indicator.dart`

### **Step 7: Build Screens**
- Create `home_screen.dart`
- Create `map_screen.dart`
- Create `route_selection_screen.dart`

### **Step 8: Configure Maps**
- Add Google Maps API key
- Configure Android/iOS permissions
- Test map functionality

### **Step 9: Integration**
- Connect API service
- Test route calculation
- Implement error handling

### **Step 10: Testing & Deployment**
- Test on multiple devices
- Optimize performance
- Prepare for app store release

---

## 🎯 **Key Features Summary**

### **Core Functionality**
1. **Dual Route Display** - Shows Cleanest and Fastest routes
2. **Interactive Map** - Google Maps integration with route polylines
3. **AQI Analysis** - Detailed air quality metrics for each route
4. **Location Services** - GPS integration for current location
5. **Route Selection** - Tap to select and highlight routes

### **UI Components**
1. **Route Cards** - Color-coded metric display
2. **AQI Indicators** - Visual air quality representation
3. **Map Widget** - Interactive route visualization
4. **Loading States** - Smooth loading animations
5. **Error Handling** - User-friendly error messages

### **Technical Features**
1. **API Integration** - RESTful API communication
2. **State Management** - Provider pattern for state
3. **Caching** - Local data persistence
4. **Offline Support** - Basic offline functionality
5. **Performance** - Optimized rendering and data handling

---

## 📊 **Backend API Endpoints**

### **Multi-Route Endpoint**
```
GET /routes/multi
Parameters:
- start_lat: Double (required)
- start_lon: Double (required)
- end_lat: Double (required)
- end_lon: Double (required)

Response:
{
  "routes": [
    {
      "route_number": 1,
      "coordinates": [[lat, lon], ...],
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
    }
  ],
  "total_routes": 2,
  "status": "success",
  "data_source": "google_multi_route"
}
```

---

## 🔍 **Testing Strategy**

### **Unit Tests**
- Model serialization/deserialization
- API service methods
- Location service functions
- Utility functions

### **Integration Tests**
- API endpoint integration
- Map widget functionality
- Route calculation flow
- Error handling scenarios

### **UI Tests**
- Screen navigation
- User interactions
- Route selection
- Data display

---

## 📈 **Performance Optimization**

### **API Optimization**
- Request caching
- Timeout handling
- Retry mechanisms
- Data compression

### **Map Performance**
- Polyline optimization
- Marker clustering
- Tile caching
- Lazy loading

### **Memory Management**
- Image optimization
- Data cleanup
- State disposal
- Resource management

---

This comprehensive guide provides everything needed to build a production-ready Flutter app that integrates with your Kolkata AQI Routing backend. The app will display 2 routes (Cleanest and Fastest) with full AQI analysis, interactive maps, and a polished user interface.
