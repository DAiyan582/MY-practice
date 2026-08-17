import os
import base64
from functools import wraps

# ===== CONFIGURATION =====
# Environment variable with fallback default
API_KEY = os.environ.get('API_KEY', 'secret123')

# ===== API KEY AUTHENTICATION =====
def check_api_key(headers):
    """
    Check API Key authentication
    
    Args:
        headers: Dictionary of request headers
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Get API key from headers (case-insensitive)
    key = headers.get('x-api-key')
    
    # Alternative: check both common header formats
    if not key:
        key = headers.get('X-API-Key')
    
    # Validate
    return key == API_KEY

# ===== BASIC AUTHENTICATION =====
def check_basic_auth(headers):
    """
    Check Basic Authentication (username/password)
    
    Args:
        headers: Dictionary of request headers
        
    Returns:
        bool: True if valid, False otherwise
    """
    auth_header = headers.get('authorization')
    
    # Check if Authorization header exists and starts with 'Basic '
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    
    try:
        # Extract base64 encoded credentials
        encoded = auth_header.split(' ')[1]
        
        # Decode base64 and split username:password
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        # Validate credentials
        return (username == 'admin' and password == '12345')
        
    except (IndexError, ValueError, base64.binascii.Error):
        # Handle invalid base64 or malformed header
        return False

# ===== DECORATOR VERSION (for Flask/FastAPI) =====

def require_api_key(func):
    """
    Decorator to require API Key authentication
    Use with Flask/FastAPI routes
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get headers from request (depends on framework)
        # For Flask: from flask import request
        # headers = request.headers
        
        # For now, we'll pass headers as argument
        # This is a template - actual implementation depends on framework
        return func(*args, **kwargs)
    return wrapper

# ===== CLASS VERSION (for BaseHTTPRequestHandler) =====

class AuthMiddleware:
    """
    Authentication middleware for BaseHTTPRequestHandler
    """
    
    @staticmethod
    def check_api_key(headers):
        """Check API Key authentication"""
        key = headers.get('X-API-Key')
        return key == API_KEY
    
    @staticmethod
    def check_basic_auth(headers):
        """Check Basic authentication"""
        auth_header = headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            return False
        
        try:
            encoded = auth_header.split(' ', 1)[1]
            decoded = base64.b64decode(encoded).decode()
            username, password = decoded.split(':', 1)
            return (username == 'admin' and password == '12345')
        except:
            return False
    
    @staticmethod
    def authenticate(headers, auth_type='api_key'):
        """
        Generic authentication method
        
        Args:
            headers: Request headers
            auth_type: 'api_key' or 'basic'
            
        Returns:
            bool: True if authenticated
        """
        if auth_type == 'api_key':
            return AuthMiddleware.check_api_key(headers)
        elif auth_type == 'basic':
            return AuthMiddleware.check_basic_auth(headers)
        return False