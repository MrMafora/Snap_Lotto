"""
Database Migration Script to Remove html_path Field

This script removes the html_path field from the Screenshot model
in both the application code and the database schema, as part of the
effort to eliminate HTML content capture functionality.
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Create mini Flask app for database connection
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db = SQLAlchemy(app)

def migrate_database():
    """Remove html_path column from screenshot table"""
    print("Starting migration to remove html_path field from screenshots table")
    
    # Check if the column exists
    with db.engine.connect() as conn:
        result = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name='screenshot' AND column_name='html_path');"
        ))
        column_exists = result.scalar()
        
        if not column_exists:
            print("html_path column does not exist - no migration needed")
            return True
            
        print("html_path column exists - proceeding with migration")
        
        try:
            # Begin transaction
            trans = conn.begin()
            
            # Execute the ALTER TABLE statement
            conn.execute(text("ALTER TABLE screenshot DROP COLUMN html_path;"))
            
            # Commit the transaction
            trans.commit()
            print("Migration successful: html_path column removed from screenshot table")
            return True
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            return False

def update_model_file():
    """Update the model file to remove the html_path field"""
    models_file = "models.py"
    
    # Read the current content
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Check if there's any reference to html_path in the file
    if "html_path" not in content:
        print("No html_path reference found in models.py - no update needed")
        return True
        
    print("Found html_path references in models.py - updating file")
    
    # Make a backup
    with open(f"{models_file}.bak", 'w') as f:
        f.write(content)
        
    # Remove comment about html_path
    content = content.replace(
        "# Note: html_path field has been removed from the model but still exists in the database\n    # A migration is required to completely remove it from the schema\n", 
        ""
    )
    
    # Write the updated content
    with open(models_file, 'w') as f:
        f.write(content)
        
    print("models.py updated successfully")
    return True

if __name__ == "__main__":
    with app.app_context():
        print("Starting HTML content removal migration")
        
        # First update the model file
        update_model_file()
        
        # Then migrate the database
        migrate_database()
        
        print("HTML content removal migration completed")