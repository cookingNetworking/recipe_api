"""
Replicated function.
"""

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from functools import wraps
import os
import jwt

def create_jwt(**payload):
    """Generate a jwt token ."""
    key = os.environ.get('secret_key')
    encoded = jwt.encode(payload, str(key), algorithm='HS256')
    return encoded

def decode_jwt(token):
    """Decode  jwt token"""
    key = os.environ.get('secret_key')
    decode = jwt.decode(token, str(key), algorithms=['HS256'])
    return decode

def conditional_csrf_decorator(views):
    """Csrf protect would set up by develop environments!"""
    if os.environ.get('DEV_ENV') == 'true':
        return csrf_exempt(views)
    else:
        return csrf_protect(views)