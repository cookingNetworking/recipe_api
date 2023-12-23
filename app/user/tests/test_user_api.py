"""
Test user api.
"""
from unittest.mock import patch, Mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import UserFollowing

from rest_framework.test import APIClient, force_authenticate
from rest_framework import status

import jwt
import datetime
import os
import json

CREATE_USER_URL = reverse("user:user_create")
GET_CSRF_TOKEN_URL = reverse("getCsrfToken")
ACTIVATE_USER_URL = reverse("signupvertify")
LOGIN_URL = reverse("user:login")
LOGOUT_URL = reverse("user:logout")
USER_DETAIL_URL = reverse("user:user_detail")
USER_LIST_URL = reverse("user:user_list")
USER_CHANGE_PASSWORD_URL = reverse("user:changepassword")
FOLLOW_USER_URL = reverse("user:follow")

def create_user(**params):
    """Create user and return."""
    return get_user_model().objects.create_user(**params)

def decode_content(content):
    """Decode response content!"""
    content_dict = json.loads(content.decode('utf-8'))
    return content_dict

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
        payload = {
            "email":"create@example.com",
            "password":"asduiwqhdquiwf",
            "username": "ceateduser",
            "role": 'user',
            "is_active": True,
            "is_staff": True
        }
        self.exist_user = get_user_model().objects.create(**payload)
    def test_create_user_success(self):
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

    def test_login_successed(self):
        """Test login successed!"""
        payload = {
                "email": "test1@example.com",
                "username": "testuser1",
                "is_active": True
            }
        user = get_user_model().objects.create(**payload)
        user.set_password("123564qefqwgqawegdef")
        user.save()
        params = {
            "email": "test1@example.com",
            "password": "123564qefqwgqawegdef"
        }
        res = self.client.post(LOGIN_URL, json.dumps(params), content_type='application/json')
        content = res.content.decode('utf-8')
        content_dict = json.loads(content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(content_dict['detail']['user']['email'], user.email)
        self.assertEqual(content_dict['detail']['user']['username'], user.username)

    def test_login_fail_wrong_email(self):
        """Test login with wrong eamil !"""
        payload = {
                "email": "test1@example.com",
                "username": "testuser1",
                "is_active": True
            }
        user = get_user_model().objects.create(**payload)
        user.set_password("123564qefqwgqawegdef")
        user.save()
        params = {
            "email": "wrong@example.com",
            "password": "123564qefqwgqawegdef"
        }
        res = self.client.post(LOGIN_URL, json.dumps(params), content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_fail_wrong_password(self):
        """Test login with wrong eamil !"""
        payload = {
                "email": "test1@example.com",
                "username": "testuser1",
                "is_active": True
            }
        user = get_user_model().objects.create(**payload)
        user.set_password("123564qefqwgqawegdef")
        user.save()
        params = {
            "email": "wrong@example.com",
            "password": "wrongpaassword"
        }
        res = self.client.post(LOGIN_URL, json.dumps(params), content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        """Test logout user!"""
        token_res = self.client.get(GET_CSRF_TOKEN_URL)
        csrf_token = token_res.cookies["csrftoken"].value
        self.client.force_authenticate(user=self.exist_user)
        res = self.client.post(LOGOUT_URL,HTTP_X_CSRFTOKEN=csrf_token)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_edit_user_email(self):
        """Test edit user info."""
        self.client.force_authenticate(user=self.exist_user)
        params = {
            "email": "edit@example.com"
        }
        res = self.client.patch(USER_DETAIL_URL, params)
        res_dict = decode_content(res.content)
        self.exist_user.refresh_from_db()
        self.assertEqual(self.exist_user.email, res_dict['email'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_edit_user_username(self):
        """Test edit user username."""
        self.client.force_authenticate(user=self.exist_user)
        params = {
            'username': "editname"
        }
        res = self.client.patch(USER_DETAIL_URL, params)
        self.exist_user.refresh_from_db()
        res_dict = decode_content(res.content)
        self.assertEqual(self.exist_user.username, res_dict['username'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_edit_user_role(self):
        """Test edit user role!"""
        self.client.force_authenticate(user=self.exist_user)
        params = {
            'role': "cook"
        }
        res = self.client.patch(USER_DETAIL_URL, params)
        res_dict = decode_content(res.content)
        self.exist_user.refresh_from_db()
        self.assertEqual(self.exist_user.role, res_dict['role'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_change_password(self):
        """Test change user password"""
        self.client.force_authenticate(user=self.exist_user)
        params = {
            "new_password": "newpassword123"
        }
        res = self.client.post(USER_CHANGE_PASSWORD_URL, params)
        self.exist_user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user = get_user_model().objects.get(pk=self.exist_user.pk)
        self.assertTrue(user.check_password("newpassword123"))


    def test_list_user(self):
        """Test list all user!"""
        self.client.force_authenticate(user=self.exist_user)
        params = {
            "user1":{
                "email":"mail1@example.com",
                "username": "user1",
                "is_active":True
            },
            "user2":{
                "email":"mail2@example.com",
                "username": "user2",
                "is_active":True
            },
        }
        for user_data in params.values():
            get_user_model().objects.create(**user_data)
        res = self.client.get(USER_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_content = decode_content(res.content)
        self.assertEqual(len(res_content['results']), 3)

    def test_follow_user(self):
        """Test user follow system!!"""
        self.client.force_authenticate(user=self.exist_user)
        params = {
                "email": "test3@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser3",
            }
        user_2 = get_user_model().objects.create(**params)
        payload = {"following_user_id": user_2.id}
        res = self.client.post(FOLLOW_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        exist = UserFollowing.objects.filter(
                                            user_id=self.exist_user,
                                            following_user_id=user_2
                                            ).exists()
        self.assertTrue(exist)

    def test_unfollow_user(self):
        """Test unfollow user endpoint!!"""
        self.client.force_authenticate(user=self.exist_user)
        params = {
                "email": "test3@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser3",
            }
        user_2 = get_user_model().objects.create(**params)
        follow = UserFollowing.objects.create(
                                            user_id=self.exist_user,
                                            following_user_id=user_2
                                            )
        payload = {"following_user_id": user_2.id}
        res = self.client.post(FOLLOW_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        exist = UserFollowing.objects.filter(
                                            user_id=self.exist_user,
                                            following_user_id=user_2
                                            ).exists()
        self.assertFalse(exist)

    def test_follow_list(self):
        """Test follow list for login user!!!"""
        self.client.force_authenticate(user=self.exist_user)
        params = {
                "email": "test3@example.com",
                "password": "123564qefqwgqawegdef",
                "username": "testuser3",
            }
        user_2 = get_user_model().objects.create(**params)
        follow = UserFollowing.objects.create(
                                            user_id=self.exist_user,
                                            following_user_id=user_2
                                            )
        res = self.client.get(FOLLOW_USER_URL)
        res_content = decode_content(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_content['results']), 1)
        self.assertEqual(res_content['results'][0]["following_user_id"], user_2.id)