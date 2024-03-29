"""
Celery task for recipe!
"""


from celery import shared_task
from celery import Celery
from django.db.models import Avg, Count

from django.contrib.auth import get_user_model
from .serializers import RecipeSQLDetailSerializer
from core.models import Recipe, Notification
from .redis_set import RedisHandler
import django_redis

celery_app = Celery('app', backend='redis://cache:6379/1' ,broker='redis://cache:6379/1')
redis_client1 = django_redis.get_redis_connection("default")

@shared_task
def update_recipe_views_in_redis():
    top_recipes = Recipe.objects.annotate(
        average_rating=Avg('recipe_comment__rating'),
        comment_count=Count('recipe_comment')
    ).order_by('-views')[:100].prefetch_related('photos', 'steps', 'recipe_comment')

    serializer_recipes = RecipeSQLDetailSerializer(top_recipes, many=True).data
    recipe_redis_handler = RedisHandler(redis_client1)

    for data in serializer_recipes:
        recipe_redis_handler.set_recipe(recipe_id=data['id'], data=data)

def update_recipe(hkey: str, recipe_hash , previous_hash):
    """The function to distinguish which recipe id need to update."""
    update_recipe = {}
    for k ,v in recipe_hash.items():
        previous_value = previous_hash.get(k)
        if previous_value is not None and v != previous_value:
            update_recipe[k] = v
            redis_client1.hset(f"Prev_{hkey}",f"{k}", v)
        elif previous_value is None:
            update_recipe[k] = v
            redis_client1.hset(f"Prev_{hkey}",f"{k}",v)
        elif previous_value is not None and v == previous_value:
            pass
    return update_recipe


@shared_task
def set_up_for_server_start():
    """Create hash and prev hash in the begain of server start."""
    recipe_redis_handler = RedisHandler(redis_client1)
    recipes = Recipe.objects.values("id", "views", "likes", "save_count")
    try:
        for recipe in recipes:
            recipe_redis_handler.set_hkey(hkey_name="views", recipe_id=int(recipe["id"]), initinal_value=recipe["views"])
            recipe_redis_handler.set_hkey(hkey_name="likes", recipe_id=int(recipe["id"]), initinal_value=recipe["likes"])
            recipe_redis_handler.set_hkey(hkey_name="save_count", recipe_id=int(recipe["id"]), initinal_value=recipe["save_count"])
    except Exception as e:
        print(e)

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

@shared_task
def create_notification(user_ids, message):
    """Create notification instance for user."""
    try:
        users = get_user_model().objects.filter(id__in=user_ids)
        for user in users:
            Notification.objects.create(
                client=user,
                title='Follow create recipe!',
                message=message,
                delievered=True
            )
    except Exception as e:
        print(e)