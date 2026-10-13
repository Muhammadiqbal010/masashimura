from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication

from django.db import transaction
from django.db.models import Max

from .models import HomepageConfig, BentoFacility, GalleryLookbook, PromoItem, PROMO_MAX_ITEMS
from .serializers import (
    HomepageConfigSerializer,
    BentoFacilitySerializer,
    GalleryLookbookSerializer,
    PromoItemSerializer,
)
from accounts.permissions import IsAdminOrOwner


# =========================================================
# CATATAN POLA
# - Endpoint GET yang dipakai halaman Home (publik):
#     authentication_classes = []  -> token basi diabaikan, gak bikin 401
#     permission_classes = [AllowAny]
# - Endpoint tulis (POST/PUT/DELETE) untuk CMS:
#     TokenAuthentication + IsAdminOrOwner
# =========================================================


class PublicReadMixin:
    """GET terbuka untuk semua pengunjung."""
    authentication_classes = []
    permission_classes = [AllowAny]


# ---------------------------------------------------------
# 1. CMS CONFIG (HERO, ABOUT, METRICS)
# ---------------------------------------------------------
class CurrentHomepageConfigView(PublicReadMixin, APIView):
    def get(self, request):
        config = HomepageConfig.objects.first()
        if not config:
            # Jangan bikin record dari request anonim.
            # Balas nilai default; record dibuat saat admin pertama kali simpan.
            return Response(HomepageConfigSerializer(HomepageConfig()).data, status=200)
        return Response(HomepageConfigSerializer(config).data, status=200)


class UpdateHomepageConfigView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def post(self, request):
        config = HomepageConfig.objects.first()
        if not config:
            config = HomepageConfig.objects.create()
        serializer = HomepageConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


# ---------------------------------------------------------
# 1b. PROMO & EVENT (maks PROMO_MAX_ITEMS)
# ---------------------------------------------------------
class PromoListView(PublicReadMixin, APIView):
    def get(self, request):
        items = PromoItem.objects.all().order_by("order", "id")
        return Response(PromoItemSerializer(items, many=True).data, status=200)


class PromoCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def post(self, request):
        with transaction.atomic():
            if PromoItem.objects.count() >= PROMO_MAX_ITEMS:
                return Response(
                    {"detail": f"Maksimal {PROMO_MAX_ITEMS} promo. Hapus salah satu dulu."},
                    status=400,
                )
            serializer = PromoItemSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=400)
            last = PromoItem.objects.aggregate(m=Max("order"))["m"]
            serializer.save(order=(last + 1) if last is not None else 0)
            return Response(serializer.data, status=201)


class PromoDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def get_object(self, pk):
        try:
            return PromoItem.objects.get(pk=pk)
        except PromoItem.DoesNotExist:
            return None

    def put(self, request, pk):
        item = self.get_object(pk)
        if not item:
            return Response({"detail": "Promo tidak ditemukan"}, status=404)
        serializer = PromoItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        item = self.get_object(pk)
        if not item:
            return Response({"detail": "Promo tidak ditemukan"}, status=404)
        item.delete()
        return Response({"message": "Promo berhasil dihapus"}, status=200)


