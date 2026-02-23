#!/usr/bin/env python3
# health_check.py - Verify LMS backend is running

import requests
import time

def check_backend():
    print("Checking LMS Backend Health...")
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
        if response.status_code == 200:
            print(f"✅ Health check: {response.status_code} OK")
            return True
        else:
            print(f"❌ Health check: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - backend not running")
        print("Please start the backend first with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def check_ready():
    print("\nChecking Ready endpoint...")
    try:
        response = requests.get('http://localhost:8000/api/v1/ready', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ready check: {data.get('status', 'unknown')} - DB: {data.get('database', 'unknown')}, Redis: {data.get('redis', 'unknown')}")
            return True
        else:
            print(f"❌ Ready check: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ready check error: {e}")
        return False

if __name__ == "__main__":
    print("LMS Backend Health Check")
    print("=" * 50)
    
    success = check_backend()
    if success:
        check_ready()
    
    print("\nInstructions:")
    print("1. If backend is not running, start it with:")
    print("   cd K:\\business\\projects\\lms_backend")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("2. Then start frontend in separate window:")
    print("   cd K:\\business\\projects\\lms_backend\\frontend\\educonnect-pro")
    print("   npm install")
    print("   npm run dev")