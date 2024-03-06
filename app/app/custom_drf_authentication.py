"""
Design customerizer authenticaiton class!
"""
import os
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        # If develop environment is false enforce csrf
        if os.environ.get('DEV_ENV') != 'true':
            super().enforce_csrf(request)
