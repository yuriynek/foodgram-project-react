from django.db import models
from django.core import validators
from django.contrib.auth import get_user_model


User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название', max_length=200)
    color = models.CharField('Цвет', max_length=7)
    slug = models.SlugField('Слаг', max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=200)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField('Название', max_length=200)
    # TODO: подумать над огранизацией хранения и своевременного удаления изображения
    image = models.ImageField('Изображение', upload_to='images/%Y/%m/%d/')
    text = models.TextField('Текст')
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=(validators.MinValueValidator(limit_value=1),)
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True)
    author = models.ForeignKey(
        verbose_name='Автор',
        to=User,
        related_name='recipes',
        on_delete=models.CASCADE)
    tags = models.ManyToManyField(verbose_name='Теги', to=Tag, through='RecipeTag')
    ingredients = models.ManyToManyField(
        verbose_name='Ингредиенты', to=Ingredient, through='RecipeIngredient',)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(verbose_name='Рецепт', to=Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(verbose_name='Тег', to=Tag, on_delete=models.CASCADE)

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Рецепт-Тег'
        verbose_name_plural = 'Рецепты-Теги'
        # TODO: нужно ли данное ограничение
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='unique_recipe_tag'
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.tag}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        verbose_name='Рецепт', to=Recipe, on_delete=models.CASCADE,
        related_name='ingredients_in_recipe')
    ingredient = models.ForeignKey(
        verbose_name='Ингредиент', to=Ingredient, on_delete=models.CASCADE,
        related_name='recipes'
    )
    amount = models.IntegerField(
        'Количество ингредиента',
        validators=(validators.MinValueValidator(limit_value=0),)
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Рецепт-Ингредиент'
        verbose_name_plural = 'Рецепты-Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'


class Favorite(models.Model):
    user = models.ForeignKey(
        verbose_name='Пользователь', to=User, on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        verbose_name='Рецепт', to=Recipe, on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранное'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        verbose_name='Пользователь', to=User, on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        verbose_name='Рецепт', to=Recipe, on_delete=models.CASCADE,
        related_name='shopping_recipes'
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Список покупок'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_shopping'
            )
        ]

