#!/usr/bin/env python3
# verify_integration.py - Verify LMS full stack integration

import requests
import time
import sys

def check_service(url, name, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}: {response.status_code} OK")
            return True
        else:
            print(f"❌ {name}: {response.status_code} - {response.text[:100]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Connection refused - service not running")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    print("Verifying LMS Full Stack Integration...")
    print("=" * 50)
    
    # Check backend services
    checks = [
        ("Backend Health", "http://localhost:8000/api/v1/health"),
        ("Backend Ready", "http://localhost:8000/api/v1/ready"),
        ("Frontend", "http://localhost:3000"),
    ]
    
    success_count = 0
    for name, url in checks:
        if check_service(url, name):
            success_count += 1
    
    print(f"\nIntegration Status: {success_count}/{len(checks)} services working")
    
    if success_count == len(checks):
        print("🎉 LMS Full Stack Integration SUCCESS!")
        print("The system is ready for use.")
        return True
    else:
        print("⚠️  Integration INCOMPLETE - please start missing services")
        print("Run: .\\start_lms_full.ps1 to start both backend and frontend")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)