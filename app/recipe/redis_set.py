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
        self.redis_client.set(f'Recipe_detail_{recipe_id}',json_data, ex=timeout)

    def get_recipe(self, recipe_id):
        """
        Get recipe in redis.

        :param recipe_id: The ID of the recipe. Must be an integer.
        :return: The data associated with the recipe, if exists.
        """
        data = self.redis_client.get(f'Recipe_detail_{recipe_id}')

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
        self.redis_client.delete(f'Recipe_detail_{recipe_id}')

    def set_hkey(self, hkey_name: str, recipe_id: int, initinal_value=0):
        """
        Set hkey data type in cache(redis).

        :param recipe_id: The ID of the recipe. Must be an integer.
        :param initinal_value: The initial value of the recipe staff. Must be an integer.
        """
        if self.redis_client.hget(f"Recipe_{hkey_name}",f"{recipe_id}"):
            return KeyError({"error":"This recipe id is used before, please check again!"})
        self.redis_client.hset(f"Recipe_{hkey_name}", f"{recipe_id}", initinal_value)
        self.redis_client.hset(f"Prev_{hkey_name}",f"{recipe_id}", initinal_value)
        return True

    def get_hset(self, hkey_name: str):
        """
        Get the full hash set !
        """
        data = self.redis_client.get(f'Recipe_{hkey_name}')
        if data:
            try:
                return json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                    print(f"Error decoding JSON for Recipe_{hkey_name}: {e}")
                    return None
    def get_prev_hset(self, hkey_name: str):
        """
        Specilized for get hash
        """
        data = self.redis_client.get(f'Prev_{hkey_name}')
        if data:
            try:
                return json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                    print(f"Error decoding JSON for Recipe_{hkey_name}: {e}")
                    return None

    def get_hkey(self, hkey_name: str, recipe_id: int):
        """
        Get views value of giving recipe id.
        :param recipe_id: The ID of the recipe. Must be an integer.
        """
        recipe_view = self.redis_client.hget(f'Recipe_{hkey_name}', f"{recipe_id}")
        if recipe_view:
            return int(recipe_view)
        return None


    def del_hkey(self, hkey_name: str, *recipe_id: int):
        """
        Del  value of giving recipe id.
        :param recipe_id: The ID of the recipe. Must be an integer or list.
        """
        try:
            del_id = [str(key) for key in recipe_id]
            self.redis_client.hdel(f"Recipe_{hkey_name}", *del_id)
            return True
        except Exception as e:
            print(e)
            return False

    def update_hkey(self, hkey_name: str, *recipe_id: int, value: str):
        """
        Update the hkey value in hash .
        :param hkey_name: The hkey of the recipe. Must be an str.
        :param recipe_id: The ID of the recipe. Must be an integer.
        :param value: The value need to be updated. Must be an str.
        """
        value = self.get_hkey(hkey_name, recipe_id)
        if value is not None:
            self.redis_client.hmset(f"Recipe_{hkey_name}",{f"{recipe_id}": f"{value}"})
        else:
            self.set_hkey(hkey_name=hkey_name, recipe_id=recipe_id, value=value)

    def increase_recipe_view(self, hkey_name: str, recipe_id: int, increment_value=1):
        """
        Increase value for hkey value
        :param recipe_id: The ID of the recipe. Must be an integer.
        :param increment_value: The increase value of the recipe staff. Must be an integer.
        """
        value = self.get_hkey(hkey_name, f"{recipe_id}")
        print(value)
        if value is not None:
            self.redis_client.hincrby(f'Recipe_{hkey_name}', f"{recipe_id}", increment_value)
        else:
            raise ValueError({"error": f"{recipe_id} is not found in {hkey_name}"})



