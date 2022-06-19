from rest_framework import viewsets, permissions


class FlattenMixinSerializer:
    """
    "Делает плоскими" данные во вложенных сериализаторах.
    """
    def to_representation(self, instance):
        assert hasattr(self.Meta, 'flatten'), (
            f'В классе {self.__class__.__name__} '
            f'отсутствует атрибут "Meta.flatten"'
        )
        # Получаем текущее представление объекта (сериализатора)
        representation = super().to_representation(instance)
        # Проходимся по полям вложенного сериализатора,
        # которые нужно сделать "плоскими"
        for field in self.Meta.flatten:
            instance_representation = representation.pop(field)
            for key in instance_representation:
                representation[key] = instance_representation[key]
        return representation


class ReadOnlyAnyNoPaginationMixinViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
