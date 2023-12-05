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

def decode_content(content):
    """Decode response content!"""
    content_dict = json.loads(content.decode('utf-8'))
    return content_dict

def detail_url(recipe_id):
    """Create and return detail recipe url with given recipe_id!!!"""
    return reverse("recipe:recipe-detai", args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a simple recipe!"""
    defaults = {
        "title":"sample title",
        "cost_time":"20",
        "description":"Sample description",
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user,**defaults)
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
                "username":"testuser1"}
        user = create_user(**params)
        recipe = create_recipe(user=user)
        res = self.client.get(RECIPE_URL)
        res_content = json.loads(res.content)
        print(res_content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_content['results'][0]['id'], recipe.id)