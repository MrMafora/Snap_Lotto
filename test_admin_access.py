#!/usr/bin/env python3
"""
Test admin access functionality
"""
import requests
import sys

def test_admin_access():
    """Test admin login and dashboard access"""
    base_url = "http://localhost:5000"
    
    # Create a session
    session = requests.Session()
    
    # Get login page to extract any CSRF tokens
    print("Getting login page...")
    login_page = session.get(f"{base_url}/login")
    if login_page.status_code != 200:
        print(f"Failed to get login page: {login_page.status_code}")
        return False
    
    # Attempt login with admin credentials
    print("Attempting admin login...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("Login successful (redirect received)")
        
        # Try to access admin page
        print("Accessing admin dashboard...")
        admin_response = session.get(f"{base_url}/admin")
        print(f"Admin page status: {admin_response.status_code}")
        
        if admin_response.status_code == 200:
            print("✓ Admin dashboard accessible")
            return True
        else:
            print(f"✗ Admin dashboard error: {admin_response.status_code}")
            print("Response content:")
            print(admin_response.text[:500])
            return False
    else:
        print(f"Login failed: {login_response.status_code}")
        print("Response content:")
        print(login_response.text[:500])
        return False

if __name__ == "__main__":
    success = test_admin_access()
    sys.exit(0 if success else 1)