from rest_framework import serializers, validators, exceptions
from users.serializers import UserSerializer
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from . import models
import base64
import uuid


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=models.Ingredient.objects.all().values_list('pk', flat=True),
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = models.RecipeIngredient
        fields = ('amount', 'id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all().values_list('pk', flat=True),
    )

    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('name', 'color', 'slug')

    def to_internal_value(self, data):
        if isinstance(data, int):
            data = {'id': data}
        return super().to_internal_value(data)


class ImageFromBase64Field(serializers.ImageField):
    def to_internal_value(self, data):
        try:
            data_format, base64_string = data.split(';base64,')
            extension = data_format.split('/')[-1]
            image_id = uuid.uuid4()
            data = ContentFile(
                base64.b64decode(base64_string),
                name=f'{image_id}.{extension}'
            )
        except exceptions.APIException:
            raise serializers.ValidationError('Ошибка декодирования изображения')
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):

    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredients_in_recipe')
    tags = TagSerializer(many=True,)
    image = ImageFromBase64Field()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = ('id', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, recipe):
        return recipe.favorite_recipes.filter(
            user=self.context.get('request').user,
            recipe=recipe
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        return recipe.shopping_recipes.filter(
            user=self.context.get('request').user,
            recipe=recipe
        ).exists()

    @staticmethod
    def create_tags_in_recipe(tags, recipe):
        for tag in tags:
            models.RecipeTag.objects.create(
                recipe=recipe,
                tag=get_object_or_404(models.Tag, pk=tag.get('id')))
        return None

    @staticmethod
    def create_ingredients_in_recipe(ingredients, recipe):
        for ingredient_in_recipe in ingredients:
            models.RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=get_object_or_404(
                    models.Ingredient, pk=ingredient_in_recipe.get('id')),
                amount=ingredient_in_recipe.get('amount'))
        return None

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_in_recipe')
        recipe = models.Recipe.objects.create(**validated_data)
        self.create_tags_in_recipe(tags, recipe)
        self.create_ingredients_in_recipe(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_in_recipe')
        models.RecipeTag.objects.filter(recipe=recipe).delete()
        models.RecipeIngredient.objects.filter(recipe=recipe).delete()
        models.Recipe.objects.filter(pk=recipe.pk).update(**validated_data)
        self.create_tags_in_recipe(tags, recipe)
        self.create_ingredients_in_recipe(ingredients, recipe)
        return recipe


class ShoppingCartSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ReadOnlyField(source='recipe.image.url')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = models.ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time', 'recipe', 'user')
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True},
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe')),
        ]

    def delete(self):
        data = self.initial_data
        user_recipe = self.Meta.model.objects.filter(
            recipe=data['recipe'],
            user=data['user']
        )
        if not user_recipe.exists():
            raise serializers.ValidationError('Ошибка - такой записи не существует!')
        user_recipe.delete()


class FavoriteSerializer(ShoppingCartSerializer):

    class Meta(ShoppingCartSerializer.Meta):
        model = models.Favorite
