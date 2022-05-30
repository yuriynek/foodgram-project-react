from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from django.contrib.auth import get_user_model
from . import serializers
from djoser.serializers import SetPasswordSerializer


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
