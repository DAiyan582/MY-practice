import json
import os
from pathlib import Path

# ===== CONFIGURATION =====
# Get the directory where this script is located
BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / 'data' / 'db.json'

# ===== DATABASE FUNCTIONS =====

def load_db():
    """
    Load database from JSON file
    
    Returns:
        dict: The database contents
    
    Raises:
        FileNotFoundError: If database file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(DB_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_db(data):
    """
    Save database to JSON file
    
    Args:
        data: Dictionary to save to JSON file
    """
    # Create directory if it doesn't exist
    os.makedirs(DB_FILE.parent, exist_ok=True)
    
    with open(DB_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)

# ===== VERSION WITH ERROR HANDLING =====

def load_db_safe():
    """
    Load database safely with error handling
    
    Returns:
        dict: Database contents, or empty dict if file doesn't exist
    """
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        # Create empty database if file doesn't exist
        empty_db = {"students": [], "enrollments": []}  # Default structure
        save_db(empty_db)
        return empty_db
    except json.JSONDecodeError:
        # Handle corrupted JSON
        print(f"Error: {DB_FILE} contains invalid JSON")
        return {}

# ===== VERSION WITH RESOURCE-SPECIFIC HELPERS =====

class Database:
    """
    Database helper class for managing JSON data
    """
    
    def __init__(self, db_file=None):
        """
        Initialize database
        
        Args:
            db_file: Path to database file (optional)
        """
        if db_file:
            self.db_file = Path(db_file)
        else:
            self.db_file = Path(__file__).parent / 'data' / 'db.json'
    
    def load(self):
        """Load database from file"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
    
    def save(self, data):
        """Save database to file"""
        os.makedirs(self.db_file.parent, exist_ok=True)
        with open(self.db_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)
    
    def get_resource(self, resource_name):
        """
        Get a specific resource from database
        
        Args:
            resource_name: Name of the resource (e.g., 'students')
        
        Returns:
            list: The resource data, or empty list if not found
        """
        db = self.load()
        return db.get(resource_name, [])
    
    def save_resource(self, resource_name, data):
        """
        Save a specific resource to database
        
        Args:
            resource_name: Name of the resource
            data: Data to save for this resource
        """
        db = self.load()
        db[resource_name] = data
        self.save(db)
    
    def add_item(self, resource_name, item):
        """
        Add an item to a resource
        
        Args:
            resource_name: Name of the resource
            item: Item to add
        
        Returns:
            dict: The added item with generated ID
        """
        db = self.load()
        resource = db.get(resource_name, [])
        
        # Auto-generate ID
        if resource:
            new_id = max(r.get('id', 0) for r in resource) + 1
        else:
            new_id = 1
        
        item['id'] = new_id
        resource.append(item)
        db[resource_name] = resource
        self.save(db)
        
        return item
    
    def get_item(self, resource_name, item_id):
        """
        Get an item from a resource by ID
        
        Args:
            resource_name: Name of the resource
            item_id: ID of the item
        
        Returns:
            dict: The item, or None if not found
        """
        resource = self.get_resource(resource_name)
        return next((item for item in resource if item.get('id') == item_id), None)
    
    def update_item(self, resource_name, item_id, updates):
        """
        Update an item in a resource
        
        Args:
            resource_name: Name of the resource
            item_id: ID of the item to update
            updates: Dictionary of fields to update
        
        Returns:
            dict: The updated item, or None if not found
        """
        db = self.load()
        resource = db.get(resource_name, [])
        
        for idx, item in enumerate(resource):
            if item.get('id') == item_id:
                # Update item, preserving id
                resource[idx] = {**item, **updates, 'id': item_id}
                db[resource_name] = resource
                self.save(db)
                return resource[idx]
        
        return None
    
    def delete_item(self, resource_name, item_id):
        """
        Delete an item from a resource
        
        Args:
            resource_name: Name of the resource
            item_id: ID of the item to delete
        
        Returns:
            dict: The deleted item, or None if not found
        """
        db = self.load()
        resource = db.get(resource_name, [])
        
        for idx, item in enumerate(resource):
            if item.get('id') == item_id:
                deleted = resource.pop(idx)
                db[resource_name] = resource
                self.save(db)
                return deleted
        
        return None