from rest_framework import serializers, exceptions
import uuid
from django.core.files.base import ContentFile
import base64


class ImageFromBase64Field(serializers.ImageField):
    def to_internal_value(self, data):
        try:
            data_format, base64_string = data.split(';base64,')
            extension = data_format.split('/')[-1]
            image_id = uuid.uuid4()
            data = ContentFile(
                base64.b64decode(base64_string),
                name=f'{image_id}.{extension}'
            )
        except exceptions.APIException:
            raise serializers.ValidationError('Ошибка декодирования изображения')
        return super().to_internal_value(data)
