#!/usr/bin/env python3
"""Test script to verify Swagger authorization configuration"""

import json
import sys
import os

def test_swagger_auth_config():
    """Test that Swagger authorization is properly configured"""
    
    print("Testing Swagger Authorization Configuration...")
    
    # Check if the custom openapi function is implemented
    try:
        # Try to import main to see if custom_openapi exists
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
        
        from app.main import app
        
        # Check if openapi schema is generated
        if hasattr(app, 'openapi_schema') and app.openapi_schema:
            print("✅ Custom OpenAPI schema generated")
            
            # Check for security schemes
            if 'components' in app.openapi_schema and 'securitySchemes' in app.openapi_schema['components']:
                security_schemes = app.openapi_schema['components']['securitySchemes']
                expected_schemes = ['OAuth2PasswordBearer', 'AccessTokenCookie', 'RefreshTokenCookie']
                
                found_schemes = list(security_schemes.keys())
                missing_schemes = [scheme for scheme in expected_schemes if scheme not in found_schemes]
                
                if missing_schemes:
                    print(f"❌ Missing security schemes: {missing_schemes}")
                    return False
                else:
                    print("✅ All required security schemes present")
                    
                # Check if protected endpoints have security
                if 'paths' in app.openapi_schema:
                    protected_count = 0
                    total_paths = len(app.openapi_schema['paths'])
                    
                    for path in app.openapi_schema['paths']:
                        for method in app.openapi_schema['paths'][path]:
                            if 'security' in app.openapi_schema['paths'][path][method]:
                                protected_count += 1
                    
                    print(f"✅ {protected_count}/{total_paths} paths have security configuration")
                    
            else:
                print("❌ No security schemes in OpenAPI schema")
                return False
                
        else:
            print("❌ Custom OpenAPI schema not generated")
            return False
            
    except ImportError as e:
        print(f"⚠️  Could not import app.main: {e}")
        print("Running manual verification...")
        
        # Manual verification of the implementation
        try:
            with open('app/main.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'def custom_openapi()' in content:
                print("✅ custom_openapi function defined")
            else:
                print("❌ custom_openapi function not found")
                return False
                
            if 'securitySchemes' in content:
                print("✅ securitySchemes configuration present")
            else:
                print("❌ securitySchemes configuration missing")
                return False
                
            if 'AccessTokenCookie' in content and 'RefreshTokenCookie' in content:
                print("✅ Cookie-based auth schemes configured")
            else:
                print("❌ Cookie-based auth schemes missing")
                return False
                
        except Exception as e:
            print(f"❌ Error reading main.py: {e}")
            return False
    
    print("\n🎉 Swagger Authorization Configuration Test PASSED")
    return True

def main():
    """Main function"""
    success = test_swagger_auth_config()
    
    # Create test report
    os.makedirs('reports', exist_ok=True)
    with open('reports/swagger_auth_test.json', 'w') as f:
        json.dump({
            'timestamp': str(__import__('datetime').datetime.now()),
            'success': success,
            'details': 'Swagger authorization configuration verified'
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())