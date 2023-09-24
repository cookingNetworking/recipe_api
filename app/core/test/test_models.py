"""
Test for models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

class ModelTests(TestCase):
    """Test models."""
    def test_create_user_with_email(self):
        """Test creating user with email is successful."""
        email = "test1@example.com"
        password = "testpassword123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_with_normalize_email(self):
        """Test create user with normalized email."""
        sample_emails = [
            ['test5@EXAMPLE.com', 'test5@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, excepted in sample_emails:
            user = get_user_model().objects.create_user(email=email,password='password123')
            self.assertEqual(user.email, excepted)


    def test_create_user_without_email_raise_error(self):
        """Test create user without email."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("","passowrd123123")

    def test_create_superuser(self):
        """Test create superuser."""
        user = get_user_model().objects.create_superuser('super@example.com', 'superuser123')

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)