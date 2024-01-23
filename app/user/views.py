"""
Views for user API.
"""


from rest_framework import (status,
                            generics,
                            permissions,
                            authentication,
                            mixins,
                            viewsets
                            )
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
                                    extend_schema,
                                    extend_schema_view,
                                    OpenApiExample,
                                    OpenApiParameter,
                                    OpenApiTypes,
                                    OpenApiResponse
                                    )

from django.conf import settings
from django.http import JsonResponse
from urllib.parse import urlencode
from django.core.cache import cache
from django.contrib.auth import get_user_model, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from django.middleware.csrf import rotate_token


from celery.contrib.abortable import AbortableAsyncResult
from datetime import datetime
from jwt.exceptions import ExpiredSignatureError

from core.models import UserFollowing
from user.tasks import delete_unactivate_user, sending_mail, celery_app
from user.utils import  create_jwt, decode_jwt
from user.serializers import (
                                UserSerializer,
                                UserDetailResponseSerializer,
                                PasswordSerialzier,
                                LoginSerializer,
                                Ok200serializer,
                                Created201serializer,
                                Error400Serializer,
                                Error401Serializer,
                                Error403CSRFTokenmissingSerialzier,
                                Error500Serializer,
                                FollowSerializer,
                                CheckEmailResponseSerializer,
                                CheckUsernameResponseSerializer,
                                EmailSerializer,
                                UsernameSerializer,
                                )

@extend_schema(
    parameters=[
         OpenApiParameter(
            name='Session_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.COOKIE,
            required=True,
            description='Ensure session id is in cookie!'
            )
        ],
        responses={
        200: UserSerializer,
        403: 'You do not have permission to perform this action.',

    },
        examples=[
        OpenApiExample(
            "Request forbbiden",
            value={'detail': 'You do not have permission to perform this action.'},
            response_only=True,
            status_codes=['403']
            ),
        ]
)
class UserListView(generics.ListAPIView):
    """List all user API.\t Only admin user can access this API!"""
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()


