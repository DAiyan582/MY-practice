from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import os

# ===== CONFIGURATION =====
DATABASE_FILE = "database.json"
RESOURCE = "enrollments"  # Change this for different resources
REQUIRED_FIELDS = ['studentName', 'courseCode']  # Change per resource

# ===== DATABASE FUNCTIONS =====
def load_database():
    """Load database from JSON file"""
    try:
        with open(DATABASE_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        # Create default database if not exists
        default_db = {RESOURCE: []}
        save_database(default_db)
        return default_db

def save_database(data):
    """Save database to JSON file"""
    with open(DATABASE_FILE, "w") as file:
        json.dump(data, file, indent=4)

# ===== HELPER FUNCTION =====
def send_json(handler, status, success, data_or_msg):
    """
    Send JSON response matching the Express pattern
    
    Args:
        handler: The BaseHTTPRequestHandler instance
        status: HTTP status code
        success: Boolean (True/False)
        data_or_msg: If success=True, this is the data; if False, this is the error message
    """
    if success:
        response = {"success": True, "data": data_or_msg}
    else:
        response = {"success": False, "msg": data_or_msg}
    
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(response).encode())

# ===== MAIN HANDLER CLASS =====
class EnrollmentAPI(BaseHTTPRequestHandler):
    
    def read_json_body(self):
        """Read and parse JSON from request body"""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}
    
    # ========== RETRIEVE ALL (with filters) ==========
    # GET /api/enrollments
    # GET /api/enrollments?courseCode=CSE4165&status=enrolled
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)
        
        # Remove leading/trailing slashes and split
        path_parts = path.strip('/').split('/')
        
        # GET /api/enrollments
        if len(path_parts) == 2 and path_parts[0] == 'api' and path_parts[1] == RESOURCE:
            db = load_database()
            result = db.get(RESOURCE, []).copy()
            
            # Generic filter: any query param matches a field with the same name
            for key, values in query_params.items():
                if values:  # Check if there's a value
                    value = values[0]  # Take first value
                    result = [item for item in result if str(item.get(key)) == str(value)]
            
            send_json(self, 200, True, result)
            return
        
        # GET /api/enrollments/:id
        if len(path_parts) == 3 and path_parts[0] == 'api' and path_parts[1] == RESOURCE:
            try:
                item_id = int(path_parts[2])
                db = load_database()
                items = db.get(RESOURCE, [])
                
                # Find item by id
                item = next((i for i in items if i.get('id') == item_id), None)
                if not item:
                    send_json(self, 404, False, 'Not found')
                    return
                
                send_json(self, 200, True, item)
            except ValueError:
                send_json(self, 400, False, 'Invalid ID format')
            return
        
        # Endpoint not found
        send_json(self, 404, False, 'Endpoint not found')
    
    # ========== CREATE ==========
    # POST /api/enrollments
    # body: { studentName, courseCode, semester, status }
    def do_POST(self):
        path_parts = self.path.strip('/').split('/')
        
        # POST /api/enrollments
        if len(path_parts) == 2 and path_parts[0] == 'api' and path_parts[1] == RESOURCE:
            body = self.read_json_body()
            
            # Check for missing required fields
            missing = [field for field in REQUIRED_FIELDS if field not in body]
            if missing:
                send_json(self, 400, False, f"Missing fields: {', '.join(missing)}")
                return
            
            db = load_database()
            items = db.get(RESOURCE, [])
            
            # Generate new ID
            if items:
                new_id = max(item.get('id', 0) for item in items) + 1
            else:
                new_id = 1
            
            # Create new item
            new_item = {
                "id": new_id,
                **body,
                "status": body.get('status', 'enrolled')  # Default value
            }
            
            items.append(new_item)
            db[RESOURCE] = items
            save_database(db)
            
            send_json(self, 201, True, new_item)
            return
        
        send_json(self, 404, False, 'Endpoint not found')
    
    # ========== UPDATE (full or partial) ==========
    # PUT /api/enrollments/:id
    # PATCH /api/enrollments/:id
    def do_PUT(self):
        self._handle_update()
    
    def do_PATCH(self):
        self._handle_update()
    
    def _handle_update(self):
        path_parts = self.path.strip('/').split('/')
        
        # PUT/PATCH /api/enrollments/:id
        if len(path_parts) == 3 and path_parts[0] == 'api' and path_parts[1] == RESOURCE:
            try:
                item_id = int(path_parts[2])
                body = self.read_json_body()
                
                db = load_database()
                items = db.get(RESOURCE, [])
                
                # Find item by id
                idx = next((i for i, item in enumerate(items) if item.get('id') == item_id), -1)
                if idx == -1:
                    send_json(self, 404, False, 'Not found')
                    return
                
                # Update item (preserve id)
                items[idx] = {**items[idx], **body, "id": items[idx].get('id')}
                db[RESOURCE] = items
                save_database(db)
                
                send_json(self, 200, True, items[idx])
            except ValueError:
                send_json(self, 400, False, 'Invalid ID format')
            return
        
        send_json(self, 404, False, 'Endpoint not found')
    
    # ========== DELETE ==========
    # DELETE /api/enrollments/:id
    def do_DELETE(self):
        path_parts = self.path.strip('/').split('/')
        
        # DELETE /api/enrollments/:id
        if len(path_parts) == 3 and path_parts[0] == 'api' and path_parts[1] == RESOURCE:
            try:
                item_id = int(path_parts[2])
                
                db = load_database()
                items = db.get(RESOURCE, [])
                
                # Find item by id
                idx = next((i for i, item in enumerate(items) if item.get('id') == item_id), -1)
                if idx == -1:
                    send_json(self, 404, False, 'Not found')
                    return
                
                # Remove item
                removed = items.pop(idx)
                db[RESOURCE] = items
                save_database(db)
                
                send_json(self, 200, True, removed)
            except ValueError:
                send_json(self, 400, False, 'Invalid ID format')
            return
        
        send_json(self, 404, False, 'Endpoint not found')

# ===== RUN SERVER =====
if __name__ == "__main__":
    server = HTTPServer(('', 5000), EnrollmentAPI)
    print("=" * 50)
    print("🚀 Enrollment API Server Running")
    print("=" * 50)
    print(f"📍 Server: http://127.0.0.1:5000")
    print(f"📁 Resource: {RESOURCE}")
    print(f"📋 Required Fields: {REQUIRED_FIELDS}")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print("\n📌 Available Endpoints:")
    print(f"  GET    /api/{RESOURCE}")
    print(f"  GET    /api/{RESOURCE}/:id")
    print(f"  POST   /api/{RESOURCE}")
    print(f"  PUT    /api/{RESOURCE}/:id")
    print(f"  PATCH  /api/{RESOURCE}/:id")
    print(f"  DELETE /api/{RESOURCE}/:id")
    print("=" * 50)
    server.serve_forever()