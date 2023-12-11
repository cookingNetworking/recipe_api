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

def decode_content(content):
    """Decode response content!"""
    content_dict = json.loads(content.decode('utf-8'))
    return content_dict

def detail_url(recipe_id):
    """Create and return detail recipe url with given recipe_id!!!"""
    return reverse("recipe:recipe-detail", args=[recipe_id])

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
            serializer = RecipeSQLDetailSerializer(recipe)
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

        res = self.client.post(RECIPE_URL, payload)
        print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['title'], payload['title'])
        self.assertEqual(res.data['cost_time'], payload['cost_time'])
        self.assertEqual(res.data['description'], payload['description'])
