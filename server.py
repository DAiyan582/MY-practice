from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import os
import sys
import traceback

# ===== IMPORT ROUTES =====
# Import your route handlers
# from routes import enrollments  # We'll define this inline for simplicity

# ===== CONFIGURATION =====
PORT = 5000
API_KEY = os.environ.get('API_KEY', 'secret123')

# ===== AUTHENTICATION MIDDLEWARE =====
def check_api_key(headers):
    """
    Check API Key from request headers
    
    Args:
        headers: Dictionary of request headers
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    key = headers.get('X-API-Key')
    return key == API_KEY

def check_basic_auth(headers):
    """
    Check Basic Authentication
    
    Args:
        headers: Dictionary of request headers
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    import base64
    auth_header = headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    
    try:
        encoded = auth_header.split(' ')[1]
        decoded = base64.b64decode(encoded).decode()
        username, password = decoded.split(':', 1)
        return (username == 'admin' and password == '12345')
    except:
        return False

# ===== DATABASE HELPERS =====
def load_db():
    """Load database from JSON file"""
    try:
        with open('data/db.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        # Create default database
        default_db = {"enrollments": []}
        save_db(default_db)
        return default_db
    except json.JSONDecodeError:
        return {"enrollments": []}

def save_db(data):
    """Save database to JSON file"""
    import os
    os.makedirs('data', exist_ok=True)
    with open('data/db.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)

# ===== ROUTE HANDLERS =====

def handle_enrollments(handler, method, path_parts, body=None, query_params=None):
    """
    Handle all /api/enrollments routes
    
    Args:
        handler: The BaseHTTPRequestHandler instance
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        path_parts: List of URL path parts
        body: Request body (for POST/PUT/PATCH)
        query_params: Query parameters (for GET)
    """
    db = load_db()
    resource = db.get('enrollments', [])
    
    # GET /api/enrollments
    if len(path_parts) == 2:
        if method == 'GET':
            # Apply filters from query params
            result = resource.copy()
            if query_params:
                for key, values in query_params.items():
                    if values:
                        value = values[0]
                        result = [item for item in result if str(item.get(key)) == str(value)]
            
            send_json(handler, 200, True, result)
            return
        
        # POST /api/enrollments
        elif method == 'POST':
            if not body:
                send_json(handler, 400, False, 'Missing request body')
                return
            
            # Validate required fields
            required_fields = ['studentName', 'courseCode']
            missing = [f for f in required_fields if f not in body]
            if missing:
                send_json(handler, 400, False, f'Missing fields: {", ".join(missing)}')
                return
            
            # Generate new ID
            if resource:
                new_id = max(item.get('id', 0) for item in resource) + 1
            else:
                new_id = 1
            
            # Create new enrollment
            new_item = {
                'id': new_id,
                **body,
                'status': body.get('status', 'enrolled')
            }
            
            resource.append(new_item)
            db['enrollments'] = resource
            save_db(db)
            
            send_json(handler, 201, True, new_item)
            return
    
    # GET /api/enrollments/:id
    # PUT /api/enrollments/:id
    # PATCH /api/enrollments/:id
    # DELETE /api/enrollments/:id
    if len(path_parts) == 3:
        try:
            item_id = int(path_parts[2])
        except ValueError:
            send_json(handler, 400, False, 'Invalid ID format')
            return
        
        # Find item by ID
        idx = next((i for i, item in enumerate(resource) if item.get('id') == item_id), -1)
        
        # GET /api/enrollments/:id
        if method == 'GET':
            if idx == -1:
                send_json(handler, 404, False, 'Not found')
                return
            send_json(handler, 200, True, resource[idx])
            return
        
        # PUT /api/enrollments/:id
        # PATCH /api/enrollments/:id
        if method in ['PUT', 'PATCH']:
            if idx == -1:
                send_json(handler, 404, False, 'Not found')
                return
            
            if not body:
                send_json(handler, 400, False, 'Missing request body')
                return
            
            # Update item (preserve id)
            resource[idx] = {**resource[idx], **body, 'id': item_id}
            db['enrollments'] = resource
            save_db(db)
            
            send_json(handler, 200, True, resource[idx])
            return
        
        # DELETE /api/enrollments/:id
        if method == 'DELETE':
            if idx == -1:
                send_json(handler, 404, False, 'Not found')
                return
            
            deleted = resource.pop(idx)
            db['enrollments'] = resource
            save_db(db)
            
            send_json(handler, 200, True, deleted)
            return
    
    # If we get here, route not found
    send_json(handler, 404, False, 'Route not found')

# ===== HELPER FUNCTION =====

def send_json(handler, status, success, data_or_msg):
    """
    Send JSON response
    
    Args:
        handler: The BaseHTTPRequestHandler instance
        status: HTTP status code
        success: Boolean (True/False)
        data_or_msg: Data if success=True, error message if success=False
    """
    if success:
        response = {'success': True, 'data': data_or_msg}
    else:
        response = {'success': False, 'msg': data_or_msg}
    
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json')
    handler.end_headers()
    handler.wfile.write(json.dumps(response).encode())

# ===== MAIN SERVER CLASS =====

class StudentAPI(BaseHTTPRequestHandler):
    
    def read_json_body(self):
        """Read and parse JSON from request body"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return None
        
        body = self.rfile.read(content_length)
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    
    def handle_health_check(self):
        """Handle health check at root endpoint"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'success': True,
            'msg': 'API running'
        }).encode())
    
    def do_GET(self):
        # Parse URL
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)
        
        # Health check: GET /
        if path == '/':
            self.handle_health_check()
            return
        
        # Split path into parts
        path_parts = path.strip('/').split('/')
        
        # Check if path starts with /api/enrollments
        if len(path_parts) >= 2 and path_parts[0] == 'api' and path_parts[1] == 'enrollments':
            # Apply authentication middleware
            if not check_api_key(self.headers):
                send_json(self, 401, False, 'Unauthorized')
                return
            
            # Route to handler
            handle_enrollments(self, 'GET', path_parts[1:], query_params=query_params)
            return
        
        # 404 - Route not found
        send_json(self, 404, False, 'Route not found')
    
    def do_POST(self):
        # Parse URL
        parsed = urlparse(self.path)
        path = parsed.path
        path_parts = path.strip('/').split('/')
        
        # Check if path starts with /api/enrollments
        if len(path_parts) >= 2 and path_parts[0] == 'api' and path_parts[1] == 'enrollments':
            # Apply authentication middleware
            if not check_api_key(self.headers):
                send_json(self, 401, False, 'Unauthorized')
                return
            
            # Read request body
            body = self.read_json_body()
            
            # Route to handler
            handle_enrollments(self, 'POST', path_parts[1:], body=body)
            return
        
        # 404 - Route not found
        send_json(self, 404, False, 'Route not found')
    
    def do_PUT(self):
        # Parse URL
        parsed = urlparse(self.path)
        path = parsed.path
        path_parts = path.strip('/').split('/')
        
        # Check if path starts with /api/enrollments
        if len(path_parts) >= 2 and path_parts[0] == 'api' and path_parts[1] == 'enrollments':
            # Apply authentication middleware
            if not check_api_key(self.headers):
                send_json(self, 401, False, 'Unauthorized')
                return
            
            # Read request body
            body = self.read_json_body()
            
            # Route to handler
            handle_enrollments(self, 'PUT', path_parts[1:], body=body)
            return
        
        # 404 - Route not found
        send_json(self, 404, False, 'Route not found')
    
    def do_PATCH(self):
        # Parse URL
        parsed = urlparse(self.path)
        path = parsed.path
        path_parts = path.strip('/').split('/')
        
        # Check if path starts with /api/enrollments
        if len(path_parts) >= 2 and path_parts[0] == 'api' and path_parts[1] == 'enrollments':
            # Apply authentication middleware
            if not check_api_key(self.headers):
                send_json(self, 401, False, 'Unauthorized')
                return
            
            # Read request body
            body = self.read_json_body()
            
            # Route to handler
            handle_enrollments(self, 'PATCH', path_parts[1:], body=body)
            return
        
        # 404 - Route not found
        send_json(self, 404, False, 'Route not found')
    
    def do_DELETE(self):
        # Parse URL
        parsed = urlparse(self.path)
        path = parsed.path
        path_parts = path.strip('/').split('/')
        
        # Check if path starts with /api/enrollments
        if len(path_parts) >= 2 and path_parts[0] == 'api' and path_parts[1] == 'enrollments':
            # Apply authentication middleware
            if not check_api_key(self.headers):
                send_json(self, 401, False, 'Unauthorized')
                return
            
            # Route to handler
            handle_enrollments(self, 'DELETE', path_parts[1:])
            return
        
        # 404 - Route not found
        send_json(self, 404, False, 'Route not found')
    
    # ===== ERROR HANDLING =====
    
    def handle_error(self):
        """Handle any unhandled errors"""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_msg = f"{exc_type.__name__}: {exc_value}"
        
        # Log error for debugging
        print(f"ERROR: {error_msg}")
        traceback.print_exc()
        
        # Send error response
        send_json(self, 500, False, 'Server error')

# ===== RUN SERVER =====

def run_server():
    """Start the HTTP server"""
    try:
        server = HTTPServer(('', PORT), StudentAPI)
        print("=" * 50)
        print("🚀 API Running on http://localhost:5000")
        print("=" * 50)
        print(f"🔑 API Key: {API_KEY}")
        print("📌 Available Endpoints:")
        print("  GET    /")
        print("  GET    /api/enrollments")
        print("  GET    /api/enrollments/:id")
        print("  POST   /api/enrollments")
        print("  PUT    /api/enrollments/:id")
        print("  PATCH  /api/enrollments/:id")
        print("  DELETE /api/enrollments/:id")
        print("=" * 50)
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server()