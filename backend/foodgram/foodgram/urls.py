from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import path, include
from djoser.conf import default_settings

API_URL = 'api'


urlpatterns = [
    path('admin/', admin.site.urls),
    path(f'{API_URL}/', include('users.urls', namespace='users')),
    path(f'{API_URL}/', include('recipes.urls', namespace='recipes')),
    path(f'{API_URL}/auth/', include('djoser.urls')),
    path(f'{API_URL}/auth/', include('djoser.urls.authtoken'))
]
