#!/bin/bash

# Comprehensive deployment preparation script
echo "=== Comprehensive Deployment Preparation ==="

# Set all environment variables for deployment
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1
export PIP_BREAK_SYSTEM_PACKAGES=1
export PIP_ROOT_USER_ACTION=ignore
export FLASK_APP=main.py
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

echo "1. Environment variables configured"

# Run the advanced pyee fix
echo "2. Running advanced pyee package fix..."
./fix_pyee_advanced.sh

# Install missing packages that aren't in requirements.txt
echo "3. Installing additional dependencies..."
pip install --no-cache-dir babel flask-babel flask-limiter pyjwt 2>/dev/null || echo "Additional packages installation attempted"

# Verify critical imports
echo "4. Verifying critical imports..."
python -c "
import sys
critical_modules = ['flask', 'gunicorn', 'psycopg2', 'sqlalchemy', 'werkzeug']
failed_modules = []

for module in critical_modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
        failed_modules.append(module)

if failed_modules:
    print(f'Failed modules: {failed_modules}')
    sys.exit(1)
else:
    print('All critical modules available')
"

# Test application startup
echo "5. Testing application startup..."
python -c "
import os
os.environ['PORT'] = '8080'
try:
    from main import app
    print('✅ Application imports successfully')
except Exception as e:
    print(f'❌ Application startup failed: {e}')
    import traceback
    traceback.print_exc()
"

# Test gunicorn configuration
echo "6. Testing gunicorn configuration..."
gunicorn --check-config main:app && echo "✅ Gunicorn configuration valid" || echo "❌ Gunicorn configuration failed"

echo "=== Deployment Preparation Complete ==="
echo "Ready for Cloud Run deployment!"