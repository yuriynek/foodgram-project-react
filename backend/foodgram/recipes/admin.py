from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import (Tag, Ingredient, Recipe, RecipeTag,
                     RecipeIngredient, Favorite, ShoppingCart)


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('slug',)
    # list_editable = ('name', 'slug',)


@register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    # list_editable = ('name', 'measurement_unit',)


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pub_date', 'name', 'author',)
    search_fields = ('name',)
    filter_fields = ('pub_date', 'tags', 'ingredients',)


@register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag')
    # list_editable = ('recipe', 'tag')
    filter_fields = ('tag',)
    search_fields = ('recipe',)


@register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient')
    # list_editable = ('recipe', 'ingredient')
    filter_fields = ('ingredient',)
    search_fields = ('recipe',)


@register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)


@register(ShoppingCart)
class ShoppingCartAdmin(FavoriteAdmin):
    pass
