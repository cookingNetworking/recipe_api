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