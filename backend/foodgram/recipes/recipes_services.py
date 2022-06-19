# Модуль, в котором содержится логика работы приложения:
# обращения к БД, генерация отчетов и т.д.

import io
from collections import Iterable

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from recipes import models

from .models import Recipe

User = get_user_model()


def create_tags_in_recipe(tags: Iterable, recipe: Recipe) -> None:
    for tag in tags:
        models.RecipeTag.objects.create(
            recipe=recipe,
            tag=get_object_or_404(models.Tag, pk=tag.get('id')))
    return None


def create_ingredients_in_recipe(
        ingredients: Iterable, recipe: Recipe) -> None:
    for ingredient_in_recipe in ingredients:
        models.RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=get_object_or_404(
                models.Ingredient, pk=ingredient_in_recipe.get('id')),
            amount=ingredient_in_recipe.get('amount'))
    return None


def get_txt_report(request, filename: str) -> HttpResponse:
    """
    Генерация списка покупок в TXT
    """
    text = 'СПИСОК ПОКУПОК:'
    shopping_list = _get_shopping_list(request.user)
    num = 1
    for ingredient in shopping_list:
        ingredient_amount = (f'{num}. {ingredient.name.capitalize()} - '
                             f'{ingredient.shop_amount} '
                             f'{ingredient.measurement_unit}.')
        text += f'\n{ingredient_amount}'
        num += 1
    response = HttpResponse(text, content_type='text/plain; charset=utf8')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def get_pdf_report(request, filename: str) -> FileResponse:
    """
    Генерация списка покупок в PDF.
    TODO: Некорректно отображается кириллица,
    несмотря на попытки исправить кодировки с помощью регистрации TTF-шрифтов
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
    pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
    pdfmetrics.registerFont(TTFont('VeraIt', 'VeraIt.ttf'))
    pdfmetrics.registerFont(TTFont('VeraBI', 'VeraBI.ttf'))
    pdf.setFont('Vera', 16)
    shopping_list = _get_shopping_list(request.user)
    textobject = pdf.beginText(2 * cm, 29.7 * cm - 2 * cm)
    textobject.textLine('SHOPPING LIST:')

    num = 1
    for ingredient in shopping_list:
        ingredient_amount = (f'{num}. {ingredient.name.capitalize()} - '
                             f'{ingredient.shop_amount} '
                             f'{ingredient.measurement_unit}.')
        textobject.textLine(ingredient_amount)
        num += 1

    pdf.drawText(textobject)
    pdf.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=filename)


def _get_shopping_list(user: User) -> Iterable:
    """
    Получение списка покупок пользователя из БД.
    """
    return models.Ingredient.objects.filter(
        recipes__recipe__in=user.shopping_cart.values_list(
            'recipe', flat=True)
    ).annotate(shop_amount=Sum('recipes__amount'))


def get_user_favorite_recipes(user: User) -> Iterable:
    return models.Recipe.objects.filter(
        id__in=user.favorites.all().values_list(
            'recipe', flat=True)
    )


def get_user_shopping_cart_recipes(user: User) -> Iterable:
    return models.Recipe.objects.filter(
        id__in=user.shopping_cart.values_list(
            'recipe', flat=True)
    )
