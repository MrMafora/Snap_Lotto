#!/usr/bin/env python
"""
Script to update the admin user's password.
"""

import os
import sys
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User

def update_admin_password(username, new_password):
    """
    Update an admin user's password.
    
    Args:
        username (str): Admin username
        new_password (str): New password to set
    
    Returns:
        bool: True if password was updated, False otherwise
    """
    # Create and configure the app
    app = create_app()
    
    with app.app_context():
        # Find the admin user
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ No user found with username: {username}")
            return False
            
        if not user.is_admin:
            print(f"⚠️ User {username} is not an admin.")
            
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        print(f"✅ Password updated successfully for user: {username}")
        return True

if __name__ == "__main__":
    # If run directly, take the username and password from arguments
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        new_password = sys.argv[2]
    else:
        # Default to the admin user if no arguments provided
        username = "admin"
        new_password = "St0n3@g3"  # Hard-coded password for demonstration only
    
    update_admin_password(username, new_password)