from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_social_oauth2.authentication import SocialAuthentication

class SocialAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'rest_framework_social_oauth2.authentication.SocialAuthentication'
    name = 'SocialAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'oauth2',
            'flows': {
                'authorizationCode': {
                    'authorizationUrl': 'https://provider.com/o/authorize',
                    'tokenUrl': 'https://provider.com/o/token',
                    'refreshUrl': 'https://provider.com/o/refresh',
                    'scopes': {
                        'read': 'Read scope',
                        'write': 'Write scope'
                    }
                }
            }
        }
