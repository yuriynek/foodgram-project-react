from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework import validators

from api.fields import ImageFromBase64Field
from api.mixins import FlattenMixinSerializer
from recipes import models, recipes_services
from users.models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed')
        read_only_fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed')

    def get_is_subscribed(self, user):
        subscriber = self.context.get('request').user
        if not subscriber.is_authenticated:
            return False
        return user.subscribers.filter(
            subscriber=subscriber
        ).exists()


class CreateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')
        required_fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True, 'required': True},
        }

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=models.Ingredient.objects.all().values_list(
            'pk', flat=True),
        validators=[validators.UniqueValidator(
            queryset=models.Ingredient.objects.all().values_list('id', flat=True)
        )]
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = models.RecipeIngredient
        fields = ('amount', 'id', 'name', 'measurement_unit')

    def to_representation(self, instance):
        """???????????????????? id ?????????????????????? ?????? ???????????? ???? ???????????? ????????????"""
        representation = super().to_representation(instance)
        representation['id'] = get_object_or_404(
            models.RecipeIngredient,
            id=representation['id']
        ).ingredient.id
        return representation


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
        read_only_fields = ('id', 'author', 'is_favorited',
                            'is_in_shopping_cart')

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return recipe.favorite_recipes.filter(
            user=user,
            recipe=recipe
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return recipe.shopping_recipes.filter(
            user=user,
            recipe=recipe
        ).exists()

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_in_recipe')
        recipe = models.Recipe.objects.create(**validated_data)
        recipes_services.create_tags_in_recipe(tags, recipe)
        recipes_services.create_ingredients_in_recipe(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_in_recipe')
        image = validated_data.pop('image')
        models.RecipeTag.objects.filter(recipe=recipe).delete()
        models.RecipeIngredient.objects.filter(recipe=recipe).delete()
        models.Recipe.objects.filter(pk=recipe.pk).update(**validated_data)
        recipes_services.create_tags_in_recipe(tags, recipe)
        recipes_services.create_ingredients_in_recipe(ingredients, recipe)
        new_recipe = get_object_or_404(models.Recipe, pk=recipe.pk)
        new_recipe.image = image
        new_recipe.save()
        return new_recipe


class FilterListSerializer(serializers.ListSerializer):
    """
    ???????????????????????? ?????? ?????????????????? ???????????? ???????????????????? ???????????????? ?? ????????
    recipes ?????? ?????????????????????? ????????????????
    """
    def to_representation(self, data):
        value = self.context.get('request').query_params.get('recipes_limit')
        data = super().to_representation(data)
        if not value:
            return data
        try:
            return data[:int(value)]
        except ValueError:
            return data


class CompactRecipeSerializer(serializers.ModelSerializer):

    image = serializers.ReadOnlyField(source='image.url')

    class Meta:
        list_serializer_class = FilterListSerializer
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ExtendedUserSerializer(UserSerializer):

    recipes = CompactRecipeSerializer(read_only=True, many=True)

    recipes_count = serializers.IntegerField(
        read_only=True,
        source='recipes.count')

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')


class SubscribeUserSerializer(FlattenMixinSerializer,
                              serializers.ModelSerializer):
    user = ExtendedUserSerializer(read_only=True,
                                  source='subscribed')

    class Meta:
        model = Subscription
        fields = ('subscribed', 'subscriber', 'user')
        extra_kwargs = {
            'subscribed': {'write_only': True},
            'subscriber': {'write_only': True},
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('subscriber', 'subscribed')),
        ]
        # ???????? ??????????????????????????, ?????????????????? ??????????????
        # ???????????????? ???????? ?????????????? "????????????????"
        flatten = ('user',)

    def validate_subscribed(self, value):
        if value == self.context.get('request').user:
            raise serializers.ValidationError(
                '???????????? ?????????????????????? ???? ???????????? ????????!')
        return value

    def delete(self):
        data = self.initial_data
        subscription = Subscription.objects.filter(
            subscriber=data['subscriber'],
            subscribed=data['subscribed']
        )
        if not subscription.exists():
            raise serializers.ValidationError(
                '???????????? - ?????????? ???????????????? ???? ????????????????????')
        subscription.delete()


class ShoppingCartSerializer(FlattenMixinSerializer,
                             serializers.ModelSerializer):

    recipe_compact = CompactRecipeSerializer(read_only=True,
                                             source='recipe')

    class Meta:
        model = models.ShoppingCart
        fields = ('recipe_compact', 'recipe', 'user')
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True},
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe')),
        ]
        # ???????? ??????????????????????????, ?????????????????? ??????????????
        # ???????????????? ???????? ?????????????? "????????????????"
        flatten = ('recipe_compact',)

    def delete(self):
        data = self.initial_data
        user_recipe = self.Meta.model.objects.filter(
            recipe=data['recipe'],
            user=data['user']
        )
        if not user_recipe.exists():
            raise serializers.ValidationError(
                '???????????? - ?????????? ???????????? ???? ????????????????????!')
        user_recipe.delete()


class FavoriteSerializer(ShoppingCartSerializer):

    class Meta(ShoppingCartSerializer.Meta):
        model = models.Favorite
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe')),
        ]
