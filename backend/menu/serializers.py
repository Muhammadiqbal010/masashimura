from rest_framework import serializers
from django.db import transaction

from . import bundles as bundle_logic
from .models import Menu, Category, MenuBundle, MenuBundleItem
from .options import clean_options, OptionError


class CategorySerializer(serializers.ModelSerializer):
    # Nilai dari annotate(Count) di CategoryViewSet. Kalau serializer dipakai tanpa
    # annotate (mis. respons POST), baru jatuh ke hitung manual.
    menu_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "group", "menu_count"]

    def get_menu_count(self, obj):
        annotated = getattr(obj, "menu_count", None)
        return annotated if annotated is not None else obj.menu_set.count()


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

    def validate_price(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Harga harus lebih dari 0.")
        return value

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
            "is_recommended", "options", "created_at",
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_category_group(self, obj):
        return obj.category.group if obj.category else None

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None


# ─────────────────────────────────────────────
# MENU PAKET
# ─────────────────────────────────────────────

def _has_required_option(menu):
    return any(isinstance(g, dict) and g.get("required") for g in (menu.options or []))


class BundleItemInputSerializer(serializers.Serializer):
    menu = serializers.PrimaryKeyRelatedField(queryset=Menu.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=20, default=1)


class BundleSerializer(serializers.ModelSerializer):
    """Serializer staff: baca (harga POS + harga web) dan tulis (nama, menu + jumlah, harga paket)."""
    items = BundleItemInputSerializer(many=True, write_only=True)
    contents = serializers.SerializerMethodField()
    pos = serializers.SerializerMethodField()
    web = serializers.SerializerMethodField()
    unavailable_reason = serializers.SerializerMethodField()

    class Meta:
        model = MenuBundle
        fields = [
            "id", "name", "description", "price", "is_available",
            "items", "contents", "pos", "web", "unavailable_reason",
        ]

    def get_contents(self, obj):
        return [
            {"menu": i.menu_id, "name": i.menu.name, "quantity": i.quantity,
             "price": int(i.menu.price), "is_available": i.menu.is_available, "is_active": i.menu.is_active}
            for i in obj.items.all()
        ]

    def get_pos(self, obj):
        return bundle_logic.pricing(obj, "pos")

    def get_web(self, obj):
        return bundle_logic.pricing(obj, "web")

    def get_unavailable_reason(self, obj):
        return bundle_logic.unavailable_reason(obj, "pos")

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Nama paket wajib diisi.")
        return value

    def validate_price(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Harga paket harus lebih dari 0.")
        return value

    def validate_items(self, rows):
        if not rows:
            raise serializers.ValidationError("Paket minimal berisi satu menu.")
        seen = set()
        for row in rows:
            menu = row["menu"]
            if menu.pk in seen:
                raise serializers.ValidationError(f"{menu.name} dobel. Ubah jumlahnya saja.")
            seen.add(menu.pk)
            if menu.is_secret:
                raise serializers.ValidationError(f"{menu.name} adalah secret menu dan tidak bisa masuk paket.")
            if _has_required_option(menu):
                raise serializers.ValidationError(
                    f"{menu.name} punya pilihan wajib (mis. level pedas), belum bisa masuk paket."
                )
        if sum(r["quantity"] for r in rows) < 2:
            raise serializers.ValidationError("Paket minimal berisi 2 porsi (mis. 2 menu berbeda).")
        return rows

    def _save_items(self, bundle, rows):
        bundle.items.all().delete()
        MenuBundleItem.objects.bulk_create(
            [MenuBundleItem(bundle=bundle, menu=r["menu"], quantity=r["quantity"]) for r in rows]
        )

    @transaction.atomic
    def create(self, validated):
        rows = validated.pop("items")
        bundle = MenuBundle.objects.create(**validated)
        self._save_items(bundle, rows)
        return bundle

    @transaction.atomic
    def update(self, instance, validated):
        rows = validated.pop("items", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if rows is not None:
            self._save_items(instance, rows)
        return instance


class PublicBundleSerializer(serializers.ModelSerializer):
    """Serializer publik: hanya angka web. Harga POS dan data staf tidak ikut keluar."""
    contents = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    normal_price = serializers.SerializerMethodField()
    savings = serializers.SerializerMethodField()
    unavailable_reason = serializers.SerializerMethodField()

    class Meta:
        model = MenuBundle
        fields = ["id", "name", "description", "contents", "price", "normal_price", "savings", "unavailable_reason"]

    def get_contents(self, obj):
        return [{"menu": i.menu_id, "name": i.menu.name, "quantity": i.quantity} for i in obj.items.all()]

    def _p(self, obj):
        return bundle_logic.pricing(obj, "web")

    def get_price(self, obj):
        return self._p(obj)["price"]

    def get_normal_price(self, obj):
        # Harga normal hanya ditampilkan kalau paket memang lebih murah.
        p = self._p(obj)
        return None if p["not_cheaper"] else p["normal_price"]

    def get_savings(self, obj):
        return self._p(obj)["savings"]

    def get_unavailable_reason(self, obj):
        return bundle_logic.unavailable_reason(obj, "web")
