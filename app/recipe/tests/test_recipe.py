"""Test recipe api end point!"""

from unittest.mock import patch, Mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import *
from recipe.serializers import RecipeSQLDetailSerializer
from rest_framework.test import APIClient, force_authenticate
from rest_framework import status
import json


RECIPE_URL = reverse("recipe:recipe-list")
RECIPE_COMMENT_URL = reverse("recipe:recipecomment-list")
INGREDIENT_URL = reverse("recipe:ingredient-list")
LIKE_RECIPE_URL = reverse("recipe:like-recipe")
SAVE_ACTION_URL = reverse("recipe:save-action")
def decode_content(content):
    """Decode response content!"""
    content_dict = json.loads(content.decode('utf-8'))
    return content_dict

def detail_url(recipe_id):
    """Create and return detail recipe url with given recipe_id!!!"""
    return reverse("recipe:recipe-detail", args=[recipe_id])

def detail_comment_rul(comment_id):
    """Create and return detail recipe comment url with given comment_id !!!"""
    return reverse("recipe:recipecomment-detail", args=[comment_id])

def create_recipe(user, **params):
    """Create and return a simple recipe!"""
    ingredient = Ingredient.objects.create(name='chocolate')
    defaults = {
        "title":"sample title",
        "cost_time":"20",
        "description":"Sample description",
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user,**defaults)
    recipe.ingredients.add(ingredient)
    recipe.save()
    return recipe

def create_user(**params):
    """Create user and return !"""
    return get_user_model().objects.create(**params)


class PublicAgentAPITests(TestCase):
    """Test unauthenticated API request!!"""
    def setUp(self):
        self.client= APIClient()

    def test_auth_required(self):
        """Test the API end point that need to login!!"""
        params = {
            'title':'sampletitle',
            'cost_time':'25',
            'description':'asjdiojfwioqwf'
        }

        res = self.client.post(RECIPE_URL, params)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_recipe_list_public(self):
        """Test the recipe list api could be access without login in!"""
        params = {
                "password":"test1123123123",
                "username":"testuser1"
                }
        user = create_user(**params)
        recipe2_params= {
            'title':'sampletitle1',
            'cost_time':'25',
            'description':'sample1'
        }
        recipe1 = create_recipe(user)
        recipe2 = Recipe.objects.create(user=user, **recipe2_params)

        res = self.client.get(RECIPE_URL)
        res_content = decode_content(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_content['results']), 2)
        self.assertEqual(res_content['results'][0]['id'], recipe1.id)
        self.assertEqual(res_content['results'][1]['id'], recipe2.id)

    def test_recipe_retrieve_public(self):
        """Test the recipe retrieve api could be access without login in!"""
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view,\
            patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe:
            params = {
                    "password":"test1123123123",
                    "username":"testuser1"
                    }
            user = create_user(**params)
            recipe = create_recipe(user=user)
            url = detail_url(recipe.id)
            mock_increase_recipe_view.return_value = None
            mock_set_recipe.return_value = None
            res = self.client.get(url)
            res_content = decode_content(res.content)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['id'], recipe.id)

    def test_recipe_list_filter_by_ingredient(self):
        """Test the recipe list api that filter by ingredients!"""
        params = {
                "password":"test1123123123",
                "username":"testuser1"
                }
        user = create_user(**params)
        recipe1 = create_recipe(user=user)
        recipe2_params= {
            'title':'sampletitle1',
            'cost_time':'25',
            'description':'sample1'
        }
        recipe2 = Recipe.objects.create(user=user, **recipe2_params)
        url = '/recipes/?ingredients=chocolate'
        res = self.client.get(url)
        res_content = decode_content(res.content)
        returned_recipe_ids = [recipe['id'] for recipe in res_content['results']]
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_content['results'][0]['id'], recipe1.id)
        self.assertNotIn(recipe2.id, returned_recipe_ids)

    def test_get_comments_list_public(self):
        """Test the recipe comments list for specific recipe."""
        params = {
                "password":"test1123123123",
                "username":"testuser1"
                }
        user = create_user(**params)
        recipe = create_recipe(user=user)
        comment_1 = RecipeComment.objects.create(
                                                user=user,
                                                recipe=recipe,
                                                comment='test comment1',
                                                rating=5
                                                )
        comment_2 = RecipeComment.objects.create(
                                                user=user,
                                                recipe=recipe,
                                                comment='test comment2',
                                                rating=3
                                                )
        res = self.client.get(
                            RECIPE_COMMENT_URL,
                            {"page": 1, "recipe_id":recipe.id}
                            )
        res_content = decode_content(res.content)
        comment_ids = [recipe['id'] for recipe in res_content['results']]
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_content['results']), 2)
        self.assertIn(comment_1.id, comment_ids)
        self.assertIn(comment_2.id, comment_ids)

    def test_ingredients_list_public(self):
        """Test ingredients list without login !"""
        ingredient_1 = Ingredient.objects.create(
                                                name='chocolate'
                                                    )
        ingredient_2 = Ingredient.objects.create(
                                                name='banana'
                                                )
        ingredient_3 = Ingredient.objects.create(
                                                name='beef'
                                                )

        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_content = decode_content(res.content)
        self.assertEqual(len(res_content['results']), 3)


