from django_filters import rest_framework as django_filters
from . import models


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = models.Ingredient
        fields = {'name': ['istartswith', 'icontains']}


def favorites(request):
    if request is None:
        return models.Recipe.objects.none()
    return models.Recipe.objects.filter(
        id__in=request.user.favorites.all().values_list('recipe', flat=True))


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact'
    )
    tags = django_filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='exact'
    )
    is_favorited = django_filters.ModelChoiceFilter(
        queryset=favorites
    )
    is_favorited = django_filters.BooleanFilter(

    )

    class Meta:
        model = models.Recipe
        fields = ('author', 'tags', 'is_favorited')



