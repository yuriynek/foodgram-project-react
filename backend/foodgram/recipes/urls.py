from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'recipes'

router = DefaultRouter()

router.register('ingredients', views.IngredientViewSet,
                basename='ingredients api endpoint')
router.register('tags', views.TagViewSet,
                basename='tags api endpoint')
router.register('recipes', views.RecipeViewSet,
                basename='recipes api endpoint')

urlpatterns = [
    path('', include(router.urls)),
]
