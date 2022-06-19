from rest_framework import permissions


class IsAuthorOrReadOnlyPermission(permissions.BasePermission):
    """Проверка. Если запрос только на чтение, то разрешаем его.
    Если пользователь авторизован - разрешает создание записи
    Если запрос на изменение - проверяем, является ли пользователь
    автором"""
    message = 'Права на изменение данного контента принадлежат автору'

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
