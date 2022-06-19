from django.contrib.auth import get_user_model
from collections import Iterable

User = get_user_model()


def get_user_subscriptions(user: User) -> Iterable:
    """
    Получить все подписки пользователя user
    """
    return User.objects.filter(
        id__in=user.subscriptions.all().values_list('subscribed', flat=True)
    )
