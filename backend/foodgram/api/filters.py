from django_filters import rest_framework as django_filters
from rest_framework import filters

from recipes import models, recipes_services


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
    )

    class Meta:
        model = models.Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact'
    )

    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        lookup_expr='icontains'
    )

    is_favorited = django_filters.BooleanFilter(
        method='show_favorited'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='show_shopping_cart'
    )

    class Meta:
        model = models.Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def show_favorited(self, queryset, name, value):
        if value:
            return recipes_services.get_user_favorite_recipes(
                user=self.request.user, queryset=queryset)
        return queryset.all()

    def show_shopping_cart(self, queryset, name, value):
        if value:
            return recipes_services.get_user_shopping_cart_recipes(
                user=self.request.user, queryset=queryset)
        return queryset.all()


class LimitRecipesFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        query_param = request.query_params.get('recipes_limit')
        try:
            return queryset[0:int(query_param)]
        except TypeError:
            return queryset
