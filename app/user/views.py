"""
Views for user API.
"""
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema,OpenApiExample

from user.serializer import UserSerializer, Error400Serializer, Error500Serializer
@extend_schema( responses={
                        201: UserSerializer,
                        400: Error400Serializer,
                        500: Error500Serializer,
                    },
                    examples=[
                    OpenApiExample(
                        'Email Error',
                        value={'error': 'Email field is required!!!', 'detail': 'Please provide an email.'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        'Internal Error',
                        value={'error': 'Internal server error'},
                        response_only=True,
                        status_codes=['500']
                    )
                    ],
                    description='Create a new user',)
class CreateUserView(generics.CreateAPIView):
    """Create user API."""
    serializer_class = UserSerializer



    
    def create(self, request, *args, **kwargs):
        """Add customerized status code."""
        try:
            email = request.data.get('email')
            print(request)
            print(request.data)
            if not email or len(email)==0:
                return Response({'error':'Email field is required!!!','detail': 'Please provide an email.'}, status=status.HTTP_400_BAD_REQUEST)
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(e)
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@extend_schema(
    responses={
                200: "ok",
                400: Error400Serializer,
                500: Error500Serializer,},
                 examples=[
                    OpenApiExample(
                        'Email exist Error',
                        value={'error': 'Email is already existed !!!', 'detail': 'Please use another email.'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        'Internal Error',
                        value={'error': 'Internal server error'},
                        response_only=True,
                        status_codes=['500']
                    )
                    ],
    description='Checks if an email is already taken',
)
@api_view(['POST'])
def check_email_replicate(request):
    """Check create user request email and password is existed or not."""

    try:
        if get_user_model().objects.filter(eamil=request.data.get('email')).exists():
            return Response(
                {'error':'Email is already existed !!!','detail': 'Please use another email.'}, 
                status=status.HTTP_400_BAD_REQUEST
                )
    except Exception as e:
            print(e)
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

