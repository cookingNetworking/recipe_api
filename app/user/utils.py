"""
Replicated function.
"""
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
