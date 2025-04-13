"""
Script to reset an admin user's password.
"""
import os
import sys
from werkzeug.security import generate_password_hash
from models import db, User
from main import app

def reset_password(username, new_password):
    """
    Reset the password for the specified user.
    
    Args:
        username (str): Username of the user
        new_password (str): New password to set
    """
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User with username '{username}' does not exist.")
            return None
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        print(f"Password for user '{username}' has been reset successfully!")
        return user

if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    
    # Reset the password
    reset_password(username, new_password)