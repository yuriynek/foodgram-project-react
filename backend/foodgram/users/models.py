from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    email = models.EmailField('Email', unique=True)


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscribed = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('subscriber', 'subscribed'),
                name='unique_subscriber_subscribed'
            )
        ]
