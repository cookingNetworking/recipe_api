"""
URL mapping for user API.
"""

from django.urls import path

from user import views


app_name ='user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('check_email/',views.check_email_replicate, name='check_email_replicate'),
    path('check_username/',views.check_username_replicate, name='check_username_replicate'),
    path('login/',views.LoginView.as_view(), name='login'),
    path('logout/',views.LogoutView.as_view(), name='logout'),
    path('detail/',views.UserDetailView.as_view(), name='user_detail')
]