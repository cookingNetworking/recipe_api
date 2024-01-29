"""
Customerize Middle ware!
"""
from social_core.exceptions import AuthStateMissing
from django.shortcuts import redirect

class SocialAuthException:
    """
    Hnadle state missing problem!
    """
    def process_exception(self, request, exception):
        if isinstance(exception, AuthStateMissing):
            return redirect('social:begin', backend='google-oauth2')