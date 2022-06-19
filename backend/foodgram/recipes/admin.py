from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import (Tag, Ingredient, Recipe, RecipeTag,
                     RecipeIngredient, Favorite, ShoppingCart)


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('slug',)


@register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'in_favorite_counts')
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('in_favorite_counts',)

    @admin.display(description='Количество добавлений в избранное')
    def in_favorite_counts(self, recipe):
        return recipe.favorite_recipes.count()


@register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag')
    list_filter = ('tag',)
    search_fields = ('recipe',)


@register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe',)
    search_fields = ('ingredient',)


@register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user',)


@register(ShoppingCart)
class ShoppingCartAdmin(FavoriteAdmin):
    pass
