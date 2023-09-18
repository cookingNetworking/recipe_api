"""
Views for user API.
"""
from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema,OpenApiExample

from datetime import datetime
from user.tasks import delete_unactivate_user

from user.utils import  create_jwt, sending_mail 
from user.serializer import (
        UserSerializer,
        Created201serializer,
        Error400Serializer,
        Error500Serializer,
        CheckEmailResponseSerializer,
        CheckUsernameResponseSerializer,
        EmailSerializer,
        UsernameSerializer,
        )
@extend_schema( responses={
                        201: Created201serializer,
                        400: Error400Serializer,
                        500: Error500Serializer,
                    },
                    examples=[
                         OpenApiExample(
                        'User created!',
                        value={'message': 'User created, please check yout email to active your account in 15 minutes !', 'token': 'Bear token'},
                        response_only=True,
                        status_codes=['201']
                        ),
                    OpenApiExample(
                        'Email or password Error',
                        value={'error': 'Email or password field is required!!!', 'detail': 'Please provide an email or password.'},
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
            password = request.data.get('password')
            if not email or len(email) == 0:
                return Response({'error':'Email field is required!!!','detail': 'Please provide an email.'}, status=status.HTTP_400_BAD_REQUEST)
            if not password or len(password) == 0:
                 return Response({'error':'Password field is required!!!','detail': 'Please provide password.'}, status=status.HTTP_400_BAD_REQUEST)
            super().create(request, *args, **kwargs)
            current_time = int(datetime.now().timestamp())
            delete_unactivate_user.apply_async((email,), countdown=3)
            payload = {
                "email": email,
                "exp" : current_time + (1 * 60)
            }
            token = create_jwt(**payload)
            link = f"http://cookNetwork/vertify?token={token}"
            content = {
                 "subject": "Activate your account", 
                 "message":f"Click the link to activate your account at cooNetwork!!\n{link}\nWarning : If you haven't sing up an accoutn at cookNetwork, please don't click th link!!!"
                 }     
            sending_mail(email, **content)
            return Response({'message':'User created, please check yout email to active your account in 15 minutes !','token': f'Bear {token}'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            get_user_model().objects.filter(email=email).delete()
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    request = EmailSerializer,
    responses={
                200: CheckEmailResponseSerializer,
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
        if get_user_model().objects.filter(email=request.data.get('email')).exists():
            return Response(
                {'error':'Email is already existed !!!','detail': 'Please use another email.'},
                status=status.HTTP_400_BAD_REQUEST
                )
        return Response({'message':'Email check ok!','detail':'User could use this email!'}, status=status.HTTP_200_OK)
    except Exception as e:
            print(e)
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@extend_schema(
                request = UsernameSerializer,
                responses={
                            200: CheckUsernameResponseSerializer,
                            400: Error400Serializer,
                            500: Error500Serializer,},
                            examples=[
                                OpenApiExample(
                                    'Email exist Error',
                                    value={'error': 'Username is already existed !!!', 'detail': 'Please use another username.'},
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
def check_username_replicate(request):
    """Check create user request email and password is existed or not."""

    try:
        if get_user_model().objects.filter(username=request.data.get('username')).exists():
            return Response(
                {'error':'Username is already existed !!!','detail': 'Please use another username.'},
                status=status.HTTP_400_BAD_REQUEST
                )
        return Response({'message':'username check ok!', 'detail':'User could use this username!'}, status=status.HTTP_200_OK)
    except Exception as e:
            print(e)
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

