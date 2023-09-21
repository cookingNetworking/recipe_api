"""
Views for user API.
"""
from rest_framework import status, generics, permissions, authentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema,OpenApiExample, OpenApiParameter, OpenApiTypes

from django.core.cache import cache
from django.contrib.auth import get_user_model, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from django.middleware.csrf import rotate_token

from celery.contrib.abortable import AbortableAsyncResult
from datetime import datetime

from user.tasks import delete_unactivate_user, sending_mail, celery_app
from user.utils import  create_jwt, decode_jwt
from user.serializer import (
        UserSerializer,
        LoginSerializer,
        Ok200serializer,
        Created201serializer,
        Error400Serializer,
        Error401Serializer,
        Error500Serializer,
        CheckEmailResponseSerializer,
        CheckUsernameResponseSerializer,
        EmailSerializer,
        UsernameSerializer,
        )


@extend_schema(  
    parameters=[
                OpenApiParameter(
               name='X-CSRFToken',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.HEADER,
               required=True,
               description='CSRF token for request'
          ),
    ],
    responses={
        201: Created201serializer,
        400: Error400Serializer,
        500: Error500Serializer,
    },
    examples=[
            OpenApiExample(
        'User created!',
        value={'message': 'User created, please check yout email to active your account in 15 minutes !', 'token': 'Token that sendiing to email of user'},
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
@method_decorator(csrf_protect, name='dispatch')
class CreateUserView(generics.CreateAPIView):
    """Create user API."""
    permission_classes = [permissions.AllowAny]
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
            result = delete_unactivate_user.apply_async((email,), countdown=15*60)
            cache.set(f'del_unactive_{email}', result.id, 9000)
            payload = {
                "email": email,
                "exp" : current_time + (15 * 60)
            }
            token = create_jwt(**payload)
            link = f"http://cookNetwork/vertify?token={token}"
            content = {
                 "subject": "Activate your account",
                 "message":f"Click the link to activate your account at cooNetwork!!\n{link}\nWarning : If you haven't sing up an accoutn at cookNetwork, please don't click th link!!!"
                 }
            sending_mail.apply_async(args=(email,), kwargs=content, countdown=0)
            return Response({'message':'User created, please check yout email to active your account in 15 minutes !','token': f'{token}'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            celery_app.control.revoke(result.id, terminate=True, signal='SIGKILL')
            get_user_model().objects.filter(email=email).delete()
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    parameters=[
          OpenApiParameter(
               name='X-CSRFToken',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.HEADER,
               required=True,
               description='CSRF token for request'
          ),
    ],
    request=LoginSerializer,
    responses={
        400: Error400Serializer,
    }
)
@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    """Login views for user an will return a session in header"""
    permission_classes = [permissions.AllowAny,]
    authentication_classes = [authentication.SessionAuthentication,]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        print(request)
        if serializer.is_valid():
            print(serializer.validated_data)
            user = serializer.validated_data['user']
            login(request, user)
            rotate_token(request)
            csrf_token = request.META.get('CSRF_COOKIE', '')
            print(request.META)
            session_id = request.session.session_key
            print(csrf_token)
            print(type(csrf_token))
            print(type(session_id))
            return Response({'session_id': session_id, 'csrf_token': csrf_token}, status=status.HTTP_200_OK)
        
        return Response({'error':serializer.errors,'detail':'Please login again!'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message':"Successed logout."}, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='X-CSRFToken',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=True,
            description='CSRF token for request'
        ),
    ],    
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
@method_decorator(csrf_protect, name='dispatch')
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
    parameters=[
          OpenApiParameter(
               name='X-CSRFToken',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.HEADER,
               required=True,
               description='CSRF token for request'
          ),
    ],
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


@extend_schema(
                parameters=[
                            OpenApiParameter(
                            name='token',
                            type=str,
                            location=OpenApiParameter.QUERY,
                            description='Your token description here',
                            required=True
                            ),
                ],
                responses={
                            200: Ok200serializer,
                            400: Error400Serializer,
                            401: Error401Serializer,
                            500: Error500Serializer,},
                            examples=[
                                 OpenApiExample(
                                    'Email exist Error',
                                    value={'error': 'User is been actived!!!', 'detail': 'Redirect to login page, please login cookNetwoking with your email and password!'},
                                    response_only=True,
                                    status_codes=['200']
                                ),
                                OpenApiExample(
                                    'Email exist Error',
                                    value={'error': 'Email has not been sign up , please check again!!!', 'detail': 'Please sign up again.'},
                                    response_only=True,
                                    status_codes=['400']
                                ),
                                OpenApiExample(
                                    'Email exist Error',
                                    value={'error': 'Username is already existed !!!', 'detail': 'Please use another username.'},
                                    response_only=True,
                                    status_codes=['401']
                                ),
                                OpenApiExample(
                                    'Internal Error',
                                    value={'error': 'Internal server error'},
                                    response_only=True,
                                    status_codes=['500']
                                )
                                ],
                description='Checks activate link is correctly or not, the link will present like [/signupVertify?token="token"] ',
            )
@api_view(['GET'])
def sign_up_vertify(request):
    """Vertify token is leagal or not!"""

    try:
        token = request.query_params.get("token")
        result = decode_jwt(token)
        user = get_user_model().objects.get(email=result["email"])
        if not user:
            return Response(
                    {'error':'Email has not been sign up , please check again!!!','detail': 'Please sign up again.'},
                    status=status.HTTP_400_BAD_REQUEST
                    )
        current_time = int(datetime.now().timestamp())
        if current_time > result["exp"]:
            return Response(
                            {'error':'Token is expired.','detail': 'Please sign up again.'},
                            status=status.HTTP_401_UNAUTHORIZED
                            )
        user.is_active = True
        user.save()
        task_id = cache.get(f'del_unactive_{result["email"]}')
        res = AbortableAsyncResult(task_id)
        res.abort()
        if res.state == 'REVOKED' or res.state == 'ABORTED':
            print("Taks canceled")
        else:
            print(f"task staus: {result.state}")
        return Response({'message': 'User is been actived!!', "detail": "Redirect to login page, please login cookNetwoking with your email and password!"}, status=status.HTTP_200_OK)
    except Exception as e:
            print(e)
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
     responses={
                200: Ok200serializer,
               },
               examples=[
                        OpenApiExample(
                        'getToken success',
                        value={'message': 'CSRF cookie set', 'detail': 'X-CSRFToken will return in cookies. Please set X-CSRFToken header when send post, put, update method '},
                        response_only=True,
                        status_codes=['200']
                    ),]
)
@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCsrfToken(APIView):
    """Get csrf_token protect from csrf attact!!!"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        return Response({'message':'CSRF cookie set','detail': 'X-CSRFToken will return in cookies. Please set X-CSRFToken header when send post, put, update method '}, status=status.HTTP_200_OK)