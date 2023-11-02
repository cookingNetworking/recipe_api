"""Some settings about redis!"""


import random
import json

class RedisHandler:
    """
    Class for redis setting
    ex:
    recipe_handler = RedisHandler('recipe')
    recipe_handler.set_recipe(recipe_id=1, data=data)

    recipe_view_set_handler = RedisHandler('recipe_view')
    recipe_view_set_handler.set_hkey(recipe_id=1,initinal_value=0)
    """

    def __init__(self, redis_client):
        """
        Initialize the RedisHandler

        :param redis_client: The redis connection pool must. Shoud establish at first.
        """
        self.redis_client = redis_client

    def set_recipe(self,recipe_id: int, data):
        """
        Cache recipe in redis.

        :param recipe_id: The ID of the recipe. Must be an integer.
        :param data: The data to be stored. Must be a dict.
        Time of timeout is random set from 25 min to 30 min.
        """
        json_data = json.dumps(data)
        timeout = random.randint(1500, 1800)
        self.redis_client.set(f'Recipe_{recipe_id}',json_data, ex=timeout)

    def get_recipe(self, recipe_id):
        """
        Get recipe in redis.

        :param recipe_id: The ID of the recipe. Must be an integer.
        :return: The data associated with the recipe, if exists.
        """
        data = self.redis_client.get(f'Recipe_{recipe_id}')

        if data:
            try:
                return json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for Recipe_{recipe_id}: {e}")
                return None

    def delete_recipe_in_cache(self, recipe_id):
        """
        Delete recipe in redis!

        :param recipe_id: The ID of the recipe. Must be an integer.
        """
        self.redis_client.delete(f'Recipe_{recipe_id}')

    def set_hkey(self, hkey_name: str, recipe_id: int, initinal_value=0):
        """
        Set hkey data type in cache(redis).

        :param recipe_id: The ID of the recipe. Must be an integer.
        :param initinal_value: The initial value of the recipe staff. Must be an integer.
        """
        self.redis_client.hset(f"Recipe_{hkey_name}", f"{recipe_id}", initinal_value)

    def get_hkey(self, hkey_name: str, recipe_id: int):
        """
        Get views value of giving recipe id.
        :param recipe_id: The ID of the recipe. Must be an integer.
        """
        recipe_view = self.redis_client.hget(f'Recipe_{hkey_name}', f"{recipe_id}")
        if recipe_view:
            return int(recipe_view)
        return None

    def increase_recipe_view(self, hkey_name: str, recipe_id: int, increment_value=1):
        """
        Increase value for hkey value
        :param recipe_id: The ID of the recipe. Must be an integer.
        :param increment_value: The increase value of the recipe staff. Must be an integer.
        """
        self.redis_client.hincrby(f'Recipe_{hkey_name}', f"{recipe_id}", increment_value)



