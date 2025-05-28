#!/usr/bin/env python3
"""
Create admin account for lottery automation system
"""
import os
import sys
sys.path.append(os.getcwd())

from main import app, db
from models import User

def create_admin_account():
    """Create a default admin account"""
    print("Creating admin account for automation access...")
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print("✅ Admin account already exists!")
            print(f"Username: admin")
            print(f"You can log in with this account to access automation controls.")
            return True
        
        try:
            # Create new admin user
            admin_user = User(
                username='admin',
                email='admin@lottery.local',
                is_admin=True
            )
            admin_user.set_password('admin123')  # Simple password for demo
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("🎉 SUCCESS! Admin account created:")
            print(f"Username: admin")
            print(f"Password: admin123")
            print(f"Email: admin@lottery.local")
            print(f"Admin privileges: Yes")
            print()
            print("🔑 You can now log in at /login to access:")
            print("  ✓ Automation Control Center")
            print("  ✓ Progress bars for all automation steps")
            print("  ✓ Screenshot validation and AI processing")
            print("  ✓ Complete lottery data management")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR creating admin account: {str(e)}")
            return False

if __name__ == "__main__":
    print("=== ADMIN ACCOUNT CREATION ===\n")
    success = create_admin_account()
    
    if success:
        print("\n=== NEXT STEPS ===")
        print("1. Go to /login in your browser")
        print("2. Enter username: admin")
        print("3. Enter password: admin123")
        print("4. Access automation controls at /admin/automation-control")
        print("5. Test the 'Clear Old Screenshots' button with progress bars!")
    else:
        print("\n⚠️  Failed to create admin account. Check the logs above.")