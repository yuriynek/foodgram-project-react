from django.contrib.auth import get_user_model
from djoser.serializers import SetPasswordSerializer
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as django_filters
from rest_framework import permissions
from recipes import models
from users.users_services import get_user_subscriptions
from . import serializers, filters
from django.db.models import Count
from django.db.models.functions import Lower
from recipes.recipes_services import (get_txt_report, get_pdf_report)
from .mixins import ReadOnlyAnyNoPaginationMixinViewSet
from .permissions import IsAuthorOrReadOnlyPermission

User = get_user_model()


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):

    queryset = User.objects.annotate(recipes_count=Count('recipes'))

    def get_permissions(self):
        if (self.action not in (
                'me', 'set_password', 'subscribe', 'subscriptions')
                and self.request.method in permissions.SAFE_METHODS):
            self.permission_classes = (permissions.AllowAny,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateUserSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.action == 'subscribe':
            return serializers.SubscribeUserSerializer
        if self.action == 'subscriptions':
            return serializers.ExtendedUserSerializer
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
        subscriptions = get_user_subscriptions(request.user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(
            self.get_serializer(subscriptions, many=True).data
        )


class IngredientViewSet(ReadOnlyAnyNoPaginationMixinViewSet):
    queryset = models.Ingredient.objects.all().order_by(Lower('name'))
    serializer_class = serializers.IngredientSerializer
    filter_backends = (django_filters.DjangoFilterBackend,)
    filter_class = filters.IngredientFilter


class TagViewSet(ReadOnlyAnyNoPaginationMixinViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    filter_backends = (django_filters.DjangoFilterBackend,
                       filters.LimitRecipesFilterBackend
                       )
    filter_class = filters.RecipeFilter

    def get_serializer_class(self):
        if self.action == 'shopping_cart':
            return serializers.ShoppingCartSerializer
        if self.action == 'favorite':
            return serializers.FavoriteSerializer
        return serializers.RecipeSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            self.permission_classes = (permissions.AllowAny,)
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            self.permission_classes = (IsAuthorOrReadOnlyPermission,)
        return super().get_permissions()

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
