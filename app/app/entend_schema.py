"""
Customerized drf-spectacular extend schema!
"""

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response


class CustomSpectacularAPIView(SpectacularAPIView):
    def get(self, request, *args, **kwargs):
        #get the autocreate schema from function view or class bass view!
        schema = super().get(request, *args, **kwargs).data

        # Add the schema manually!
        schema['paths']['/social/login/google-oauth2/'] = {
            'get': {
                'operationId': 'googleOAuth2Login',
                'summary': 'Google OAuth2 login',
                'description': 'User google account to login cookingnetwork',
                'tags': ['Auth'],
                'responses': {
                    '302': {
                        'description': 'Redirect to the home page',
                    },
                    '400': {
                        'description': 'Bad request!',
                    }
                },
            },
        }
        schema['paths']['ws/notify/'] = {
            'get': {
                'operationId': 'Websocket connetion for notification',
                'summary': 'Websocket connetion for notification',
                'description': 'Connect the server with websocket protocol, and add to the user group!',
                'tags': ['WS'],
                'responses': {
                    '101': {
                        'description': ' Websocket connect!!',
                    },
                    '500'
                    : {
                        'description': ' Server error!',
                    },
                    '502':{
                        'description': '  Unauthenticated user attempted to connect!!',
                    }
                },
            },
        }

        return Response(schema)