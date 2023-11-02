"""
Celery task for recipe!
"""


from celery import shared_task
from celery import Celery

from .serializers import ReciperSQLDetailSerializer
from core.models import Recipe
from .redis_set import RedisHandler
import django_redis

redis_client1 = django_redis.get_redis_connection("default")

@shared_task
def update_recipe_views_in_redis():
    top_recipes = Recipe.objects.prefetch_related('photos', 'steps').all()

    serializer_recipes = ReciperSQLDetailSerializer(top_recipes, many=True).data
    recipe_redis_handler = RedisHandler(redis_client1)

    for data in serializer_recipes:
        recipe_redis_handler.set_recipe(recipe_id=data['id'], data=data)

@shared_task
def consist_redis_and_sql_data():
    recipe_redis_handler = RedisHandler(redis_client1)
    recipe_views = recipe_redis_handler.get_hset("views")
    recipe_likes = recipe_redis_handler.get_hset("likes")
    recipe_save_counts = recipe_redis_handler.get_hset("save_counts")

    recipe_previos_views =
    recipe_previos_views =
    recipe_previos_views =

    #Get recipe value in redis
    recipe_views = {int(k): int(v) for k, v in recipe_views.items()}
    recipe_likes  = {int(k): int(v) for k, v in recipe_likes.items()}
    recipe_save_counts = {int(k): int(v) for k, v in recipe_save_counts.items()}

    #Get recipe previous value in redis
    recipe_views = {int(k): int(v) for k, v in recipe_views.items()}
    recipe_likes  = {int(k): int(v) for k, v in recipe_likes.items()}
    recipe_save_counts = {int(k): int(v) for k, v in recipe_save_counts.items()}
