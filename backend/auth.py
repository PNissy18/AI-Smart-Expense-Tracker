"""
Authentication module for AI Smart Expense Tracker.
Provides JWT token creation/validation and login_required decorator.
"""
import jwt
import functools
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, g

# Secret key for JWT signing — change this in production!
SECRET_KEY = 'ai-expense-tracker-secret-key-2026'
TOKEN_EXPIRY_HOURS = 24


def create_token(user_id, email):
    """Create a JWT token for an authenticated user."""
    payload = {
        'sub': user_id,
        'email': email,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token):
    """Decode and validate a JWT token."""
    return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])


def login_required(f):
    """
    Decorator to protect API endpoints.
    Extracts JWT from Authorization header, validates it,
    and sets g.user_id and g.user_email for the request.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401

        token = auth_header.split(' ')[1]

        try:
            payload = decode_token(token)
            g.user_id = payload['sub']
            g.user_email = payload['email']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired. Please login again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token. Please login again.'}), 401

        return f(*args, **kwargs)
    return decorated