@extend_schema(
    parameters=[
            OpenApiParameter(
            name='X-CSRFToken',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=True,
            description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken!'
          )
    ],
    responses={
        201: Created201serializer,
        400: Error400Serializer,
        403: Error403CSRFTokenmissingSerialzier,
        500: Error500Serializer,
    },
    examples=[
        OpenApiExample(
        'User created!',
        value={'message': 'User created, please check your email to active your account in 15 minutes !', 'token': 'Token that sendiing to email of user'},
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
        "Request forbbiden",
        value={'error': 'CSRF token missing or incorrect.'},
        response_only=True,
        status_codes=['403']
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
            role = request.data.get('role')
            if role == 'admin':
                return Response({'error':'Admin is not allowed!!!','detail': 'Please change the role.'}, status=status.HTTP_400_BAD_REQUEST)
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
            return Response({'message':'User created, please check your email to active your account in 15 minutes !','token': f'{token}'}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
        # Handle validation errors (like email already exists) here
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if 'result' in locals():
                celery_app.control.revoke(result.id, terminate=True, signal='SIGKILL')
            print(e)
            get_user_model().objects.filter(email=email).delete()
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDetailView(generics.RetrieveUpdateAPIView):
    """Manage the user detail."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
            parameters=[
                OpenApiParameter(
                name='Session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                required=True,
                description='Ensure session id is in cookie!'
                )
            ],
            request=UserDetailResponseSerializer,
            responses={
                200:UserDetailResponseSerializer,
                403:"Authentication credentials were not provided.",
                },
            examples=[
                OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            ]
            )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='X-CSRFToken',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken'
            ),
            OpenApiParameter(
                name='Session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                required=True,
                description='Ensure session id is in cookie!'
            )
        ],
        request=UserDetailResponseSerializer,
        responses={
            200:UserDetailResponseSerializer,
            403:"Authentication credentials were not provided.",
            500:Error500Serializer
            },
        examples=[
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"error":"Inernal error messages"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    )
    @method_decorator(csrf_protect, name='dispatch')
    def put(self, request, *args, **kwargs):
        try:
            return super().put(request, *args, **kwargs)
        except Exception as e:
            return Response({"c":f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
            parameters=[
               OpenApiParameter(
               name='X-CSRFToken',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.HEADER,
               required=True,
               description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken'
               ),
                OpenApiParameter(
                name='Session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                required=True,
                description='Ensure session id is in cookie!'
                )
            ],
            request=UserDetailResponseSerializer,
            responses={
                200:UserDetailResponseSerializer,
                403:"Authentication credentials were not provided.",
                500:Error500Serializer
                },
            examples=[
                OpenApiExample(
                    "Request forbbiden",
                    value={"detail":"Authentication credentials were not provided."},
                    response_only=True,
                    status_codes=['403']
                ),
                OpenApiExample(
                    "Request forbbiden",
                    value={"error":"Inernal error messages"},
                    response_only=True,
                    status_codes=['500']
                ),
            ]
            )
    @method_decorator(csrf_protect, name='dispatch')
    def patch(self, request, *args, **kwargs):
        try:
            return super().patch(request, *args, **kwargs)
        except Exception as e:
            return Response({"c":f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user

@extend_schema(
    parameters=[
          OpenApiParameter(
               name='X-CSRFToken',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.HEADER,
               required=True,
               description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken'
               )
    ],
    request=LoginSerializer,
    responses={
        200: Ok200serializer,
        400: Error400Serializer,
        403: Error403CSRFTokenmissingSerialzier,
        500: Error500Serializer
    },
    examples=[
        OpenApiExample(
        'User login!',
        value={'message': 'Login successed!', 'detail': "user detai example: {'email': 'superuser@django.com', 'username': 'example', 'role': 'user'}"},
        description = "When login successed, server would response new csrftoken and session id in set-cookies",
        response_only=True,
        status_codes=['200']
        ),
    OpenApiExample(
        "Value or field error",
        value={'error': 'Error message ', 'detail': 'Please login again.'},
        description="Probably have these error :{'field_name': ['This field is required.']},{'char_field': ['Ensure this field has no more than X characters.']}",
        response_only=True,
        status_codes=['400']
    ),
    OpenApiExample(
        "Account is not actived!",
        value={'error': 'Account is not been active!', 'detail': 'Please check your email!!'},
        description="Account is not active!",
        response_only=True,
        status_codes=['400']
    ),
    OpenApiExample(
        "Request forbbiden",
        value={'error': 'CSRF token missing or incorrect.'},
        response_only=True,
        status_codes=['403']
    ),
    OpenApiExample(
        'Internal Error',
        value={'error': 'Internal server error'},
        response_only=True,
        status_codes=['500']
    )
    ],
    description='Create a new user',
)
@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    """Login views for user an will return a session in header"""
    permission_classes = [permissions.AllowAny,]
    authentication_classes = [authentication.SessionAuthentication,]

    def post(self, request):
        if request.user.is_authenticated:
            return Response({"error":"Already login!",'detail':'please redirect to home page!'}, status=status.HTTP_400_BAD_REQUEST)
        email = request.data.get('email')
        user = get_user_model().objects.filter(email=email).first()
        if not user:
            return Response({"error":"Login failed!",'detail':'Please login again!!'}, status=status.HTTP_400_BAD_REQUEST)
        if user.is_active == False:
            return Response({"error":"Account is not been active!",'detail':'Please check your email!!'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            session_id = request.session.session_key
            rotate_token(request)
            user_json = UserSerializer(user)
            csrf_token = request.META.get('CSRF_COOKIE', '')

            return Response({'message':'Login successed!','detail':{'user':user_json.data},"csrf_token":csrf_token}, status=status.HTTP_200_OK)

        return Response({'error':serializer.errors,'detail':'Please login again!'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    parameters=[
          OpenApiParameter(
               name='X-CSRFToken',
               type=OpenApiTypes.STR,
               location=OpenApiParameter.HEADER,
               required=True,
               description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken')
    ],
    responses={
        200: Ok200serializer,
        403 :Error403CSRFTokenmissingSerialzier,
        500: Error500Serializer
    },
    examples=[
    OpenApiExample(
    "Logout succeed",
    value={'message':"Successed logout.",'detail':"Session id remove from "},
    response_only=True,
    status_codes=['200']
    ),
    OpenApiExample(
    "Request forbbiden",
    value={'error': 'CSRF token missing or incorrect.'},
    response_only=True,
    status_codes=['403']
    ),
    OpenApiExample(
        'Internal Error',
        value={'error': 'Internal server error'},
        response_only=True,
        status_codes=['500']
    )
    ]
)
@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    """Clear session id from cookies!"""
    def post(self, request):
        try:
            print(request)
            if not request.headers['X-CSRFToken']:
                return Response({"error":"Loss CSRFToken in request header!","detail":"Please get csrftoken again!"}, status=status.HTTP_403_FORBIDDEN)
            logout(request)
            return Response({'message':"Successed logout.",'detail':"Session id remove from cookies!"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e,1)
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@extend_schema(
    parameters=[
        OpenApiParameter(
            name='X-CSRFToken',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=True,
            description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken'
        ),
    ],
    request = EmailSerializer,
    responses={
                200: CheckEmailResponseSerializer,
                400: Error400Serializer,
                403 :Error403CSRFTokenmissingSerialzier,
                500: Error500Serializer,},
                 examples=[
                     OpenApiExample(
                        "Email okay",
                        value={'message':"Email check ok!",'detail':"User could use this email!"},
                        response_only=True,
                        status_codes=['200']
                    ),
                    OpenApiExample(
                        'Email exist Error',
                        value={'error': 'Email is already existed !!!', 'detail': 'Please use another email.'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        "Request forbbiden",
                        value={'error': 'CSRF token missing or incorrect.'},
                        response_only=True,
                        status_codes=['403']
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
@csrf_protect
def check_email_replicate(request):
    """Check create user request email  is existed or not."""

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
               description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken'
          ),
    ],
    request = UsernameSerializer,
    responses={
                200: CheckUsernameResponseSerializer,
                400: Error400Serializer,
                403 :Error403CSRFTokenmissingSerialzier,
                500: Error500Serializer,},
                examples=[
                     OpenApiExample(
                        "Username check okay",
                        value={'message':"Username check ok!",'detail':"Username could use this email!"},
                        response_only=True,
                        status_codes=['200']
                    ),
                    OpenApiExample(
                        'Username exist Error',
                        value={'error': 'Username is already existed !!!', 'detail': 'Please use another username.'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        "Request forbbiden",
                        value={'error': 'CSRF token missing or incorrect.'},
                        response_only=True,
                        status_codes=['403']
                    ),
                    OpenApiExample(
                        'Internal Error',
                        value={'error': 'Internal server error'},
                        response_only=True,
                        status_codes=['500']
                    )
                    ],
    description='Checks if username is already taken',
)
@api_view(['POST'])
@csrf_protect
def check_username_replicate(request):
    """Check create user request  username is existed or not."""

    try:
        print(request.headers)
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
        500: Error500Serializer,
    },
    examples=[
        OpenApiExample(
            'Email exist Error',
            value={'message': 'User is been actived!!!', 'detail': 'Redirect to login page, please login cookNetwoking with your email and password!'},
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
    description='Checks activate link is correctly or not, the link will present like [/signupVertify?token="token"]',
)
@api_view(['GET'])
def sign_up_vertify(request):
    """Vertify token is leagal or not!"""

    try:
        token = request.query_params.get("token")
        result = decode_jwt(token)
        user = get_user_model().objects.filter(email=result["email"]).first()
        if not user:
            return Response(
                    {'error':'Email has not been sign up , please check again!!!','detail': 'Please sign up again.'},
                    status=status.HTTP_400_BAD_REQUEST
                    )
        user.is_active = True
        user.save()
        task_id = cache.get(f'del_unactive_{result["email"]}')
        res = AbortableAsyncResult(task_id)
        res.abort()
        if res.state == 'REVOKED' or res.state == 'ABORTED':
            print("Taks canceled")
        else:
            print(f"task staus: {res.state}")
        return Response({'message': 'User is been actived!!', "detail": "Redirect to login page, please login cookNetwoking with your email and password!"}, status=status.HTTP_200_OK)
    except ExpiredSignatureError:
        return Response(
            {'error': 'Token is expired.', 'detail': 'Please sign up again.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
            print(e)
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(ensure_csrf_cookie, name='dispatch')
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
class GetCsrfToken(APIView):
    """Get csrf_token protect from csrf attact!!!"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        csrf_token = request.META.get('CSRF_COOKIE', '')
        return Response({'message':'CSRF cookie set','detail': 'X-CSRFToken will return in cookies. Please set X-CSRFToken header when send post, put, update method ','csrfToken': csrf_token}, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ChangePassword(APIView):
    """Change password for authenticated user."""
    permission_classes = [permissions.IsAuthenticated,]
    authentication_classes = [authentication.SessionAuthentication,]

    @extend_schema(
    parameters=[
                OpenApiParameter(
                    name='token',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Your token description here',
                    required=True
                ),
                OpenApiParameter(
                    name='Session_id',
                    type=OpenApiTypes.STR,
                    location=OpenApiParameter.COOKIE,
                    required=True,
                    description='Ensure session id is in cookie!'
                )

        ],
    request=PasswordSerialzier,
    responses={
                200: Ok200serializer,
                401: Error401Serializer,
                403 :Error403CSRFTokenmissingSerialzier,
                500 :Error500Serializer
               },
     examples=[
                    OpenApiExample(
                        'Send email success!',
                        value={'message':'Change password success','detail':'Please use new password login again!','redirect':'/user/login/'},
                        response_only=True,
                        status_codes=['200']
                    ),
                     OpenApiExample(
                        'not authenticated',
                        value={'error':'User is not authenticated!','detal':'Please login','redirect':'/user/login'},
                        response_only=True,
                        status_codes=['401']
                    ),
                    OpenApiExample(
                        "Request forbbiden",
                        value={'error': 'CSRF token missing or incorrect.'},
                        response_only=True,
                        status_codes=['403']
                    ),
                    OpenApiExample(
                        'Internal error',
                        value={'message': 'Internal error message!'},
                        response_only=True,
                        status_codes=['500']
                    ),],
         description='Change user password, please check password and recheck password is the same.Post password with hash to this api.'
)
    @method_decorator(ensure_csrf_cookie, name='dispatch')
    def post(self, request):
        try:
            if request.user.is_authenticated == False:
                return Response({'error':'User is not authenticated!','detal':'Please login','redirect':'/user/login'}, status=status.HTTP_401_UNAUTORIZED)
            password = request.data.get('new_password')
            user = request.user
            user.set_password(password)
            user.save()
            return Response({'message':'Change password success','detail':'Please use new password login again!','redirect':'/user/login/'}, status=status.HTTP_200_OK)

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
            description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken!'
          )
    ],
    request=EmailSerializer,
    responses={
                200: Ok200serializer,
                403 :Error403CSRFTokenmissingSerialzier,
                400: Error400Serializer
               },
               examples=[
                    OpenApiExample(
                        'Send email success!',
                        value={'message': 'Link is sending to your mail!', 'detail': 'please reset password in 15 min!','token':'token'},
                        response_only=True,
                        status_codes=['200']
                    ),
                     OpenApiExample(
                        'getToken success',
                        value={'message': 'Email is not existed!,please try again!'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        "Request forbbiden",
                        value={'error': 'CSRF token missing or incorrect.'},
                        response_only=True,
                        status_codes=['403']
                    ),
                    OpenApiExample(
                        'getToken success',
                        value={'message': 'Internal error message!'},
                        response_only=True,
                        status_codes=['500']
                    ),]
                )
@method_decorator(ensure_csrf_cookie, name='dispatch')
class EmailVertificationView(APIView):
    """(Anonymous user)Forget password first step, check email is existed then send email with reset password link!"""
    def post(self, request):
        """Check the email and send vertifi-code!"""
        try:
            email = request.data.get('email')
            if get_user_model().objects.filter(email=email).exists():
                current_time = int(datetime.now().timestamp())
                payload = {
                    "email": email,
                    "exp" : current_time + (15 * 60),
                    "usuage": 'reset_password'
                }
                token = create_jwt(**payload)
                link = f"http://cookNetwork/reset-password?code={token}"
                content = {
                    "subject": "Your link for change password",
                    "message":f"Reset password link:{link}\nWarning : If you haven't sing up an accoutn at cookNetwork, please don't click th link!!!"
                    }
                sending_mail.apply_async(args=(email,), kwargs=content, countdown=0)
                cache.set(f'Rest_password_{email}', email, 9000)
                return Response({"message":'Link is sending to your mail!','detail':'please reset password in 15 min!','token':f'{token}'}, status=status.HTTP_200_OK)
            return Response({"error":'Email is not existed!,please try again'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as val_err:
            print(val_err)
            return Response({'error':f'{val_err}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    parameters=[
            OpenApiParameter(
            name='X-CSRFToken',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=True,
            description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken!'
          )
    ],
    request=PasswordSerialzier,
    responses={
                200: Ok200serializer,
                401: Error401Serializer,
                403 :Error403CSRFTokenmissingSerialzier,
                500 :Error500Serializer
               },
     examples=[
                    OpenApiExample(
                        'Send email success!',
                        value={'message': 'Vertify code is sending to your mail!', 'detail': 'please reset password in 15 min!'},
                        response_only=True,
                        status_codes=['200']
                    ),
                     OpenApiExample(
                        'getToken success',
                        value={'message': 'Email is not existed!,please try again!'},
                        response_only=True,
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        "Request forbbiden",
                        value={'error': 'CSRF token missing or incorrect.'},
                        response_only=True,
                        status_codes=['403']
                    ),
                    OpenApiExample(
                        'getToken success',
                        value={'message': 'Internal error message!'},
                        response_only=True,
                        status_codes=['500']
                    ),],
                    description='Forget password , the url must be like reset-password?code="token from /foreget-password/"'

)
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResetPasswordView(APIView):
    """(Anonymous user)check token is correct or not ,if correct then user can reset password! """

    def post(self, request):
        token = request.query_params.get('code')
        try:
            content = decode_jwt(token)
            if content.get('usuage') != 'reset_password':
                return Response({'error':'Wrong token with usuage '}, status=status.HTTP_401_UNAUTHORIZED)
            email = content.get('email')
            if cache.get(f'Rest_password_{email}') == None:
                return Response({'error':'Wrong token with email !'}, status=status.HTTP_401_UNAUTHORIZED)
            user = get_user_model().objects.filter(email=email).first()
            if not user:
                return Response({'error':'Wrong token with user!'}, status=status.HTTP_401_UNAUTHORIZED)
            password = request.data.get('password')
            user.set_password(password)
            user.save()
            cache.delete(f'Rest_password_{email}')
            return Response({'message':'Reset password success','detal':'Use new password login again!','redirect':'/user/login/'}, status=status.HTTP_200_OK)
        except ExpiredSignatureError:
            return Response(
                {'error': 'Token is expired.', 'detail': 'Please sign up again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
                print(e)
                return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def time_now(request):
    time_now = datetime.now()
    return Response({"time_now":f"{time_now}"}, status=status.HTTP_200_OK)



@extend_schema(
    parameters=[
            OpenApiParameter(
                name='X-CSRFToken',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken!'
                ),
    ],
    responses={
        201: Created201serializer,
        400: Error400Serializer,
        403: 'CSRF token missing or incorrect.',
        500: Error500Serializer,
    },
    examples=[
        OpenApiExample(
        'User created!',
        value={'message': 'Email is resend, please check your email to active your account in 15 minutes !', 'token': 'Token that sendiing to email of user'},
        response_only=True,
        status_codes=['200']
        ),
    OpenApiExample(
        'Email  Error',
        value={'error': 'Email is requured!!!', 'detail': 'Please provide an email .'},
        response_only=True,
        status_codes=['400']
    ),
    OpenApiExample(
        "Request forbbiden",
        value={'error': 'CSRF token missing or incorrect.'},
        response_only=True,
        status_codes=['403']
    ),
    OpenApiExample(
        'Internal Error',
        value={'error': 'Internal server error'},
        response_only=True,
        status_codes=['500']
    )
    ],
    description='Create a new user',)
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResendVertifyEmail(APIView):
    """Resend vertify email to user!"""
    def post(self, request):
        email = request.data.get("email")
        if not email :
            return Response({"error":"Email is requured!!",'detail': 'Please provide an email .'} ,status=status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.filter(email=email).first()
        if not user:
            return Response({"error":"Emaill is not be register, please sign up again!!"} ,status=status.HTTP_400_BAD_REQUEST)
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
                "message":f"Click the link to activate your account at cooNetwork!!\n{link}\nWarning : If you haven't sing up an accoutn at cookNetwork, please don't click the link!!!"
                }
        sending_mail.apply_async(args=(email,), kwargs=content, countdown=0)
        return Response({'message':'Email is resend, please check your email to active your account in 15 minutes !','token': f'{token}'}, status=status.HTTP_200_OK)
@method_decorator(csrf_protect, name='dispatch')
@extend_schema_view(
    list=extend_schema(
        parameters=[
           OpenApiParameter(
                name='Session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Ensure session id is in cookie!'
                ),
        ],
        responses={
            201: Created201serializer,
            400: Error400Serializer,
            401: Error401Serializer,
            403: Error403CSRFTokenmissingSerialzier,
            500: Error500Serializer,
        },
        examples=[
            OpenApiExample(
                'Get the follow list!',
                value={'message': 'Get the follow list !'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Request data is invalid!',
                value={'error': 'Request data is invalid!'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'User not login',
                value={'error': 'Authentication credentials were not provided.'},
                response_only=True,
                status_codes=['401']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={'error': 'CSRF token missing or incorrect.'},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                'Internal Error',
                value={'error': 'Internal server error'},
                response_only=True,
                status_codes=['500']
            )
        ],
        ),
    create=extend_schema(
        parameters=[
            OpenApiParameter(
            name='X-CSRFToken',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            required=True,
            description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken!'
            ),
           OpenApiParameter(
                name='Session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Ensure session id is in cookie!'
                ),
        ],
        responses={
            201: Created201serializer,
            400: Error400Serializer,
            401: Error401Serializer,
            403: Error403CSRFTokenmissingSerialzier,
            500: Error500Serializer,
        },
        examples=[
            OpenApiExample(
                'Unfollow the user!',
                value={'message': 'Unfollow the user!'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Follow the user!',
                value={'message': 'Follow the user!'},
                response_only=True,
                status_codes=['201']
            ),
            OpenApiExample(
                'Request data is invalid!',
                value={'error': 'Request data is invalid!'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'User not login',
                value={'error': 'Authentication credentials were not provided.'},
                response_only=True,
                status_codes=['401']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={'error': 'CSRF token missing or incorrect.'},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                'Internal Error',
                value={'error': 'Internal server error'},
                response_only=True,
                status_codes=['500']
            )
        ],
        description='Follow or un follow user!')
)
class FollowViewSet(
                    mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    viewsets.GenericViewSet
                    ):
    """Follow and un follow views for follow action!"""
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return UserFollowing.objects.filter(user_id=user).order_by('create')

    def list(self, request, *args, **kwargs):
        """End point for user follow system  to show login user follow status!!!"""
        try:
            res = super().list(request, *args, **kwargs)
            return res
        except ValidationError as e:
            return Response({'error':'Request data is invalid!'}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(({'error':'Internal server error!'}, status.HTTP_500_INTERNAL_SERVER_ERROR))

    def create(self, request, *args, **kwargs):
        """End point for user follow system!!"""
        try:
            user = request.user
            following_user_id = request.data.get('following_user_id')
            following = get_user_model().objects.get(id = following_user_id)
            follow , created= UserFollowing.objects.get_or_create(
                                                user_id=user,
                                                following_user_id=following
                                                )
            if created:
                return Response({'message':'Follow the user!'}, status.HTTP_201_CREATED)
            elif follow:
                follow.delete()
                return Response({'message':'Unfollow the user!'}, status.HTTP_200_OK)


        except ValidationError as e:
            return Response({'error':'Request data is invalid!'}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(({'error':'Internal server error!'}, status.HTTP_500_INTERNAL_SERVER_ERROR))

@extend_schema(
    responses={200: Ok200serializer,
               400: Error400Serializer,
               500: Error500Serializer
               },
    methods=['GET'],
    examples=[
            OpenApiExample(
                'Get google oauth rul!',
                value={'message': 'Goole oauth url:{}!'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Request data is invalid!',
                value={'error': 'User already login!'},
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
    summary='Retrieve Google Login URL',
    description='Provides a URL for Google OAuth2 login.',
)
@api_view(['GET'])
def google_login(request):
    #Allow use choice googel to login!
    try:
        if request.user.is_authenticated:
            return Response({'error':'User already login!'},status.HTTP_400_BAD_REQUEST)
        else:
            # Define the basic google oauth url and params
            google_oauth2_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
            google_oauth2_params = {
                'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'redirect_uri': settings.GOOGLE_OAUTH2_REDIRECT_URI,  # The redirect url you define in google cloud console
                'scope': 'openid email profile',
                'response_type': 'code',
                'access_type': 'offline',
                'prompt': 'consent',
            }
            full_url = f"{google_oauth2_base_url}?{urlencode(google_oauth2_params)}"
            return Response({'message':f'Goole oauth url:{full_url}'}, status.HTTP_200_OK)
    except Exception as e:
            print(e)
            return Response(({'error':'Internal server error!'}, status.HTTP_500_INTERNAL_SERVER_ERROR))