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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
        extend_schema,
        OpenApiExample,
        extend_schema_view,
        OpenApiParameter,
        OpenApiTypes
)
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db.models import Q, F, Prefetch, Count, Avg
from django.shortcuts import get_object_or_404
from functools import reduce
from operator import or_

from core import models
from core import permissions as Customize_permission
from recipe import serializers
from .utils import UnsafeMethodCSRFMixin, saved_action, CustomPagination
from .redis_set import RedisHandler
from rest_framework.exceptions import ValidationError
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
                "Ingredients",
                OpenApiTypes.STR,
                description="Comma seprated list of ingredient name to filter.",
            ),
        ],
        responses={
            200:serializers.RecipeSerialzier(many=True),
            400:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
            ]
        ),
    create=extend_schema(
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
        responses= {
            201:serializers.RecipeSQLDetailSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    ),
    retrieve=extend_schema(
        responses={
            200:serializers.RecipeSQLDetailSerializer,
            400:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    ),
    update=extend_schema(
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
        responses={
            201:serializers.RecipeSQLDetailSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    ),
    partial_update=extend_schema(
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
        responses={
            201:serializers.RecipeSQLDetailSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    ),
    destroy=extend_schema(
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
        responses={
            204:serializers.ResponseSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "destroy recipe successed.",
                value="No_content,Redirect to list page",
                response_only=True,
                status_codes=['204']
            ),
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    )
)
class RecipeViewSet(UnsafeMethodCSRFMixin, viewsets.ModelViewSet):
    """Views for manage recipe APIs."""
    serializer_class = serializers.RecipeSQLDetailSerializer
    queryset = models.Recipe.objects.all().order_by("create_time")
    permission_classes = [permissions.IsAuthenticated]
    filter_backend = [filters.OrderingFilter]
    ordering_fields = ['create_time', 'name']
    ordering = ['create_time']
    recipe_redis_handler = RedisHandler(redis_client1)

    def get_permissions(self):
        if self.action in ['list','retrieve']:
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
        queryset = self.queryset.annotate(
        comment_count=Count('recipe_comment'),
        average_rating=Avg('recipe_comment__rating')
        )
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

    def to_representation(self, instance):
        """Transform to leagal format"""
        ret = super().to_representation(instance)
        # tranform datetime
        if 'create_time' in ret:
            ret['create_time'] = ret['create_time'].isoformat()
        if 'recipe_comment' in ret:
            for comment in ret['recipe_comment']:
                if 'crated_time' in comment:
                    comment['crated_time'] = comment['crated_time'].isoformat()
        return ret

    def list(self, request, *args, **kwargs):
        """list of recipe!"""
        self.pagination_class = CustomPagination
        response = super().list(request, *args, **kwargs)
        try:
            search_tags = request.query_params.get('tags')
            search_ingredients = request.query_params.get('ingredients')
            search_user = request.query_params.get('user')

            if search_tags:
                tags = search_tags.split(",")
                models.Tag.objects.filter(name__in=tags).update(views=F('views') + 1)

            if search_ingredients:
                ingredients = search_ingredients.split(",")
                models.Ingredient.objects.filter(name__in=ingredients).update(views=F('views') + 1)
            return response
        except ValidationError as e:
            return Response({'error':f'{e}',"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
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
                self.recipe_redis_handler.increase_recipe_view(hkey_name="views",recipe_id=recipe_id)
                cache_data["views"] = cache_data.get("views", 0) + 1
                self.recipe_redis_handler.set_recipe(recipe_id=recipe_id, data=cache_data)
                return Response({'recipe': cache_data}, status.HTTP_200_OK)
            # If data is not in Redis, fetch it from SQL
            recipe_instance = self.queryset.get(id=recipe_id)
            average_rating_result = recipe_instance.recipe_comment.aggregate(average_rating=Avg('rating'))
            comment_count_result = recipe_instance.recipe_comment.aggregate(comment_count=Count('id'))
            average_rating = average_rating_result.get("average_rating")
            comment_count = comment_count_result.get("comment_count")
            setattr(recipe_instance, 'average_rating', average_rating)
            setattr(recipe_instance, 'comment_count', comment_count)
            recipe = serializers.RecipeSQLDetailSerializer(recipe_instance)
            self.recipe_redis_handler.set_recipe(recipe_id=recipe_id, data=recipe.data)
            self.recipe_redis_handler.increase_recipe_view(hkey_name="views",recipe_id=(recipe_id))
            return Response({'recipe':recipe.data}, status.HTTP_200_OK)
        except ValidationError as e :
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_INTERNAL_SERVER_ERROR)
        except Exception as e :
            return Response({'error':f'{e}',"detail":"Please check again!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        except ValidationError as e :
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"error":e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        """Update recipe and change recipe cache in redis.(partial)"""
        response = super().partial_update(self, request, *args, **kwargs)
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
        except ValidationError as e :
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"error":e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def destroy(self, request, *args, **kwargs):
        """Destroy the recipe instance and clear data in Redis cache."""
        try:
            instance = self.get_object()
            recipe_id = instance.id
            super().destroy(self, request, *args, **kwargs)
            self.recipe_redis_handler.del_hkey(hkey_name="views", recipe_id=recipe_id)
            self.recipe_redis_handler.del_hkey(hkey_name="likes", recipe_id=recipe_id)
            self.recipe_redis_handler.del_hkey(hkey_name="save_count", recipe_id=recipe_id)
            self.recipe_redis_handler.del_prev_hkey(hkey_name="views", recipe_id=recipe_id)
            self.recipe_redis_handler.del_prev_hkey(hkey_name="likes", recipe_id=recipe_id)
            self.recipe_redis_handler.del_prev_hkey(hkey_name="save_count", recipe_id=recipe_id)
            return Response("No_content,Redirect to list page", status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e :
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"error":e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_protect, name='dispatch')
@extend_schema_view(
    create=extend_schema(
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
            ),
        ],
        request=serializers.RecipeCommentSerializer,
        responses={
            201:serializers.RecipeCommentSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    ),
    destroy=extend_schema(
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
                ),
        ],
        responses={
            204:serializers.ResponseSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "No content",
                value={"message":"None content",},
                response_only=True,
                status_codes=['204']
            ),
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            ),
        ]
    ),
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                required=True,
                description='Ensure session id is in cookie!'
                ),
            OpenApiParameter(
                name='recipe_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='The recipe_id that need to comment'
                ),
        ],
        responses={
            200:serializers.RecipeCommentSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            )
        ],
    ),
    update=extend_schema(
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                required=True,
                description='Ensure session id is in cookie!'
                ),
            OpenApiParameter(
                name='X-CSRFToken',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken'
                ),
        ],
        responses={
            200:serializers.RecipeCommentSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            )
        ]
    ),
    partial_update=extend_schema(
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                required=True,
                description='Ensure session id is in cookie!'
                ),
            OpenApiParameter(
                name='X-CSRFToken',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='CSRF token for request, need to get from cookies and set in header as X-CSRFToken'
                ),
        ],
        responses={
            200:serializers.RecipeCommentSerializer,
            400:serializers.ResponseSerializer,
            403:serializers.ResponseSerializer,
            500:serializers.ResponseSerializer
        },
        examples=[
            OpenApiExample(
                "Bad request",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Request forbbiden",
                value={"detail":"Authentication credentials were not provided."},
                response_only=True,
                status_codes=['403']
            ),
            OpenApiExample(
                "Interval server error!",
                value={"error":"error","detail":"please check again!"},
                response_only=True,
                status_codes=['500']
            )
        ]
    )
)
class RecipeCommentViewSet(
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.UpdateModelMixin,
                        viewsets.GenericViewSet
                        ):
    """Viewset for recipe comment!"""
    serializer_class = serializers.RecipeCommentSerializer
    queryset = models.RecipeComment.objects.all().order_by("-created_time")
    permission_classes = [permissions.IsAuthenticated]
    recipe_redis_handler = RedisHandler(redis_client1)

    def get_permissions(self):
        if self.action in ['list']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [Customize_permission.IsAdminOrRecipeOwmer]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        """List recipecommet filter by recipe id."""
        try:
            recipe_id = request.query_params.get('recipe_id')
            if recipe_id is not None:
                self.queryset = self.queryset.prefetch_related(
                        Prefetch('recipe_comment', queryset=models.RecipeComment.objects.filter(recipe=recipe_id))
                    )
            return super().list(request, *args, **kwargs)
        except ValidationError as e:
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error':f'{e}  '}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """Base create method and update the recipe with new comment in cache!"""
        try:
            serializer = self.get_serializer(data=request.data)
            print(serializer)
            response = super().create(request, *args, **kwargs)
            print(response)
            self.recipe_redis_handler.update_recipe_in_cache(recipe_id=response.data.get("recipe"))
            print(5)
            return response
        except ValidationError as e:
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error':f'{e} '}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Base destroy method and update the recipe with new comment in cache!"""
        try:
            instance = self.get_object()
            recipe_id = instance.recipe.id
            self.perform_destroy(instance)
            self.recipe_redis_handler.update_recipe_in_cache(recipe_id=recipe_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error':f'{e}  '}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_update(self, serializer):
        """Base on UpdateModelMixin and update the recipe with new comment in cache! """
        super().perform_update(serializer)
        instance = serializer.instance
        # Ensure that the recipe instance exists before trying to access its id
        if hasattr(instance, 'recipe') and instance.recipe:
            recipe_id = instance.recipe.id
            self.recipe_redis_handler.update_recipe_in_cache(recipe_id=recipe_id)
        else:
            # Handle the case where recipe is None, if necessary
            pass

    def update(self, request, *args, **kwargs):
        """Add new response to cache error"""
        try:
            response = super().update(request, *args, **kwargs)
            return response
        except ValidationError as e:
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error':f'{e}  '}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        200:serializers.ResponseSerializer,
        400:serializers.ResponseSerializer,
        403:serializers.ResponseSerializer,
        404:serializers.ResponseSerializer,
        500:serializers.ResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Successed',
            value={'message': 'Like action successed!', 'detail': ""},
            response_only=True,
            status_codes=['200']
        ),
        OpenApiExample(
            'Successed',
            value={'message': 'Like action was revoke!', 'detail': ""},
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
    description="The user could like or revoke like from recipe!"
)
@api_view(['POST'])
@csrf_protect
@permission_classes([IsAuthenticated])
def like_button(request):
    """Action that user like the recipe!"""
    recipe_id = request.data.get("id")
    recipe_redis_handler = RedisHandler(redis_client1)
    try:
        recipe = models.Recipe.objects.filter(id=recipe_id).first()
        if not recipe:
            return Response({"error":"There is no recipe with this id"}, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        like,created = models.Like.objects.get_or_create(user=user ,recipe=recipe)
        if created:
            recipe.likes=F('likes') + 1
            recipe.save(update_fields=['likes'])
            recipe.refresh_from_db()
            recipe_redis_handler.increase_recipe_view(hkey_name="likes", recipe_id=recipe_id)
            print(recipe.likes)
            return Response({"message":"Like action successed!"}, status=status.HTTP_200_OK)
        else:
            like.delete()
            recipe.likes=F('likes') - 1
            recipe.save(update_fields=['likes'])
            recipe_redis_handler.increase_recipe_view(hkey_name="likes", recipe_id=recipe_id, increment_value=-1)
            recipe.refresh_from_db()
            print(recipe.likes)
            return Response({"message":"Like action was revoke!"}, status=status.HTTP_200_OK)

    except ValidationError as e :
            return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e :
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
        OpenApiParameter(
                name='Session_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                required=True,
                description='Ensure session id is in cookie!'
        ),
    ],
    request=serializers.SaveActionSerializer,
    responses={
        200:serializers.ResponseSerializer,
        400:serializers.ResponseSerializer,
        403:serializers.ResponseSerializer,
        404:serializers.ResponseSerializer,
        500:serializers.ResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Successed',
            value={'message': 'Save action successed!'},
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
            "Value or field error",
            value={'error': 'Check recipe_id , tag or ingredient at least in is in request!!'},
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
def save_button(request):
    """The function for save recipe or not !"""
    try:
        recipe = models.Recipe.objects.filter(id=request.data.get('recipe_id')).first()
        print(recipe)
        tag = models.Tag.objects.filter(name=request.data.get('tag')).first()
        ingredient = models.Ingredient.objects.filter(name=request.data.get('ingredient')).first()
        if not recipe and not tag and not ingredient:
            return Response({"error":"Check recipe_id , tag or ingredient at least in is in request!!"}, status=status.HTTP_404_NOT_FOUND)
        #save_action is import form .utils
        if recipe:
            return saved_action(user=request.user, obj=recipe)
        elif tag:
            return saved_action(user=request.user, obj=tag)
        elif ingredient:
            return saved_action(user=request.user, obj=ingredient)
        return Response({'error': 'No valid object found'}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e :
        return Response({'error': str(e),"detail":"Please check again!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e :
        return Response({'error':f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




