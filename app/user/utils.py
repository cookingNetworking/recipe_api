"""
Replicated function.
"""


from django.core.mail import send_mail
from rest_framework.response import Response

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
    decode = jwt.decode(token, str(key), algorithm='HS256')
    return decode
def sending_mail(toeamil, **content):
    """Function to send email . """
    try:
        send_mail(
        f"{content['subject']}",
        f"{content['message']}",
        "as2229181@gmail.com",
        [f"{toeamil}"],
        fail_silently=False,
        )
        return
    except Exception as e:
        return e
