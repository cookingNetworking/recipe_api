"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from user import views as user_views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path('admin/', admin.site.urls),
     # YOUR PATTERNS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('user/',include('user.urls')),
    path('signupVertify', view=user_views.sign_up_vertify, name='signupvertify' ),
    path('getCsrfToken/', user_views.GetCsrfToken.as_view(), name='getCsrfToken'),
    path('forget-password/', user_views.EmailVertificationView.as_view(), name='foregetpassword'),
    path('reset-password', user_views.ResetPasswordView.as_view(), name='resetpassword'),
    path('time/', user_views.time_now, name='time_now'),
    path('resendVertify/',user_views.ResendVertifyEmail.as_view(), name='reseendertifyemail')
]
