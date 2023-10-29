"""Some settings about redis!"""

import django_redis

redis_client1 = django_redis.get_redis_connection("default")

def set_recipe_view_hkey(recipe_id):
    """Set hkey data type in cache(redis)."""
    redis_client1.hset("recipe_view", f"{recipe_id}", 0)

def get_recipe_view_hkey(recipe_id):
    """Get views value of giving recipe id.""" 
    recipe_view = redis_client1.hget('recipe_view', f"{recipe_id}")
    return recipe_view

def increase_recipe_view(recipe_id):
    redis_client1.hincrby('recipe_view', f"{recipe_id}")
    