"""
Customerize Middle ware!
"""
import os

from django.utils.deprecation import MiddlewareMixin
from social_core.exceptions import AuthStateMissing
from django.shortcuts import redirect

class SocialAuthException(MiddlewareMixin):
    """
    Hnadle state missing problem!
    """
    def process_exception(self, request, exception):
        if isinstance(exception, AuthStateMissing):
            user = request.user
            if user.is_authenticated:
                #If the session id exist redirect to the path you set.
                return redirect('swagger-ui')
                #If the session id not exist , redirect google oauth page.
            return redirect('social:begin', backend='google-oauth2')


class CheckSessionMiddleware(MiddlewareMixin):
    """Check session id is exist or not when use /social/login/google-oauth2/ api"""
    def process_request(self, request):
        if request.path == '/social/login/google-oauth2/':
            session_id = request.COOKIES.get('sessionid', None)
            print(session_id)
            if session_id:
                return redirect('swagger-ui')
        return None