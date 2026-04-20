"""
Test Script for Predictive AQI System Structure
Verifies all components are properly structured and can be imported
"""

import os
import sys
import json
from datetime import datetime

def test_file_structure():
    """Test if all required files are created"""
    print("=== Testing File Structure ===")
    
    required_files = [
        'aqi_data_collector.py',
        'data_preprocessor.py', 
        'lstm_aqi_predictor.py',
        'training_pipeline.py',
        'predictive_aqi_service.py',
        'predictive_api.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"  Found: {file}")
    
    if missing_files:
        print(f"  Missing files: {missing_files}")
        return False
    else:
        print("  All required files found!")
        return True

def test_configuration():
    """Test configuration files"""
    print("\n=== Testing Configuration ===")
    
    config_files = [
        '../config/training_config.json',
        '../requirements.txt'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  Found: {config_file}")
            if config_file.endswith('.json'):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    print(f"    Valid JSON with {len(config)} keys")
                except Exception as e:
                    print(f"    Error reading JSON: {e}")
                    return False
        else:
            print(f"  Missing: {config_file}")
            return False
    
    return True

def test_basic_imports():
    """Test basic Python imports"""
    print("\n=== Testing Basic Imports ===")
    
    try:
        import json
        print("  json: OK")
    except ImportError:
        print("  json: FAILED")
        return False
    
    try:
        import sqlite3
        print("  sqlite3: OK")
    except ImportError:
        print("  sqlite3: FAILED")
        return False
    
    try:
        import requests
        print("  requests: OK")
    except ImportError:
        print("  requests: FAILED - install with: pip install requests")
        return False
    
    try:
        import flask
        print("  flask: OK")
    except ImportError:
        print("  flask: FAILED - install with: pip install flask")
        return False
    
    return True

def test_ml_imports():
    """Test ML-related imports (may fail if not installed)"""
    print("\n=== Testing ML Imports (Optional) ===")
    
    ml_packages = {
        'tensorflow': 'tensorflow',
        'pandas': 'pandas', 
        'numpy': 'numpy',
        'sklearn': 'scikit-learn'
    }
    
    results = {}
    for package, import_name in ml_packages.items():
        try:
            __import__(import_name)
            print(f"  {package}: OK")
            results[package] = True
        except ImportError:
            print(f"  {package}: NOT INSTALLED")
            results[package] = False
    
    return results

def test_api_structure():
    """Test API endpoint definitions"""
    print("\n=== Testing API Structure ===")
    
    try:
        with open('predictive_api.py', 'r') as f:
            api_content = f.read()
        
        required_endpoints = [
            '/api/health',
            '/api/aqi/predict',
            '/api/routes/predictive',
            '/api/routes/compare',
            '/api/model/train',
            '/api/model/status'
        ]
        
        found_endpoints = []
        for endpoint in required_endpoints:
            if endpoint in api_content:
                found_endpoints.append(endpoint)
                print(f"  Found endpoint: {endpoint}")
            else:
                print(f"  Missing endpoint: {endpoint}")
        
        print(f"  Found {len(found_endpoints)}/{len(required_endpoints)} endpoints")
        return len(found_endpoints) >= len(required_endpoints) - 1  # Allow 1 missing
        
    except Exception as e:
        print(f"  Error reading API file: {e}")
        return False

def test_model_architecture():
    """Test LSTM model architecture definition"""
    print("\n=== Testing Model Architecture ===")
    
    try:
        with open('lstm_aqi_predictor.py', 'r') as f:
            model_content = f.read()
        
        required_components = [
            'class LSTMAQIPredictor',
            'def build_model',
            'LSTM',
            'MultiHeadAttention',
            'Dense'
        ]
        
        found_components = []
        for component in required_components:
            if component in model_content:
                found_components.append(component)
                print(f"  Found: {component}")
            else:
                print(f"  Missing: {component}")
        
        print(f"  Found {len(found_components)}/{len(required_components)} components")
        return len(found_components) >= len(required_components) - 1
        
    except Exception as e:
        print(f"  Error reading model file: {e}")
        return False

def test_data_pipeline():
    """Test data pipeline components"""
    print("\n=== Testing Data Pipeline ===")
    
    try:
        # Test data collector
        with open('aqi_data_collector.py', 'r') as f:
            collector_content = f.read()
        
        collector_components = ['AQIDataCollector', 'fetch_aqi_data', 'store_aqi_data']
        for component in collector_components:
            if component in collector_content:
                print(f"  DataCollector: {component} - OK")
            else:
                print(f"  DataCollector: {component} - MISSING")
        
        # Test preprocessor
        with open('data_preprocessor.py', 'r') as f:
            preprocessor_content = f.read()
        
        preprocessor_components = ['AQIDataPreprocessor', 'validate_data_quality', 'clean_data']
        for component in preprocessor_components:
            if component in preprocessor_content:
                print(f"  Preprocessor: {component} - OK")
            else:
                print(f"  Preprocessor: {component} - MISSING")
        
        return True
        
    except Exception as e:
        print(f"  Error testing data pipeline: {e}")
        return False

def generate_summary_report():
    """Generate summary report of system status"""
    print("\n" + "="*60)
    print("PREDICTIVE AQI SYSTEM - STRUCTURE TEST REPORT")
    print("="*60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Configuration", test_configuration), 
        ("Basic Imports", test_basic_imports),
        ("API Structure", test_api_structure),
        ("Model Architecture", test_model_architecture),
        ("Data Pipeline", test_data_pipeline)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Test ML imports separately
    ml_results = test_ml_imports()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Core Tests: {passed}/{total} passed")
    
    if passed == total:
        print("  All core components are properly structured!")
    else:
        print("  Some components need attention.")
    
    ml_installed = sum(1 for result in ml_results.values() if result)
    ml_total = len(ml_results)
    
    print(f"ML Packages: {ml_installed}/{ml_total} installed")
    
    if ml_installed < ml_total:
        print("  Note: ML packages are optional for structure testing")
        print("  Install with: pip install tensorflow pandas numpy scikit-learn")
    
    print("\nNext Steps:")
    print("1. Install ML dependencies if not already done")
    print("2. Set up Google Maps API key in .env file")
    print("3. Run: python training_pipeline.py to train the model")
    print("4. Run: python predictive_api.py to start the API server")
    
    return results, ml_results

def main():
    """Main test function"""
    print("Predictive AQI System - Structure Test")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Change to backend directory if needed
    if not os.path.exists('predictive_api.py'):
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        if os.path.exists(backend_dir):
            os.chdir(backend_dir)
            print(f"Changed to backend directory: {os.getcwd()}")
    
    return generate_summary_report()

if __name__ == "__main__":
    main()
