"""Urls for test page"""

from django.urls import path, include
from . import views
app_name ='test'


urlpatterns = [
    path('upload_image/', views.test_upload_image, name='test_upload_image'),
    path('login/', views.notification_test_login, name='notification_test_login')

]