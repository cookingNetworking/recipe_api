"""
Serialzier for User model.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from core.models import UserFollowing

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id","email","password","username","role","birthday","is_staff","last_login"]
        extra_kwargs = {"id":{'read_only':True},
                        "password":{'write_only':True, "min_length" : 8,'required': True},
                        'last_login':{'read_only':True},
                        "is_staff": {'read_only': True},
                        "email": {'required': True},
                        "username": {'required': True}
                        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' in self.context and self.context['request'].method in ['GET','PUT','PATCH']:
            self.fields.pop('password', None)


    def create(self, validated_data):
        """Create user and return user with encrypted password"""
        validated_data.pop('last_login', None)
        validated_data.pop('is_staff', None)
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Upadte and return user."""
        validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        return user

class UserDetailResponseSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ["email", "username", "role","birthday", "is_staff", "last_login"]


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
        attrs['user'] = user
        return attrs

class FollowSerializer(serializers.ModelSerializer):
    """Serializer of  follow action!"""
    class Meta:
        model = UserFollowing
        fields = ["user_id","following_user_id","create"]
        extra_kwargs = {
                    "user_id":{"read_only": True},
                    "following_user_id":{"required": True},
                    "create": {"read_only": True},
                    }



class PasswordSerialzier(serializers.Serializer):
    new_password = serializers.CharField(required=True)

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class Ok200serializer(serializers.Serializer):
    message = serializers.CharField()
    detail = serializers.CharField(allow_null=True)
    reidrect = serializers.CharField(allow_null=True)
    token = serializers.CharField(allow_null=True)

class Created201serializer(serializers.Serializer):
    message = serializers.CharField()
    token = serializers.CharField(allow_null=True)

class Error401Serializer(serializers.Serializer):
    error = serializers.CharField()
    detail = serializers.CharField(allow_null=True)

class Error400Serializer(serializers.Serializer):
    error = serializers.CharField()
    detail = serializers.CharField(allow_null=True)

class Error500Serializer(serializers.Serializer):
    error = serializers.CharField()

class SignUpSerializer(serializers.Serializer):
    token = serializers.CharField()

class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

class CheckEmailResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    detail = serializers.CharField(allow_null=True)

class CheckUsernameResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    detail = serializers.CharField(allow_null=True)

class Error403CSRFTokenmissingSerialzier(serializers.Serializer):
    error = serializers.CharField()
