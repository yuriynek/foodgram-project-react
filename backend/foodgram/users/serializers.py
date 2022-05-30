from rest_framework import serializers, validators
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Subscription


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed')
        read_only_fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, user):
        return user.subscribers.filter(
            subscriber=self.context.get('request').user
        ).exists()


class CreateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')
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


class SubscribeUserSerializer(serializers.ModelSerializer):
    # TODO: заменить на полный сериалайзер
    user = UserSerializer(read_only=True,
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_representation = representation.pop('user')
        for key in user_representation:
            representation[key] = user_representation[key]
        return representation

    def validate_subscribed(self, value):
        if value == self.context.get('request').user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!')
        return value

    def delete(self):
        data = self.initial_data
        subscription = Subscription.objects.filter(
            subscriber=data['subscriber'],
            subscribed=data['subscribed']
        )
        if not subscription.exists():
            raise serializers.ValidationError('Ошибка - такой подписки не существует')
        subscription.delete()
