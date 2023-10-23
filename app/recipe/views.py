"""Create recipe API end point!"""

from rest_framework import (
        status,
        generics,
        permissions,
        viewsets,
        authentication
)
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
        extend_schema,
        OpenApiExample,
        extend_schema_view,
        OpenApiParameter,
        OpenApiTypes
)
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator

from core import models
from recipe import serializers
from .utils import UnsafeMethodCSRFMixin
@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma separated list of name to filter.",
            ),
            OpenApiParameter(
                "Ingreduents",
                OpenApiTypes.STR,
                description="Comma seprated list of ingredient name to filter.",
            ),
        ]
    )
)
@method_decorator(csrf_protect, name='dispatch')
class RecipeViewSet(UnsafeMethodCSRFMixin, viewsets.ModelViewSet):
    """Views for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = models.Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list','retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


    def get_serializer_classes(self):
        """Return serializer class for request!"""
        if self.action == 'list':
            return serializers.RecipeSerialzier
        return self.serializer_class

    def get_queryset(self):
        """Retrieve recipes for specific recipe."""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_names = tags.split(',')
            queryset = queryset.filter(tags__name__in=tag_names)
        if ingredients:
            ingredients_names = ingredients.split(',')
            queryset = queryset.filter(ingredients__name__in=ingredients_names)
        return queryset.distinct()
