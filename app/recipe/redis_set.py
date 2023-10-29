"""Some settings about redis!"""

import django_redis

reids_client1 = django_redis.get_redis_connection("default")

def set_recipe_view_hkey(recipe_id):
    """Set hkey data type in cache(redis)."""
    reids_client1.hset("recipe_view", f"{recipe_id}", 0)

def get_recipe_view_hkey(recipe_id):
    """Get views value of giving recipe id.""" 
    reids_client1 = reids_client1.hget('recipe_view', f"{recipe_id}")

def increase_recipe_view(recipe_id):
    reids_client1.hincrby('recipe_view', f"{recipe_id}")
    