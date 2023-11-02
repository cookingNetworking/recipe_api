"""Some settings about redis!"""

import django_redis
import random
redis_client1 = django_redis.get_redis_connection("default")

class RedisHandler:
    """
    Class for redis setting
    ex:
    recipe_handler = RedisHandler('recipe')
    recipe_handler.set_recipe(recipe_id=1, data=data)

    recipe_view_set_handler = RedisHandler('recipe_view')
    recipe_view_set_handler.set_hkey(recipe_id=1,initinal_value=0)
    """

    def __init__(self, hkey_name: str):
        """
        Initialize the RedisHandler

        :param hkey_name: The name of the hash key or key. Must be a string.
        """
        self.hkey_name = hkey_name
        self.redis_client = redis_client1

    def set_recipe(self,recipe_id: int, data: dict):
        """Cache recipe in redis."""
        timeout = random.randint(1500, 1800)
        self.redis_client.set(f'{self.hkey_name}_{recipe_id}',data, timeout=timeout)

    def get_recipe(self, recipe_id: int):
        """Get recipe in redis."""
        data = self.redis_client.get(f'Recipe_{recipe_id}')
        if data:
            return data.decode('utf-8')
        return None

    def delete_recipe_in_cache(self, recipe_id: int):
        """Delete recipe in redis!"""
        self.redis_client.delete(f'Recipe_{recipe_id}')

    def set_hkey(self, recipe_id: int, initinal_value=0):
        """Set hkey data type in cache(redis)."""
        self.redis_client.hset(f"{self.hkey_name}", f"{recipe_id}", initinal_value)

    def get_hkey(self, recipe_id: int):
        """Get views value of giving recipe id."""
        recipe_view = self.redis_client.hget(f'{self.hkey_name}', f"{recipe_id}")
        if recipe_view:
            return int(recipe_view)
        return None
    def increase_recipe_view(self, recipe_id: int, increment_value=1):
        """Increase value for hkey value"""
        self.redis_client.hincrby(f'{self.hkey_name}', f"{recipe_id}", increment_value)



