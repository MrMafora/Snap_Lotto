
#!/bin/bash

echo "=== COMPREHENSIVE CLOUD RUN DEPLOYMENT FIX ==="

# Step 1: Clean environment completely
echo "1. Cleaning pip environment..."
pip cache purge 2>/dev/null || true
pip uninstall pyee -y 2>/dev/null || true

# Step 2: Install requirements without pyee first
echo "2. Installing requirements without pyee..."
pip install --no-cache-dir -r requirements.txt

# Step 3: Install pyee separately to avoid corruption
echo "3. Installing pyee package separately..."
pip install --force-reinstall --no-deps --no-cache-dir pyee==12.1.1

# Step 4: Verify application imports
echo "4. Testing application imports..."
python -c "
try:
    import main
    print('✅ Application imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Step 5: Test gunicorn with environment variables
echo "5. Testing gunicorn configuration..."
export PORT=8080
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1
gunicorn --check-config -c gunicorn.conf.py main:app

echo "✅ Deployment fixes completed!"
echo "Your app should now deploy successfully to Cloud Run"
