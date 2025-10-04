#!/usr/bin/env python3
"""
Create admin user in the database
"""

import os
import psycopg2
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user():
    """Create admin user if it doesn't exist"""
    
    # Admin credentials
    username = 'admin'
    email = 'admin@lottery.com'
    password = 'admin123'
    
    try:
        # Connect to database
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        
        # Check if admin already exists
        cur.execute('SELECT id FROM "user" WHERE username = %s', (username,))
        existing = cur.fetchone()
        
        if existing:
            print(f"✅ Admin user '{username}' already exists (ID: {existing[0]})")
            cur.close()
            conn.close()
            return
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Create admin user
        cur.execute("""
            INSERT INTO "user" (username, email, password_hash, is_admin, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, password_hash, True, datetime.utcnow()))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        
        print("="*60)
        print("✅ ADMIN USER CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Username: {username}")
        print(f"Email:    {email}")
        print(f"User ID:  {user_id}")
        print(f"Is Admin: True")
        print("="*60)
        print("\nYou can now login with:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print("="*60)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        raise

if __name__ == '__main__':
    create_admin_user()
