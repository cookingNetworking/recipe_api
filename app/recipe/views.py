"""Create recipe API end point!"""

from rest_framework import (
        status,
        generics,
        mixins,
        permissions,
        viewsets,
        filters
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
from django.db.models import Q

from functools import reduce
from operator import or_

from core import models
from core import permissions as Customize_permission
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
    filter_backend = [filters.OrderingFilter]
    ordering_fields = ['create_time', 'name']
    ordering = ['create_time']

    def get_permissions(self):
        if self.action in ['list']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [Customize_permission.IsAdminOrRecipeOwmer]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


    def get_serializer_class(self):
        """Return serializer class for request!"""
        if self.action == 'list':
            return serializers.RecipeSerialzier
        return self.serializer_class

    def get_queryset(self):
        """Retrun query for filter!"""
        queryset = self.queryset
        search_ingertients = self.request.query_params.get('ingredients')
        search_tags = self.request.query_params.get('tags')
        search_user = self.request.query_params.get('user')

        reqeust_filters = Q()

        if search_ingertients :
            ingredient_list = search_ingertients.split(",")
            ingredient_queries = [Q(ingredients__name__icontains=ingredient) for ingredient in ingredient_list]
            reqeust_filters |= reduce(or_, ingredient_queries)
        if search_tags:
            tag_list = search_tags.split(",")
            tag_queries = [Q(tags__name__icontains=tag) for tag in tag_list]
            reqeust_filters |= reduce(or_, tag_queries)

        if search_user:
            user_list = search_user.split(",")
            user_queries = [Q(user__username__icontains=user) for user in user_list]
            reqeust_filters |= reduce(or_, user_queries)

        return queryset.filter(reqeust_filters).distinct()

class BaseRecipeAttrViewSet(
                            mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base view set for recipe attributes."""

    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ['destroy','update']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = self.queryset
        return queryset.all().order_by("-views").distinct()

class TagViewSet(BaseRecipeAttrViewSet):
    """Views of tag API include list update destroy!"""
    serializer_class = serializers.TagSerialzier
    queryset = models.Tag.objects.all()

class IngredientViewSet(BaseRecipeAttrViewSet):
    """"Views of tag API include list update destroy!"""
    serializer_class = serializers.IngredientSerialzier
    queryset= models.Ingredient.objects.all()


