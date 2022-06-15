from django.contrib.auth import get_user_model
from djoser.serializers import SetPasswordSerializer
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as django_filters
from rest_framework import permissions, filters
from django.db.models import Sum
import io
import os
from django.conf import settings
from django.http import FileResponse, HttpResponse
from reportlab.pdfgen import canvas
import reportlab.rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFont
from recipes import models
from . import serializers, filters
from django.db.models.functions import Lower


User = get_user_model()


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):

    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = (permissions.AllowAny,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateUserSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.action == 'subscribe':
            return serializers.SubscribeUserSerializer
        return serializers.UserSerializer

    @action(['get'], detail=False)
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(['post'], detail=False)
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, pk=None):
        subscribed = self.get_object()
        serializer = self.get_serializer(
            data={
                'subscriber': request.user.pk,
                'subscribed': subscribed.pk
            }
        )
        if request.method != 'POST':
            serializer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(['get'], detail=False)
    def subscriptions(self, request):
        subscriptions = [subscription.subscribed
                         for subscription
                         in request.user.subscriptions.all()]
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(
            self.get_serializer(subscriptions, many=True).data
        )

# TODO: настроить пермишены


# TODO: сделать общие миксины
class ReadOnlyAnyNoPaginationMixin(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(ReadOnlyAnyNoPaginationMixin):
    # TODO: проверить поиск при подключении Postgres
    queryset = models.Ingredient.objects.all().order_by(Lower('name'))
    serializer_class = serializers.IngredientSerializer
    filter_backends = (django_filters.DjangoFilterBackend,)
    filter_class = filters.IngredientFilter


class TagViewSet(ReadOnlyAnyNoPaginationMixin):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    filter_backends = (django_filters.DjangoFilterBackend,)
    filter_class = filters.RecipeFilter

    def get_serializer_class(self):
        if self.action == 'shopping_cart':
            return serializers.ShoppingCartSerializer
        if self.action == 'favorite':
            return serializers.FavoriteSerializer
        return serializers.RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        """
        Добавить/удалить рецепт из списка покупок
        """
        return self._add_shopping_card_or_favorite(request)

    @action(['post', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        """
        Добавить/удалить рецепт из избранного
        """
        return self._add_shopping_card_or_favorite(request)

    @action(detail=False)
    def download_shopping_cart(self, request):
        """
        Загрузка списка покупок.
        Доступно 2 режима: pdf и txt.
        Для выбора режима надо указать соответствующее расширение
        в имени файла.
        По дефолту - txt
        """
        FILENAME = 'shopping_list.txt'
        response = {
            'txt': get_txt_report(request, FILENAME),
            'pdf': get_pdf_report(request, FILENAME)
        }
        extension = FILENAME.split('.')[-1]
        return response.get(extension, get_txt_report(request, FILENAME))

    def _add_shopping_card_or_favorite(self, request):
        """
        Общий метод для добавления (либо удаления)
        в избранное либо список покупок
        """
        recipe = self.get_object()
        serializer = self.get_serializer(
            data={
                'recipe': recipe.pk,
                'user': request.user.pk
            }
        )
        if request.method != 'POST':
            serializer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def get_txt_report(request, filename):
    """
    Генерация списка покупок в TXT
    """
    text = 'СПИСОК ПОКУПОК:'
    shopping_list = get_shopping_list(request.user)
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


def get_pdf_report(request, filename):
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
    shopping_list = get_shopping_list(request.user)
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


def get_shopping_list(user):
    """
    Получение списка покупок пользователя из БД.
    """
    return models.Ingredient.objects.filter(
        recipes__recipe__in=user.shopping_cart.values_list(
            'recipe', flat=True)
    ).annotate(shop_amount=Sum('recipes__amount'))
