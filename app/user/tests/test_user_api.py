"""
Test user api.
"""


from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")


def create_user(**params):
    """Create user and return."""
    return get_user_model().objects.create_user(**params)

class TestUser(TestCase):
    """Test every api for /user."""
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Testing creating a user is successful."""
        params = {
                "email":"test1@example.com",
                "password":"test1123123123",
                "user":"testuser1"}
        res = self.client.post(CREATE_USER_URL, params)
        print(res)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        user = get_user_model().objects.get(email=params["email"])

        self.assertTrue(user.check_password(params["password"]))
        self.assertNotIn('password', res.data)    