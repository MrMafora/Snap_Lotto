import requests
import sys

def test_server_connection():
    """Test if the server is reachable and responding to requests."""
    try:
        response = requests.get('http://localhost:5000/')
        if response.status_code == 200:
            print('✓ Server is running and accessible locally')
            
            # Test login functionality
            login_response = requests.post(
                'http://localhost:5000/login',
                data={'username': 'admin', 'password': 'St0n3@g3'},
                allow_redirects=False
            )
            
            if login_response.status_code == 302:  # Redirect status code
                print('✓ Login functionality appears to be working')
                
                # Get session cookie
                cookies = login_response.cookies
                
                # Test accessing admin page with session
                admin_response = requests.get(
                    'http://localhost:5000/admin',
                    cookies=cookies
                )
                
                if admin_response.status_code == 200:
                    print('✓ Admin page is accessible after login')
                    
                    # Test lottery analysis page
                    analysis_response = requests.get(
                        'http://localhost:5000/admin/lottery-analysis',
                        cookies=cookies
                    )
                    
                    if analysis_response.status_code == 200:
                        print('✓ Lottery analysis page is accessible')
                        
                        # Print content length to verify we got a real page
                        print(f'  Content length: {len(analysis_response.text)} bytes')
                        
                        # Check for tab content
                        if 'frequency-tab' in analysis_response.text:
                            print('✓ Frequency tab found in the page')
                        if 'patterns-tab' in analysis_response.text:
                            print('✓ Patterns tab found in the page')
                        if 'timeseries-tab' in analysis_response.text:
                            print('✓ Time Series tab found in the page')
                            
                    else:
                        print(f'✗ Could not access lottery analysis page: {analysis_response.status_code}')
                else:
                    print(f'✗ Could not access admin page: {admin_response.status_code}')
            else:
                print(f'✗ Login failed: {login_response.status_code}')
        else:
            print(f'✗ Server returned unexpected status code: {response.status_code}')
    except Exception as e:
        print(f'✗ Error connecting to server: {e}')
        return False
    
    return True

if __name__ == '__main__':
    success = test_server_connection()
    sys.exit(0 if success else 1)