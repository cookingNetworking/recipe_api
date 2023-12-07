"""Test recipe api end point!"""

from unittest.mock import patch, Mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import *

from rest_framework.test import APIClient, force_authenticate
from rest_framework import status
import json


RECIPE_URL = reverse("recipe:recipe-list")
RECIPE_COMMENT_URL = reverse("recipe:recipecomment-list")

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
        with patch('recipe.redis_set.RedisHandler.increase_recipe_view') as mock_increase_recipe_view:
            params = {
                    "password":"test1123123123",
                    "username":"testuser1"
                    }
            user = create_user(**params)
            recipe = create_recipe(user=user)
            url = detail_url(recipe.id)
            mock_increase_recipe_view.return_value = None
            res = self.client.get(url)
            res_content = decode_content(res.content)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res_content['recipe']['id'], recipe.id)

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
    
    def test_get_comments_list(self):
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
        print(res_content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_content['results']), 2)
        