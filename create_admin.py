"""
Script to create an initial admin user for the application.
"""
import os
import sys
from werkzeug.security import generate_password_hash
from models import db, User
from main import app

def create_admin_user(username, email, password):
    """
    Create an admin user with the specified credentials.
    
    Args:
        username (str): Admin username
        email (str): Admin email
        password (str): Admin password
    
    Returns:
        User: The created user object
    """
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists.")
            return None
        
        # Create new admin user
        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully!")
        return admin

if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    # Create the admin user
    create_admin_user(username, email, password)