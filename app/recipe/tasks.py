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

def update_recipe(hkey: str, recipe_hash: dict, previous_hash: dict):
    """The function to distinguish which recipe id need to update."""
    update_recipe = {}
    recipe_redis_handler = RedisHandler(redis_client1)
    for k ,v in recipe_hash.items():
        previous_value = previous_hash.get("k")
        if previous_value is not None and v != previous_value:
            update_recipe[k] = v
        elif previous_value is None:
            recipe_redis_handler.del_hkey(hkey_name=hkey, recipe_id=int(k))

    return update_recipe


@shared_task
def consist_redis_and_sql_data():
    recipe_redis_handler = RedisHandler(redis_client1)
    recipe_views = recipe_redis_handler.get_hset("views")
    recipe_likes = recipe_redis_handler.get_hset("likes")
    recipe_save_counts = recipe_redis_handler.get_hset("save_count")

    recipe_previos_views = recipe_redis_handler.get_prev_hset("views")
    recipe_previos_likes = recipe_redis_handler.get_prev_hset("likes")
    recipe_previos_save_counts = recipe_redis_handler.get_prev_hset("save_count")

    views_update = update_recipe("views", recipe_views, recipe_previos_views)
    likes_update = update_recipe("likes", recipe_likes, recipe_previos_likes)
    save_counts_update = update_recipe("save_count", recipe_save_counts, recipe_previos_save_counts)
    recipes_to_update =[]
    update_ids = set(views_update)|set(likes_update)|set(save_counts_update)

    for recipe_id in update_ids:
        update_values = {}
        if recipe_id in views_update:
            update_values["views"] = views_update[recipe_id]
        else:
            update_values["views"] = recipe_previos_views[recipe_id]
        if recipe_id in likes_update:
            update_values["likes"] = likes_update[recipe_id]
        else:
            update_values["likes"] = recipe_previos_likes[recipe_id]
        if recipe_id in save_counts_update:
            update_values["save_count"] = save_counts_update[recipe_id]
        else:
            update_values["save_count"] = recipe_previos_save_counts[recipe_id]

        recipe = Recipe(id=recipe_id, **update_values)
        recipes_to_update.append(recipe)

    Recipe.objects.bulk_update(recipes_to_update, ['views', 'likes','save_count'])