class PrivateAgentAPITests(TestCase):
    """Test the unauthenticated API request!!"""
    def setUp(self):
        self.client = APIClient()
        user_params = {
            'email':'test1@example.com',
            'username':'test1'
        }
        self.user = create_user(**user_params)
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe(self):
        """Test retrieve the recipe detail imformation!"""
        payload = {
            'title':'testcase1',
            'cost_time':'15',
            'description':'asdjiwegfioag'
        }
        recipe = create_recipe(user=self.user, **payload)
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_set_recipe.return_value = None
            mock_increase_recipe_view.return_value = None
            res = self.client.get(url)
            res_content = decode_content(res.content)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['id'], recipe.id)
            self.assertEqual(res_content['title'], recipe.title)
            self.assertEqual(res_content['cost_time'], recipe.cost_time)
            self.assertEqual(res_content['description'], recipe.description)

    def test_recipe_list(self):
        """Test list the recipe !"""
        payload_1 = {
            'title':'test_recipe 1',
            'cost_time':'20',
            'description':'sdafjkl;asdf'
        }
        payload_2 = {
            'title':'test_recipe 2',
            'cost_time':'15',
            'description':'nmx,c.vbnm,xc.vnbm,.xcvbnm,.xcvb'
        }
        recipe_1 = create_recipe(user=self.user, **payload_1)
        recipe_2 = create_recipe(user=self.user, **payload_2)
        res = self.client.get(RECIPE_URL)
        res_content = decode_content(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_content['count'], 2)
        result_id = [ recipe['id'] for recipe in res_content['results']]
        self.assertIn(recipe_1.id, result_id)
        self.assertIn(recipe_2.id, result_id)

    def test_create_recipe(self):
        """Test create recipe with authenticated!"""
        payload = {
            'title':'test for create recipe',
            'cost_time':'20',
            'description':'Uni test'
        }
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.set_hkey') as mock_update_hkey:
            mock_set_recipe.return_value = None
            mock_update_hkey.return_value = None
            res = self.client.post(RECIPE_URL, payload)
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertEqual(res.data['title'], payload['title'])
            self.assertEqual(res.data['cost_time'], payload['cost_time'])
            self.assertEqual(res.data['description'], payload['description'])

    def test_put_recipe(self):
        """Test update recipe with authenticated!"""
        payload = {
            'title':'test_title_2',
            'cost_time':'25',
            'description':'recipe for test'
        }
        recipe = create_recipe(user=self.user, **payload)
        update_param = {
            'title':'new title',
            'cost_time':'20',
            'description':'recipe for test'
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
            mock_set_recipe.return_value = None
            mock_update_hkey.return_value = None
            res = self.client.put(url, update_param)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            res_content = decode_content(res.content)
            self.assertEqual(res_content['id'], recipe.id)
            self.assertEqual(res_content['title'], update_param['title'])
            self.assertEqual(res_content['cost_time'], update_param['cost_time'])

    def test_patch_recipe(self):
        """Test patch recipe (partial update!)"""
        payload = {
            'title':'test_for_patch',
            'cost_time':'30',
            'description': 'qwiojqiwo;fjioqwe'
        }
        recipe = create_recipe(user=self.user, **payload)
        update_param = {
            'title':'new title'
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
            mock_set_recipe.return_value = None
            mock_update_hkey.return_value = None
            res = self.client.patch(url, update_param)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            res_content = decode_content(res.content)
            self.assertEqual(res_content['id'], recipe.id)
            self.assertEqual(res_content['title'], update_param['title'])

    def test_delete_recipe(self):
        """Test delete recipe with authenticated!"""
        payload = {
            'title':'test_for_delete',
            'cost_time':'30',
            'description': 'qwiojqiwo;fjioqwe'
        }
        recipe = create_recipe(user=self.user, **payload)
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.del_hkey') as mock_del_hkey, \
            patch('recipe.redis_set.RedisHandler.del_prev_hkey') as mock_del_prev_hkey:
            res = self.client.delete(url)
            self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
            res2 = self.client.get(url)
            self.assertEqual(res2.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_comment(self):
        """Add comment to recipe!"""
        recipe_params = {
            'title':'test_for_add_comment',
            'cost_time':'30',
            'description':'I LOVE UNITEST!!!!!'
        }
        recipe = create_recipe(user=self.user, **recipe_params)
        payload = {
            'recipe':f'{recipe.id}',
            'comment':'Nice recipe, it help me a lot !!!',
            'rating': 5
        }
        with patch('recipe.redis_set.RedisHandler.update_recipe_in_cache') as mock_update_recipe_in_cache, \
            patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_update_recipe_in_cache.return_value = None
            mock_set_recipe.return_value = None
            mock_increase_recipe_view.return_value = None
            res = self.client.post(RECIPE_COMMENT_URL, payload)
            res_content1 = decode_content(res.content)
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            url = detail_url(recipe.id)
            res_retrieve_recipe = self.client.get(url)
            res_content2 = decode_content(res_retrieve_recipe.content)

            self.assertEqual(res_retrieve_recipe.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content2['top_five_comments'][0]['id'], res_content1['id'])

    def test_update_comment(self):
        """Test PUT recipe comment!"""
        recipe_params = {
            'title':'test_for_update_comment',
            'cost_time':'30',
            'description':'I LOVE la !!!!!'
        }
        recipe = create_recipe(user=self.user, **recipe_params)
        comment_params = {
            'comment':'for update test',
            'rating':5
        }
        recipe_comment = RecipeComment.objects.create(
                                                    user=self.user,
                                                    recipe=recipe,
                                                    **comment_params
                                                    )
        with patch('recipe.redis_set.RedisHandler.update_recipe_in_cache') as mock_update_recipe_in_cache:
            mock_update_recipe_in_cache.return_value = None
            payload = {
                'recipe': recipe.id,
                'comment':'updated!!!',
                'rating': 5
            }
            url = detail_comment_rul(recipe_comment.id)
            res = self.client.put(url, payload)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            res_content = decode_content(res.content)
            self.assertEqual(res_content['id'], recipe_comment.id)
            self.assertEqual(res_content['comment'], payload['comment'])

    def test_partial_update_comment(self):
        """Test patch recipe comment !!!"""
        recipe_params = {
            'title':'partial_update_comment',
            'cost_time':'30',
            'description':'I LOVE la !!!!!'
        }
        recipe = create_recipe(user=self.user, **recipe_params)
        comment_params = {
            'comment':'for partial_update test',
            'rating':5
        }
        recipe_comment = RecipeComment.objects.create(
                                                    user=self.user,
                                                    recipe=recipe,
                                                    **comment_params
                                                    )
        with patch('recipe.redis_set.RedisHandler.update_recipe_in_cache') as mock_update_recipe_in_cache:
            mock_update_recipe_in_cache.return_value = None
            payload = {
                'recipe': recipe.id,
                'rating': 3
            }
            url = detail_comment_rul(recipe_comment.id)
            res = self.client.patch(url, payload)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            res_content = decode_content(res.content)
            self.assertEqual(res_content['id'], recipe_comment.id)
            self.assertEqual(res_content['rating'], payload['rating'])

    def test_destroy_comment(self):
        """Test for delete comment!!!"""
        recipe_params = {
            'title':'partial_update_comment',
            'cost_time':'30',
            'description':'I LOVE la !!!!!'
        }
        recipe = create_recipe(user=self.user, **recipe_params)
        comment_params = {
            'comment':'for destroy test',
            'rating':5
        }
        recipe_comment = RecipeComment.objects.create(
                                                    user=self.user,
                                                    recipe=recipe,
                                                    **comment_params
                                                    )
        with patch('recipe.redis_set.RedisHandler.update_recipe_in_cache') as mock_update_recipe_in_cache:
            mock_update_recipe_in_cache.return_value = None
            url = detail_comment_rul(recipe_comment.id)
            res = self.client.delete(url)
            self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_recipe_with_ingredients(self):
        """Test add ingredient when create recipe!"""
        payload = {
            'title':'test_for_add_ingredients',
            'cost_time':'20',
            'description':'asdkioasjdf',
            'ingredients':['banana']
        }
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.set_hkey') as mock_set_hkey:
            mock_set_recipe.return_value = None
            mock_set_hkey.return_value = None
            res = self.client.post(RECIPE_URL, payload)
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            exist = Ingredient.objects.filter(name=payload['ingredients'][0])
            self.assertTrue(exist)

    def test_create_recipe_with_exist_ingredient(self):
        """Test create recipe with exist ingredient!"""
        Ingredient.objects.create(name='steak')
        payload = {
            'title':'with_exist_ingredient',
            'cost_time':'20',
            'description':'asjiddsjiofp;aosdg',
            'ingredients':['steak', 'onion']
        }
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.set_hkey') as mock_set_hkey:
            mock_set_recipe.return_value = None
            mock_set_hkey.return_value = None
            res = self.client.post(RECIPE_URL, payload)
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            res_content = decode_content(res.content)
            ingredients = res_content['ingredients']
            for ingredient in payload['ingredients']:
                exist = Ingredient.objects.filter(name=ingredient)
                self.assertIn(ingredient, ingredients)
                self.assertTrue(exist)

    def test_create_ingredient_on_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients':['chocolate']
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
            mock_set_recipe.return_value = None
            mock_update_hkey.return_value = None
            res = self.client.patch(url, payload)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            exist = Ingredient.objects.filter(name=payload['ingredients'][0]).exists
            self.assertTrue(exist)

    def test_update_recipe_with_assigned_ingredients(self):
        """Test assign an exist ingredient when update recipe! """
        ingredient = Ingredient.objects.create(name='salt')
        pre_ingredient = Ingredient.objects.create(name='sugar')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(pre_ingredient)
        payload = {
            'ingredients':['salt']
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
                mock_set_recipe.return_value = None
                mock_update_hkey.return_value = None
                res = self.client.patch(url, payload)
                self.assertEqual(res.status_code, status.HTTP_200_OK)
                recipe.refresh_from_db()
                self.assertIn(ingredient, recipe.ingredients.all())
                self.assertNotIn(pre_ingredient, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clear recipe tags!"""
        ingredient = Ingredient.objects.create(name='chocolate')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)
        payload = {
            'ingredients':[]
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
                mock_set_recipe.return_value = None
                mock_update_hkey.return_value = None
                res = self.client.patch(url, payload)
                self.assertEqual(res.status_code, status.HTTP_200_OK)
                recipe.refresh_from_db()
                self.assertNotIn(ingredient, recipe.ingredients.all())

    def test_create_recipe_with_tags(self):
        """Test add tag when create recipe!"""
        payload = {
            'title':'test_for_add_ingredients',
            'cost_time':'20',
            'description':'asdkioasjdf',
            'tags':['dinner']
        }
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.set_hkey') as mock_set_hkey:
            mock_set_recipe.return_value = None
            mock_set_hkey.return_value = None
            res = self.client.post(RECIPE_URL, payload)
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            exist = Tag.objects.filter(name=payload['tags'][0])
            self.assertTrue(exist)

    def test_create_recipe_with_exist_tag(self):
        """Test create recipe with exist tag!"""
        Tag.objects.create(name='brunch')
        payload = {
            'title':'with_exist_ingredient',
            'cost_time':'20',
            'description':'asjiddsjiofp;aosdg',
            'tags':['brunch', 'anmerico']
        }
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.set_hkey') as mock_set_hkey:
            mock_set_recipe.return_value = None
            mock_set_hkey.return_value = None
            res = self.client.post(RECIPE_URL, payload)
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            res_content = decode_content(res.content)
            tags = res_content['tags']
            for tag in payload['tags']:
                exist = Tag.objects.filter(name=tag)
                self.assertIn(tag, tags)
                self.assertTrue(exist)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {
            'tags':['lunch']
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
            mock_set_recipe.return_value = None
            mock_update_hkey.return_value = None
            res = self.client.patch(url, payload)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            exist = Tag.objects.filter(name=payload['tags'][0]).exists
            self.assertTrue(exist)

    def test_update_recipe_with_assigned_tags(self):
        """Test assign an exist tag when update recipe! """
        tag = Tag.objects.create(name='breakfast')
        pre_tag = Tag.objects.create(name='dinner')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(pre_tag)
        payload = {
            'tags':['breakfast']
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
                mock_set_recipe.return_value = None
                mock_update_hkey.return_value = None
                res = self.client.patch(url, payload)
                self.assertEqual(res.status_code, status.HTTP_200_OK)
                recipe.refresh_from_db()
                self.assertIn(tag, recipe.tags.all())
                self.assertNotIn(pre_tag, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clear recipe tags!"""
        tag = Tag.objects.create(name='India')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        payload = {
            'tags':[]
        }
        url = detail_url(recipe.id)
        with patch('recipe.redis_set.RedisHandler.set_recipe') as mock_set_recipe, \
            patch('recipe.redis_set.RedisHandler.update_hkey') as mock_update_hkey:
                mock_set_recipe.return_value = None
                mock_update_hkey.return_value = None
                res = self.client.patch(url, payload)
                self.assertEqual(res.status_code, status.HTTP_200_OK)
                recipe.refresh_from_db()
                self.assertNotIn(tag, recipe.tags.all())

    def test_like_recipe(self):
        """Test user like recipe api!"""
        recipe = create_recipe(user=self.user)
        prev_recipe_like = recipe.likes
        payload = {
            'recipe_id':f'{recipe.id}'
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(LIKE_RECIPE_URL, payload)
            recipe.refresh_from_db()
            res_content = decode_content(res.content)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(recipe.likes, prev_recipe_like + 1)
            self.assertEqual(res_content['message'], 'Like action successed!')
            exist = Like.objects.filter(recipe=recipe, user=self.user)
            self.assertTrue(exist)

    def test_revoke_like_recipe(self):
        """Test user revoke like recipe api!!"""
        recipe = create_recipe(user=self.user, likes=1)
        Like.objects.create(user=self.user, recipe=recipe)
        prev_recipe_like = recipe.likes
        payload = {
            'recipe_id':f'{recipe.id}'
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(LIKE_RECIPE_URL, payload)
            recipe.refresh_from_db()
            res_content = decode_content(res.content)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(recipe.likes, prev_recipe_like - 1)
            self.assertEqual(res_content['message'], "Like action was revoke!")
            exist = Like.objects.filter(recipe=recipe, user=self.user)
            self.assertFalse(exist)

    def test_save_recipe(self):
        """Test user save recipe action !!!"""
        recipe = create_recipe(user=self.user)
        prev_recipe_save_count = recipe.save_count
        payload = {
            'recipe_id':recipe.id
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(SAVE_ACTION_URL, payload)
            res_content = decode_content(res.content)
            recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['message'], 'User save the recipe!')
            self.assertEqual(recipe.save_count, prev_recipe_save_count + 1)
            exist = Save.objects.filter(user=self.user, recipe=recipe)
            self.assertTrue(exist)

    def test_unsave_recipe(self):
        """Test user unsave recipe action !!!"""
        recipe = create_recipe(user=self.user)
        Save.objects.create(user=self.user, recipe=recipe)
        prev_recipe_save_count = recipe.save_count
        payload = {
            'recipe_id':recipe.id
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(SAVE_ACTION_URL, payload)
            res_content = decode_content(res.content)
            recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(recipe.save_count, prev_recipe_save_count - 1)
            self.assertEqual(res_content['message'], 'User unsaved the recipe !')
            exist = Save.objects.filter(user=self.user, recipe=recipe)
            self.assertFalse(exist)

    def test_save_ingredient(self):
        """Test save ingredient!!!"""
        ingredient = Ingredient.objects.create(name='chocolate')
        payload = {
            'ingredient':f'{ingredient.name}'
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(SAVE_ACTION_URL, payload)
            res_content = res_content = decode_content(res.content)
            ingredient.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['message'], 'User save the ingredient!')
            exist = Save.objects.filter(user=self.user, ingredient=ingredient)
            self.assertTrue(exist)

    def test_unsave_ingredient(self):
        """Test unsave ingredients"""
        ingredient = Ingredient.objects.create(name='chocolate')
        Save.objects.create(ingredient=ingredient, user=self.user)
        payload = {
            'ingredient':f'{ingredient.name}'
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(SAVE_ACTION_URL, payload)
            res_content = res_content = decode_content(res.content)
            ingredient.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['message'], 'User unsaved the ingredient !')
            exist = Save.objects.filter(user=self.user, ingredient=ingredient)
            self.assertFalse(exist)

    def test_save_tag(self):
        """Test save ingredient!!!"""
        tag = Tag.objects.create(name='lunch')
        payload = {
            'tag':f'{tag.name}'
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(SAVE_ACTION_URL, payload)
            res_content = res_content = decode_content(res.content)
            tag.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['message'], 'User save the tag!')
            exist = Save.objects.filter(user=self.user, tag=tag)
            self.assertTrue(exist)

    def test_unsave_tag(self):
        """Test unsave ingredients"""
        tag = Tag.objects.create(name='breakfast')
        Save.objects.create(tag=tag, user=self.user)
        payload = {
            'tag':f'{tag.name}'
        }
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            mock_increase_recipe_view.return_value = True
            res = self.client.post(SAVE_ACTION_URL, payload)
            res_content = res_content = decode_content(res.content)
            tag.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['message'], 'User unsaved the tag !')
            exist = Save.objects.filter(user=self.user, tag=tag)
            self.assertFalse(exist)