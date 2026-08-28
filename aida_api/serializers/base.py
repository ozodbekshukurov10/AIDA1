"""
AIDA Enterprise API — Base Serializer
"""
from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Barcha AIDA serializerlar uchun asos sinf.
    
    Qo'shimcha fieldlar:
    - created_at: Yaratilgan sana
    - updated_at: Yangilangan sana
    """
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        abstract = True
        fields = "__all__"

    def validate(self, attrs):
        """Umumiy tekshirish."""
        return super().validate(attrs)

    def create(self, validated_data):
        """Yaratish."""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Yangilash."""
        return super().update(instance, validated_data)


class ReadableStringRelatedField(serializers.StringRelatedField):
    """O'qiladigan string related field."""
    pass


class TimestampField(serializers.DateTimeField):
    """Timestamp formatidagi sana field."""
    format = "%Y-%m-%dT%H:%M:%SZ"
    read_only = True
