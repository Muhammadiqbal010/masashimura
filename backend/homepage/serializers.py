import re
from rest_framework import serializers
from .models import HomepageConfig, BentoFacility, GalleryLookbook, PromoItem

# Teks: null -> "" (kolomnya tidak boleh NULL)
PROMO_TEXT_FIELDS = (
    "promo_badge", "promo_title", "promo_text",
    "promo_link", "promo_link_label", "promo_image_alt",
)
# Pilihan/angka/boolean: kalau kosong/null, abaikan saja (pakai nilai lama/default)
PROMO_SKIP_IF_EMPTY = (
    "promo_image_ratio", "promo_layout", "promo_image_side", "promo_focus",
    "promo_theme", "promo_align", "promo_overlay", "promo_countdown", "promo_dismissible",
)
# Tanggal: "" -> None
PROMO_DATE_FIELDS = ("promo_from", "promo_until")


class HomepageConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomepageConfig
        fields = '__all__'

    def to_internal_value(self, data):
        # Rapikan input dari frontend sebelum divalidasi
        data = data.copy()
        for field in PROMO_TEXT_FIELDS:
            if field in data and data[field] is None:
                data[field] = ""
        for field in PROMO_SKIP_IF_EMPTY:
            if field in data and data[field] in (None, ""):
                del data[field]
        for field in PROMO_DATE_FIELDS:
            if field in data and data[field] in (None, ""):
                data[field] = None
        if "promo_image" in data and data["promo_image"] == "":
            data["promo_image"] = None
        return super().to_internal_value(data)

    def validate_promo_link(self, value):
        value = (value or "").strip()
        if not value:
            return ""
        # Link internal: "/menu", "/contact" (bukan "//situs-lain.com")
        if value.startswith("/") and not value.startswith("//"):
            return value
        # Link luar: hanya http(s). Skema seperti javascript: ditolak.
        if re.match(r"^https?://\S+$", value, re.IGNORECASE):
            return value
        raise serializers.ValidationError(
            "Link harus diawali '/' (halaman sendiri) atau 'http://' / 'https://' (link luar)."
        )

    def validate(self, attrs):
        start = attrs.get("promo_from", getattr(self.instance, "promo_from", None))
        end = attrs.get("promo_until", getattr(self.instance, "promo_until", None))
        if start and end and start > end:
            raise serializers.ValidationError(
                {"promo_until": "Tanggal selesai tidak boleh sebelum tanggal mulai."}
            )
        return attrs


# ── Promo & Event (banyak item) ─────────────────────────────────────
PROMOITEM_TEXT_FIELDS = ("badge", "title", "text", "link", "link_label", "image_alt")
PROMOITEM_SKIP_IF_EMPTY = (
    "image_ratio", "layout", "image_side", "focus", "theme", "align",
    "overlay", "countdown", "dismissible", "order",
)
PROMOITEM_DATE_FIELDS = ("show_from", "show_until")


class PromoItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoItem
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def to_internal_value(self, data):
        data = data.copy()
        for f in PROMOITEM_TEXT_FIELDS:
            if f in data and data[f] is None:
                data[f] = ""
        for f in PROMOITEM_SKIP_IF_EMPTY:
            if f in data and data[f] in (None, ""):
                del data[f]
        for f in PROMOITEM_DATE_FIELDS:
            if f in data and data[f] in (None, ""):
                data[f] = None
        if "image" in data and data["image"] == "":
            data["image"] = None
        return super().to_internal_value(data)

    def validate_link(self, value):
        value = (value or "").strip()
        if not value:
            return ""
        if value.startswith("/") and not value.startswith("//"):
            return value
        if re.match(r"^https?://\S+$", value, re.IGNORECASE):
            return value
        raise serializers.ValidationError(
            "Link harus diawali '/' (halaman sendiri) atau 'http://' / 'https://' (link luar)."
        )

    def validate(self, attrs):
        def get(k):
            return attrs.get(k, getattr(self.instance, k, None))
        if not (get("title") or get("text") or get("image")):
            raise serializers.ValidationError({"title": "Isi minimal judul, keterangan, atau gambar."})
        start, end = get("show_from"), get("show_until")
        if start and end and start > end:
            raise serializers.ValidationError(
                {"show_until": "Tanggal selesai tidak boleh sebelum tanggal mulai."}
            )
        return attrs


class BentoFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BentoFacility
        fields = '__all__'


class GalleryLookbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryLookbook
        fields = '__all__'