class PromoReorderView(APIView):
    """Body: {"ids": [3, 1, 2]} -> urutan baru (index = order)."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def post(self, request):
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return Response({"detail": "ids harus berupa daftar angka."}, status=400)
        existing = set(PromoItem.objects.values_list("id", flat=True))
        if set(ids) != existing or len(ids) != len(existing):
            return Response({"detail": "Daftar ids tidak cocok dengan promo yang ada."}, status=400)
        with transaction.atomic():
            for pos, pk in enumerate(ids):
                PromoItem.objects.filter(pk=pk).update(order=pos)
        items = PromoItem.objects.all().order_by("order", "id")
        return Response(PromoItemSerializer(items, many=True).data, status=200)


# ---------------------------------------------------------
# 2. MODUL BENTO FACILITY DINAMIS
# ---------------------------------------------------------
class BentoFacilityListView(PublicReadMixin, APIView):
    def get(self, request):
        facilities = BentoFacility.objects.all().order_by("order")
        serializer = BentoFacilitySerializer(facilities, many=True)
        return Response(serializer.data, status=200)


class BentoFacilityCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def post(self, request):
        serializer = BentoFacilitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class BentoFacilityDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def get_object(self, pk):
        try:
            return BentoFacility.objects.get(pk=pk)
        except BentoFacility.DoesNotExist:
            return None

    def put(self, request, pk):
        facility = self.get_object(pk)
        if not facility:
            return Response({"error": "Fasilitas bento tidak ditemukan"}, status=404)
        serializer = BentoFacilitySerializer(facility, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        facility = self.get_object(pk)
        if not facility:
            return Response({"error": "Fasilitas bento tidak ditemukan"}, status=404)
        facility.delete()
        return Response({"message": "Fasilitas bento berhasil dihapus"}, status=200)


# ---------------------------------------------------------
# 3. MODUL GALLERY EVENT DINAMIS (WITH TITLE)
# ---------------------------------------------------------
class GalleryListView(PublicReadMixin, APIView):
    def get(self, request):
        gallery_items = GalleryLookbook.objects.all().order_by("-created_at")
        serializer = GalleryLookbookSerializer(gallery_items, many=True)
        return Response(serializer.data, status=200)


class GalleryCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def post(self, request):
        serializer = GalleryLookbookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class GalleryDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrOwner]

    def get_object(self, pk):
        try:
            return GalleryLookbook.objects.get(pk=pk)
        except GalleryLookbook.DoesNotExist:
            return None

    def put(self, request, pk):
        gallery_item = self.get_object(pk)
        if not gallery_item:
            return Response({"error": "Foto galeri tidak ditemukan"}, status=404)
        serializer = GalleryLookbookSerializer(gallery_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        gallery_item = self.get_object(pk)
        if not gallery_item:
            return Response({"error": "Foto galeri tidak ditemukan"}, status=404)
        # Logika pre_save/post_delete otomatis menghapus aset di Cloudinary
        gallery_item.delete()
        return Response({"message": "Foto galeri & event berhasil dihapus"}, status=200)


# ---------------------------------------------------------
# 4. REVIEW GOOGLE MAPS
# ---------------------------------------------------------
class GoogleMapsReviewsView(PublicReadMixin, APIView):
    def get(self, request):
        reviews_data = [
            {"name": "Deny Yusuf Akbar", "status": "Local Guide", "text": "Cozy place, like Izakaya in Japan. Cheap food, very delicious especially Mie Jebew with Chili oil."},
            {"name": "rifky aziz", "status": "Local Guide", "text": "Makanannya murah murah, rasanya mantul, pelayanan cepat, ada wifinya, cocok buat nobar."},
            {"name": "Issa Xander", "status": "Local Guide", "text": "Tempat Nya asik full musik juga. Ayam goreng sama Milkshake nya mantap."},
            {"name": "nabil khalid", "status": "Customer", "text": "Tempaaat rekomendassiii bangettt daah, gabakall nyesel, mao ajak pacar, rekanan jugaaa bisaa bangetttt!"},
            {"name": "ayimuhammad taupik", "status": "Customer", "text": "Harga merakyat, makanannya enak, ada wifinya lagi. Recomended buat tempat nongkrong."},
            {"name": "Fajri Azhari", "status": "Customer", "text": "Tempat nongkrong rekomendasi, harga terjangkau, makanan nya juga enak, tempat nya bersih, pelayan nya oke, gass keun kesini."},
            {"name": "Muhamad Riandy", "status": "Customer", "text": "Solusi nongkrong hemat budget, harga kaki lima rasa bintang 5."},
            {"name": "Ceplik -_-", "status": "Customer", "text": "Tempatnya asik, bersih, nyaman. Serta harga murah juga euy."},
            {"name": "Zyss", "status": "Customer", "text": "Mantap, paling cocok buat nongkrong."},
            {"name": "joss tv", "status": "Customer", "text": "Tempat nya orang santuy."},
        ]
        return Response(reviews_data, status=200)