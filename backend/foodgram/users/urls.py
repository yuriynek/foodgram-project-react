from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'users'

router = DefaultRouter()

router.register('users', views.UserViewSet,
                basename='users api endpoint')

urlpatterns = [
    path('', include(router.urls)),
]
