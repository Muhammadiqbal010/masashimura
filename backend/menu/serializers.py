from rest_framework import serializers
from .models import Menu, Category
from .options import clean_options, OptionError


class CategorySerializer(serializers.ModelSerializer):
    menu_count = serializers.IntegerField(source="menu_set.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "group", "menu_count"]


class MenuSerializer(serializers.ModelSerializer):
    """Serializer staff (ManageMenus, New Order). Boleh lihat price asli, is_secret, dll."""
    category       = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), allow_null=True, required=False
    )
    category_name  = serializers.SerializerMethodField()
    category_group = serializers.SerializerMethodField()
    image          = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image_url      = serializers.SerializerMethodField(read_only=True)
    price_web      = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)

    # Dari FormData, options datang sebagai string JSON; JSONField DRF otomatis mem-parse-nya.
    options        = serializers.JSONField(required=False)

    class Meta:
        model  = Menu
        fields = [
            "id", "name", "price", "price_web",
            "category", "category_name", "category_group",
            "description", "image", "image_url",
            "is_available", "is_active",
            "is_recommended", "is_secret", "options",
        ]

    def validate_options(self, value):
        try:
            return clean_options(value)
        except OptionError as e:
            raise serializers.ValidationError(str(e))

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_category_group(self, obj):
        return obj.category.group if obj.category else None

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


class PublicMenuSerializer(serializers.ModelSerializer):
    """Serializer publik. 'price' dan 'is_secret' SENGAJA tidak dimasukin."""
    category_name  = serializers.SerializerMethodField()
    category_group = serializers.SerializerMethodField()
    image_url      = serializers.SerializerMethodField(read_only=True)
    price_web      = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)

    class Meta:
        model  = Menu
        fields = [
            "id", "name", "price_web",
            "category", "category_name", "category_group",
            "description", "image_url",
            "is_available", "is_active",
            "is_recommended", "options",
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_category_group(self, obj):
        return obj.category.group if obj.category else None

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None