"""
Serialzier for User model.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["email","password","username","role","is_staff",'last_login']
        extra_kwargs = {
                        "password":{'write_only':True, "min_length" : 8},
                        'last_login':{'read_only':True},
                        "is_staff": {'read_only': True},
                        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' in self.context and self.context['reuqest'].method in ['GET']:
            self.fields.pop('password', None)

    def create(self, validated_data):
        """Create user and return user with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)
    
    def update(self, validated_data):
        """Upadte and return user."""
        validated_data.pop('password', None)
        user = super().update(isinstance, validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    """Serializer for login !"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type':'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs.get('email'),
            password=attrs.get('password')
            )
        if not user:
            msg = _('Incorrect email or password.')
            raise serializers.ValidationError(msg, code='authorization')

        if not user.is_active:
            msg = _('User is disabled.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs





class Ok200serializer(serializers.Serializer):
    message = serializers.CharField()
    detail = serializers.CharField()

class Created201serializer(serializers.Serializer):
    message = serializers.CharField()
    token = serializers.CharField()

class Error401Serializer(serializers.Serializer):
    error = serializers.CharField()
    detail = serializers.CharField()

class Error400Serializer(serializers.Serializer):
    error = serializers.CharField()
    detail = serializers.CharField()

class Error500Serializer(serializers.Serializer):
    error = serializers.CharField()

class SignUpSerializer(serializers.Serializer):
    token = serializers.CharField()

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

class CheckEmailResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    detail = serializers.CharField()

class CheckUsernameResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    detail = serializers.CharField()