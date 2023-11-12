"""Create recipe API end point!"""

from rest_framework import (
        status,
        generics,
        mixins,
        permissions,
        viewsets,
        filters
)

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
        extend_schema,
        OpenApiExample,
        extend_schema_view,
        OpenApiParameter,
        OpenApiTypes
)
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from django.db.models import Q, F

from functools import reduce
from operator import or_

from core import models
from core import permissions as Customize_permission
from recipe import serializers
from .utils import UnsafeMethodCSRFMixin
from .redis_set import RedisHandler
import django_redis

redis_client1 = django_redis.get_redis_connection("default")


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
    serializer_class = serializers.ReciperSQLDetailSerializer
    queryset = models.Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backend = [filters.OrderingFilter]
    ordering_fields = ['create_time', 'name']
    ordering = ['create_time']
    recipe_redis_handler = RedisHandler(redis_client1)

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

    def list(self, request, *args, **kwargs):
        """list of recipe!"""
        response = super().list(request, *args, **kwargs)
        try:
            search_tags = request.query_params.get('tags')
            search_ingredients = request.query_params.get('ingredients')
            search_user = request.query_params.get('user')

            if search_tags:
                tags = search_tags.split(",")
                models.Tag.filter(name__in=tags).update(views=F('views') + 1)

            if search_ingredients:
                ingredients = search_ingredients.split(",")
                models.Ingredinet.filter(name__in=ingredients).update(views=F('views') + 1)
            return response
        except ValidationError as e:
        # Handle validation errors (like email already exists) here
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """Create recipe object."""
        try:
            response = super().create(request, *args, **kwargs)
            # Extract newly create recipe instance from serializer.
            if response.data:
                recipe_id = response.data.get('id', None)
                print(recipe_id, type)
                if recipe_id is not None:
                # Get recipe id of instance.
                    self.recipe_redis_handler.set_recipe(recipe_id=recipe_id,data=response.data)
                    self.recipe_redis_handler.set_hkey(hkey_name='views',recipe_id=int(recipe_id))
                    self.recipe_redis_handler.set_hkey(hkey_name='likes',recipe_id=int(recipe_id))
                    self.recipe_redis_handler.set_hkey(hkey_name='save_count',recipe_id=int(recipe_id))
                    return response
        except ValidationError as e:
        # Handle validation errors (like email already exists) here
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve recipe object detail"""
        try:
            recipe_id = kwargs.get('pk')
            if not recipe_id:
                return Response({"error":"Loss recipe id","detail":"Please provide recipe id!"}, status=status.HTTP_400_BAD_REQUEST)
            cache_data = self.recipe_redis_handler.get_recipe(recipe_id=int(recipe_id))

            if cache_data:
                cache_recipe = serializers.ReciperRedisDetailSerializer(data=cache_data)
                cache_recipe.is_valid(raise_exception=True)
                self.recipe_redis_handler.set_recipe(recipe_id=recipe_id, data=cache_data)
                self.recipe_redis_handler.increase_recipe_view(hkey_name="views",recipe_id=(recipe_id))
                return Response({'recipe': cache_recipe.data}, status.HTTP_200_OK)

            # If data is not in Redis, fetch it from SQL
            recipe_instance = self.queryset.get(id=recipe_id)
            recipe = serializers.ReciperSQLDetailSerializer(recipe_instance)
            self.recipe_redis_handler.set_recipe(recipe_id=recipe_id, data=recipe.data)
            self.recipe_redis_handler.increase_recipe_view(hkey_name="views",recipe_id=(recipe_id))
            return Response({'recipe':recipe.data}, status.HTTP_200_OK)
        except ValidationError as e :
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e :
            return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """Update recipe and change recipe cache in redis."""
        response = super().update(self, request, *args, **kwargs)
        try:
            recipe =  response.data
            if recipe:
                    recipe_id = response.get('id', None)
                    print(recipe_id, type)
                    if recipe_id is not None:
                    # Get recipe id of instance.
                        self.recipe_redis_handler.set_recipe(recipe_id=recipe_id,data=recipe)
                    views_value = int(recipe.get("views"))
                    likes_value = int(recipe.get("likes"))
                    save_count_value = int(recipe.get("save_count"))
                    self.recipe_redis_handler.update_hkey(hkey_name="views",recipe_id=recipe_id, value=views_value)
                    self.recipe_redis_handler.update_hkey(hkey_name="likes",recipe_id=recipe_id, value=likes_value)
                    self.recipe_redis_handler.update_hkey(hkey_name="save_count",recipe_id=recipe_id, value=save_count_value)
                    return response
        except Exception as e:
            print(e)
            return Response({"error":e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Destroy the recipe instance and clear data in Redis cache."""
        response = super().destroy(self, request, *args, **kwargs)
        recipe_id = request.data.get("id")
        self.recipe_redis_handler.del_hkey(hkey_name="views", recipe_id=recipe_id)
        self.recipe_redis_handler.del_hkey(hkey_name="views", recipe_id=recipe_id)
        self.recipe_redis_handler.del_hkey(hkey_name="views", recipe_id=recipe_id)
        return response


class BaseRecipeAttrViewSet(
                            mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base view set for recipe attributes."""

    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ['destroy','update', 'create']:
            permission_classes = [permissions.IsAdminUser]
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
    request=serializers.LikeRecipeAction,
    responses={
    200:serializers.LikeResponseSerializer,
    400:serializers.LikeResponseSerializer,
    403:serializers.LikeResponseSerializer,
    404:serializers.LikeResponseSerializer,
    500:serializers.LikeResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Successed',
            value={'message': 'Like action successed!', 'detail': ""},
            response_only=True,
            status_codes=['200']
        ),
        OpenApiExample(
            "Bad reque st",
            value={'error': 'user already like the recipe!'},
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
            "Value or field error",
            value={'error': 'There is no recipe with this id', 'detail': 'Please login again.'},
            description="Ensure recipe id is send.",
            response_only=True,
            status_codes=['404']
        ),
        OpenApiExample(
            'Internal Error',
            value={'error': 'Internal server error'},
            response_only=True,
            status_codes=['500']
        )
    ],
    )
@api_view(['POST'])
@csrf_protect
@permission_classes([IsAuthenticated])
def like_button(request):
    """Action that user like the recipe!"""
    recipe_id = request.date.get("id")
    try:
        recipe = models.Recipe.filter(id=recipe_id).first()
        if not recipe:
            return Response({"error":"There is no recipe with this id"}, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        like,created = models.Like.objects.get_or_create(user=user ,recipe=recipe)
        if created:
            recipe(likes=F('likes') + 1)
            recipe.save()
            return Response({"message":"Like action successed!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"User already liked the recipe!"}, status=status.HTPP_400_BAD_REQUEST)
    except ValidationError as e :
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e :
        return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

