#!/usr/bin/env python3
"""
Port Status Checker Utility

This script checks the status of ports 5000 and 8080 and provides diagnostic information.
It helps diagnose port conflicts and connectivity issues.
"""
import argparse
import socket
import subprocess
import sys
import os
import requests
import json
import time
from urllib.parse import urlparse

def check_port_in_use(port):
    """Check if a port is already in use by attempting to bind to it"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False  # Port is available
        except OSError:
            return True  # Port is in use

def get_process_using_port(port):
    """Get information about the process using a specific port"""
    try:
        # Use 'netstat' with grep which is more commonly available
        output = subprocess.check_output(['netstat', '-tuln'], 
                                         stderr=subprocess.STDOUT,
                                         universal_newlines=True)
        # Filter for the specific port
        port_info = []
        for line in output.strip().split('\n'):
            if f':{port}' in line:
                port_info.append(line)
        
        if port_info:
            return '\n'.join(port_info)
        else:
            # Try a more direct method using /proc/net/tcp
            try:
                with open('/proc/net/tcp', 'r') as f:
                    tcp_data = f.read()
                
                port_hex = format(port, '04X')
                for line in tcp_data.strip().split('\n'):
                    if f':{port_hex.lower()}' in line.lower():
                        return f"TCP connection on port {port} found in /proc/net/tcp"
            except Exception as e:
                pass
            
            return f"No detailed process information available for port {port}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Try using ss command which is available on many Linux systems
            output = subprocess.check_output(['ss', '-tuln'], 
                                            stderr=subprocess.STDOUT,
                                            universal_newlines=True)
            # Filter for the specific port
            port_info = []
            for line in output.strip().split('\n'):
                if f':{port}' in line:
                    port_info.append(line)
            
            if port_info:
                return '\n'.join(port_info)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If everything fails, just check if the port is in use
            if check_port_in_use(port):
                return f"Port {port} is in use, but no detailed information is available"
            else:
                return None

def check_remote_port(host, port, path='/health_check'):
    """Try to connect to a remote port and get response"""
    url = f"http://{host}:{port}{path}"
    try:
        start_time = time.time()
        response = requests.get(url, timeout=2)
        end_time = time.time()
        return {
            'status_code': response.status_code,
            'response_time': round((end_time - start_time) * 1000, 2),  # in ms
            'content': response.text[:100] if len(response.text) > 100 else response.text
        }
    except requests.RequestException as e:
        return {'error': str(e)}

def check_replit_domain():
    """Check if we can access the application via Replit's domain"""
    # Try to determine Replit domain from environment
    repl_slug = os.environ.get('REPL_SLUG', None)
    repl_owner = os.environ.get('REPL_OWNER', None)
    
    if repl_slug and repl_owner:
        domain = f"https://{repl_slug}.{repl_owner}.repl.co"
        try:
            start_time = time.time()
            response = requests.get(domain, timeout=5)
            end_time = time.time()
            return {
                'domain': domain,
                'status_code': response.status_code,
                'response_time': round((end_time - start_time) * 1000, 2),  # in ms
            }
        except requests.RequestException as e:
            return {'domain': domain, 'error': str(e)}
    
    return {'error': 'Could not determine Replit domain'}

def check_all_ports():
    """Check all important ports and return results"""
    results = {
        'ports': {},
        'processes': {},
        'connectivity': {}
    }
    
    # Check physical port status
    for port in [5000, 8080]:
        in_use = check_port_in_use(port)
        results['ports'][port] = {
            'in_use': in_use
        }
        
        if in_use:
            process_info = get_process_using_port(port)
            results['processes'][port] = process_info
    
    # Check connectivity
    for port in [5000, 8080]:
        results['connectivity'][port] = check_remote_port('localhost', port)
    
    # Check Replit domain
    results['replit_domain'] = check_replit_domain()
    
    return results

def main():
    """Main function to run the port status checker"""
    parser = argparse.ArgumentParser(description='Check port status for the application')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix port conflicts')
    args = parser.parse_args()
    
    # Get port status
    results = check_all_ports()
    
    if args.json:
        # Print JSON output
        print(json.dumps(results, indent=2))
    else:
        # Print human-readable output
        print("="*60)
        print("PORT STATUS CHECKER REPORT")
        print("="*60)
        
        # Port status
        print("\nPORT STATUS:")
        for port, status in results['ports'].items():
            in_use = "IN USE" if status['in_use'] else "AVAILABLE"
            print(f"  Port {port}: {in_use}")
        
        # Process information
        print("\nPROCESSES USING PORTS:")
        for port, process_info in results['processes'].items():
            if process_info:
                print(f"  Port {port}:")
                lines = process_info.strip().split('\n')
                for line in lines:
                    print(f"    {line}")
            else:
                print(f"  Port {port}: No process information available")
        
        # Connectivity
        print("\nCONNECTIVITY TESTS:")
        for port, conn_info in results['connectivity'].items():
            print(f"  Port {port}:")
            if 'error' in conn_info:
                print(f"    Error: {conn_info['error']}")
            else:
                print(f"    Status: {conn_info['status_code']}")
                print(f"    Response Time: {conn_info['response_time']}ms")
                print(f"    Content: {conn_info['content']}")
        
        # Replit domain
        print("\nREPLIT DOMAIN ACCESS:")
        domain_info = results['replit_domain']
        if 'error' in domain_info:
            if 'domain' in domain_info:
                print(f"  Domain: {domain_info['domain']}")
                print(f"  Error: {domain_info['error']}")
            else:
                print(f"  Error: {domain_info['error']}")
        else:
            print(f"  Domain: {domain_info['domain']}")
            print(f"  Status: {domain_info['status_code']}")
            print(f"  Response Time: {domain_info['response_time']}ms")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        port_5000_ok = results['ports'][5000]['in_use'] and 'status_code' in results['connectivity'][5000]
        port_8080_ok = results['ports'][8080]['in_use'] and 'status_code' in results['connectivity'][8080]
        
        if port_5000_ok and port_8080_ok:
            print("  ✓ Both development port (5000) and production port (8080) are working correctly")
            print("  ✓ Your application is ready for both development and deployment")
        elif port_5000_ok and not port_8080_ok:
            print("  ✓ Development port (5000) is working")
            print("  ✗ Production port (8080) is not working")
            print("  ! For Replit deployment, port 8080 must be functioning")
            print("  ! Try running the port bridge: python bridge.py")
        elif not port_5000_ok and port_8080_ok:
            print("  ✗ Development port (5000) is not working")
            print("  ✓ Production port (8080) is working")
            print("  ! For local development, port 5000 should be primary")
            print("  ! Consider restarting the application using ./start_app.sh")
        else:
            print("  ✗ Neither development nor production ports are working")
            print("  ! Start the application with ./start_app.sh or manually restart the services")
        
        print("="*60)
    
    # Attempt to fix port conflicts if requested
    if args.fix:
        if results['ports'][5000]['in_use'] and 'error' in results['connectivity'][5000]:
            print("\nAttempting to fix port 5000...")
            subprocess.run(['./clear_ports.sh'], check=False)
            print("Port clean-up complete. Please restart your application.")
        
        if results['ports'][8080]['in_use'] and 'error' in results['connectivity'][8080]:
            print("\nAttempting to fix port 8080...")
            subprocess.run(['./clear_ports.sh'], check=False)
            print("Port clean-up complete. Please restart your application.")

if __name__ == "__main__":
    main()