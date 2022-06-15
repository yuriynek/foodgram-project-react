from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()

router.register('users', views.UserViewSet,
                basename='users api endpoint')
router.register('ingredients', views.IngredientViewSet,
                basename='ingredients api endpoint')
router.register('tags', views.TagViewSet,
                basename='tags api endpoint')
router.register('recipes', views.RecipeViewSet,
                basename='recipes api endpoint')

urlpatterns = [
    path('', include(router.urls)),
    path(f'auth/', include('djoser.urls')),
    path(f'auth/', include('djoser.urls.authtoken'))
]
