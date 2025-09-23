#!/usr/bin/env python
"""Deployment startup script that ensures dependencies and starts the app"""

import os
import sys
import subprocess

def ensure_dependencies():
    """Ensure critical dependencies are installed"""
    required_packages = [
        'flask>=3.1.0',
        'flask-sqlalchemy>=3.1.1',
        'flask-login>=0.6.3',
        'flask-wtf>=1.2.2',
        'flask-limiter>=3.13',
        'psycopg2-binary>=2.9.10',
        'sqlalchemy>=2.0.40',
        'gunicorn>=23.0.0',
        'werkzeug>=3.1.3',
        'wtforms>=3.2.1',
        'email-validator>=2.2.0',
        'apscheduler>=3.11.0',
        'requests>=2.32.3',
        'pandas>=2.2.3',
        'numpy>=2.2.4'
    ]
    
    print("Checking and installing required dependencies...")
    for package in required_packages:
        try:
            # Try to import the package name (before version specifier)
            pkg_name = package.split('>=')[0].replace('-', '_')
            __import__(pkg_name)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package])

def start_application():
    """Start the application with gunicorn"""
    port = os.environ.get('PORT', '8080')
    
    # Ensure dependencies first
    ensure_dependencies()
    
    print(f"Starting application on port {port}...")
    
    # Try gunicorn first, fallback to direct Python execution
    try:
        # Run gunicorn
        subprocess.run([
            sys.executable, '-m', 'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '1',
            '--threads', '1',
            '--timeout', '120',
            '--keep-alive', '2',
            '--max-requests', '1000',
            'main:app'
        ])
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Gunicorn failed ({e}), falling back to direct Python execution...")
        # Fallback to running main.py directly
        os.environ['PORT'] = port
        subprocess.run([sys.executable, 'main.py'])

if __name__ == '__main__':
    start_application()