
#!/bin/bash

echo "=== Comprehensive Cloud Run Deployment Fix ==="

# Step 1: Fix pyee package completely
echo "1. Fixing pyee package installation..."
pip uninstall pyee -y 2>/dev/null || true
pip cache purge 2>/dev/null || true
pip install --no-deps --force-reinstall pyee==12.1.1

# Step 2: Verify essential packages
echo "2. Installing essential packages..."
pip install flask gunicorn psycopg2-binary

# Step 3: Test application imports
echo "3. Testing application imports..."
python -c "
try:
    import main
    print('✅ Application imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Step 4: Test gunicorn configuration
echo "4. Testing gunicorn configuration..."
PORT=8080 gunicorn --check-config -c gunicorn.conf.py main:app

echo "✅ Deployment fixes completed!"
echo "Your app should now deploy successfully to Cloud Run"
