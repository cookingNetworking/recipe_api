"""
Serialzier for User model.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["email","password","username","is_active","is_staff","role"]
        extra_kwargs = {"password":{'write_only':True, "min_length" : 8}}

    def create(self, validated_data):
        """Create user and return user with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)
    


class Error400Serializer(serializers.Serializer):
    error = serializers.CharField()
    detail = serializers.CharField()

class Error500Serializer(serializers.Serializer):
    error = serializers.CharField()    