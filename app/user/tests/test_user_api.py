"""
Test user api.
"""
from unittest.mock import patch, Mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


from rest_framework.test import APIClient
from rest_framework import status

import jwt
import datetime
import os

CREATE_USER_URL = reverse("user:create")
GET_CSRF_TOKEN_URL = reverse("getCsrfToken")
ACTIVATE_USER_URL = reverse("signupvertify")

def create_user(**params):
    """Create user and return."""
    return get_user_model().objects.create_user(**params)


def create_wrong_token(email=None,time=None):
    if  not email:
        email = 'wrong.email@example.com'
    if not time:      
       time = int(datetime.datetime.now().timestamp()+(15*60))
    payload={
        "email": email,
        "exp": str(time)
    }
    secret_key = os.environ.get('secret_key')
    token = jwt.encode(payload, str(secret_key), algorithm='HS256')
    return token


class TestUser(TestCase):
    """Test every api for /user."""
    def setUp(self):
        self.client = APIClient()
    

    def test_create_user_success(self, ):
        """Testing creating a user is successful."""
        with patch('user.tasks.sending_mail.apply_async') as mock_sending_mail, patch('user.tasks.delete_unactivate_user.apply_async') as mock_delete_unactivate:
            mock_delete_unactivate.return_value = Mock(id='mocked_id')
            mock_sending_mail.return_value = None
            
            params = {
                "email": "test1@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser1",
            }
            
            # Perform user creation
            res = self.client.post(CREATE_USER_URL, params)
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            
            user = get_user_model().objects.get(email=params["email"])

            self.assertTrue(user.check_password(params["password"]))
            self.assertNotIn('password', res.data)
    
    def test_email_already_exist(self):
        """Test email already exist."""
        params = {
                "email":"test1@example.com",
                "password":"test1123123123",
                "username":"testuser1",
                }
        
        create_user(**params)
        
        res = self.client.post(CREATE_USER_URL, params)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    

    def test_create_user_without_email(self):
        """Test creating a user without email."""
        params = {
                "password":"test1123123123",
                "username":"testuser1"} 
        res = self.client.post(CREATE_USER_URL, params)   
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        params1 = {
                "email": "",
                "password":"test1123123123",
                "username":"testuser1"} 
        res = self.client.post(CREATE_USER_URL, params1)   
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    

    def test_create_user_password_tooshort(self):
        """Test creat a user with invalide password!"""
        params = {
                "email":"test1@example.com",
                "password":"test",
                "username":"testuser1",
                }
        res = self.client.post(CREATE_USER_URL, params)
        
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_user_without_csrftoken(self):
        """Test create user without csrftoken."""
        self.client = APIClient(enforce_csrf_checks=True)
        params = {
                "email":"test1@example.com",
                "password":"test",
                "username":"testuser1",
                }
        res = self.client.post(CREATE_USER_URL, params)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
    

    def test_activate_user(self):
        """Test activating the user just created."""
        with patch('user.tasks.sending_mail.apply_async') as mock_sending_mail, patch('user.tasks.delete_unactivate_user.apply_async') as mock_delete_unactivate:
            mock_delete_unactivate.return_value = Mock(id='mocked_id')
            mock_sending_mail.return_value = None
            
            params = {
                "email": "test1@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser1",
            }
            
            # Perform user creation
            res =self.client.post(CREATE_USER_URL, params)
            result = res.json()
            token = result.get('token')

                # Mock the AbortableAsyncResult
            with patch('user.views.AbortableAsyncResult') as MockedAsyncResultClass:
                mock_instance = Mock()
                mock_instance.abort.return_value = None
                mock_instance.state = 'REVOKED'  # Or any state you want for your test case
                MockedAsyncResultClass.return_value = mock_instance

                # Perform the sign up verify
                res = self.client.get(ACTIVATE_USER_URL + f'?token={token}')
                
                self.assertEqual(res.status_code, status.HTTP_200_OK)
    

    def test_active_user_wrong_token(self):
        """Test active user with wrong token."""
        with patch('user.tasks.sending_mail.apply_async') as mock_sending_mail, patch('user.tasks.delete_unactivate_user.apply_async') as mock_delete_unactivate:
            mock_delete_unactivate.return_value = Mock(id='mocked_id')
            mock_sending_mail.return_value = None
            
            params = {
                "email": "test1@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser1",
            }
            
            # Perform user creation
            res = self.client.post(CREATE_USER_URL, params)
            res_token = res.json().get('token')         
            token = "vmfdskl;jgiowj jivoasjodvpkl;vnikao;nvikosa;dnv"   
            self.assertNotEqual(token, res_token)
            res = self.client.get(ACTIVATE_USER_URL + f'?token={token}')
            self.assertEqual(res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    def test_active_with_wrong_email_token(self):
        with patch('user.tasks.sending_mail.apply_async') as mock_sending_mail, patch('user.tasks.delete_unactivate_user.apply_async') as mock_delete_unactivate:
            mock_delete_unactivate.return_value = Mock(id='mocked_id')
            mock_sending_mail.return_value = None
            
            params = {
                "email": "test1@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser1",
            }
            
            # Perform user creation
            self.client.post(CREATE_USER_URL, params)
            token = create_wrong_token()
            res = self.client.get(ACTIVATE_USER_URL + f'?token={token}')
            secret_key = os.environ.get('secret_key')
            decode_token = jwt.decode(token, str(secret_key), algorithms=['HS256'])
            self.assertNotEqual(decode_token['email'], "test1@example.com")
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST) 

    def test_active_with_expired_token(self):
        """Test active suer with expired token!"""
        with patch('user.tasks.sending_mail.apply_async') as mock_sending_mail, patch('user.tasks.delete_unactivate_user.apply_async') as mock_delete_unactivate:
            mock_delete_unactivate.return_value = Mock(id='mocked_id')
            mock_sending_mail.return_value = None
            
            params = {
                "email": "test1@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser1",
            }
            
            # Perform user creation
            self.client.post(CREATE_USER_URL, params)
            with patch('user.views.AbortableAsyncResult') as MockedAsyncResultClass:
                mock_instance = Mock()
                mock_instance.abort.return_value = None
                mock_instance.state = 'REVOKED'  # Or any state you want for your test case
                MockedAsyncResultClass.return_value = mock_instance
                current_time =str(int(datetime.datetime.now().timestamp()))
                token = create_wrong_token("test1@example.com", current_time)       
                res = self.client.get(ACTIVATE_USER_URL + f'?token={token}')
                self.assertEqual(res.json().get("error"), 'Token is expired.')
                self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_csrf_token(self):
        """Test get csrf Token work or not!""" 
        res = self.client.get(GET_CSRF_TOKEN_URL)
        
        cookies = self.client.cookies
        self.assertIn("csrftoken", cookies)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        