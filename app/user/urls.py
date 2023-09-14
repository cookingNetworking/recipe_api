"""
URL mapping for user API.
"""

from django.urls import path

from user import views


app_name ='user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('check_email',views.check_email_replicate, name='check_email_replicate')
]