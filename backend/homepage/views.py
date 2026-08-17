from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .models import HomepageConfig, BentoFacility, GalleryLookbook
from .serializers import HomepageConfigSerializer, BentoFacilitySerializer, GalleryLookbookSerializer

# ---------------------------------------------------------
# 1. CMS CONFIG (HERO, ABOUT, METRICS)
# ---------------------------------------------------------
class CurrentHomepageConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        config = HomepageConfig.objects.first()
        if not config:
            config = HomepageConfig.objects.create()
        serializer = HomepageConfigSerializer(config)
        return Response(serializer.data, status=200)

class UpdateHomepageConfigView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
# 🧱 2. MODUL BENTO FACILITY DINAMIS
# ---------------------------------------------------------
class BentoFacilityListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Ambil semua fasilitas bento diurutkan dari susunan order-nya
        facilities = BentoFacility.objects.all().order_by('order')
        serializer = BentoFacilitySerializer(facilities, many=True)
        return Response(serializer.data, status=200)

class BentoFacilityCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BentoFacilitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class BentoFacilityDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
# 📸 3. MODUL GALLERY EVENT DINAMIS (WITH TITLE)
# ---------------------------------------------------------
class GalleryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Ambil seluruh galeri event dari yang terupdate (paling baru dibuat)
        gallery_items = GalleryLookbook.objects.all().order_by('-created_at')
        serializer = GalleryLookbookSerializer(gallery_items, many=True)
        return Response(serializer.data, status=200)

class GalleryCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GalleryLookbookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class GalleryDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
class GoogleMapsReviewsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Ini adalah data review asli dari Google Maps yang lo kasih tadi
        reviews_data = [
            {"name": "Deny Yusuf Akbar", "status": "Local Guide", "text": "Cozy place, like Izakaya in Japan. Cheap food, very delicious especially Mie Jebew with Chili oil."},
            {"name": "rifky aziz", "status": "Local Guide", "text": "Makanannya murah murah, rasanya mantul, pelayanan cepat, ada wifinya, cocok buat nobar."},
            {"name": "Issa Xander", "status": "Local Guide", "text": "Tempat Nya asik full musik juga. Ayam goreng sama Milkshake nya mantap."},
            {"name": "nabil khalid", "status": "Customer", "text": "Tempaaat rekomendassiii bangettt daah, gabakall nyesel, mao ajak pacar, rekanan jugaaa bisaa bangetttt!"},
            {"name": "ayimuhammad taupik", "status": "Customer", "text": "Harga merakyat, makanannya enak, ada wifinya lagi. Recomended buat tempat nongkrong."},
            {"name": "Muhamad Riandy", "status": "Customer", "text": "Solusi nongkrong hemat budget, harga kaki lima rasa bintang 5."}
        ]
        return Response(reviews_data, status=200)