from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication

from .models import UserProfile
from .serializers import (
    UserCreateSerializer, LoginSerializer, ChangePasswordSerializer,
    ResetPasswordSerializer, StaffListSerializer, AdminSetPinSerializer,
)
from .permissions import IsOwner


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        login_input = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        if not login_input or not password:
            return Response(
                {"non_field_errors": ["Username/Email dan password wajib diisi."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_obj = None
        try:
            if '@' in login_input:
                user_obj = User.objects.filter(email=login_input).first()
            if not user_obj:
                user_obj = User.objects.filter(username=login_input).first()
        except Exception as e:
            print(f"Error query user: {e}")

        user = user_obj if (user_obj and user_obj.check_password(password)) else None

        if not user:
            return Response(
                {"non_field_errors": ["Username/Email atau password salah."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.is_active:
            return Response(
                {"non_field_errors": ["Akun ini sudah dinonaktifkan."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, _ = Token.objects.get_or_create(user=user)

        if user.is_superuser:
            role = 'owner'
        elif user.is_staff:
            role = 'admin'
        elif hasattr(user, 'userprofile'):
            role = user.userprofile.role
        elif hasattr(user, 'profile'):
            role = user.profile.role
        else:
            role = 'kasir'

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'role': role
            }
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwner])
def create_user_view(request):
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": f"Staff {user.username} berhasil didaftarkan!"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Dipakai UserProfile.vue. Verifikasi: password lama ATAU PIN
    (logic OR-nya ada di ChangePasswordSerializer.validate()).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password berhasil diperbarui!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        new_username = request.data.get('username')
        if not new_username:
            return Response({"username": ["Username baru wajib diisi."]}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
            return Response({"username": ["Username ini udah dipake orang lain. Cari nama lain!"]}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.username = new_username
        user.save()
        return Response({"message": "Username berhasil diganti!", "username": user.username}, status=status.HTTP_200_OK)


class UserProfileUpdateView(APIView):
    """
    HANYA buat update username/email. Ganti password TIDAK lewat sini
    lagi — dulu endpoint ini bisa dipakai buat set_password() tanpa
    verifikasi password lama sama sekali (celah keamanan). Sekarang
    ganti password wajib lewat ChangePasswordView yang minta verifikasi.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        username = data.get('username')
        email = data.get('email')

        if username and username != user.username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({"username": ["Username ini udah dipake orang lain."]}, status=status.HTTP_400_BAD_REQUEST)
            user.username = username

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({"email": ["Email ini sudah terdaftar di akun lain."]}, status=status.HTTP_400_BAD_REQUEST)
            user.email = email

        user.save()

        return Response({
            "message": "Profil berhasil diperbarui!",
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.get_full_name() or user.username,
                "email": user.email,
            }
        }, status=status.HTTP_200_OK)


class ResetPasswordThrottle(AnonRateThrottle):
    scope = 'reset_password'


class ResetPasswordWithPinView(APIView):
    """
    Dipakai Login.vue (modal 'Lupa password') — user belum login,
    jadi wajib sebutin username. Verifikasi identitas: password lama
    ATAU PIN keamanan (salah satu cukup).
    """
    permission_classes = [AllowAny]
    throttle_classes = [ResetPasswordThrottle]

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username     = serializer.validated_data['username']
        old_password = (serializer.validated_data.get('old_password') or '').strip()
        security_pin = (serializer.validated_data.get('security_pin') or '').strip()
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(username=username)
            profile = user.profile
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            # Pesan generic — jangan bedain "user gak ada" vs "kredensial salah"
            return Response({"detail": "Username, password lama, atau PIN salah."}, status=status.HTTP_400_BAD_REQUEST)

        verified = (old_password and user.check_password(old_password)) or \
                   (security_pin and profile.check_pin(security_pin))

        if not verified:
            return Response({"detail": "Username, password lama, atau PIN salah."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password berhasil direset."}, status=status.HTTP_200_OK)


class StaffListView(APIView):
    """Cuma owner yang boleh liat daftar staff lengkap dengan status PIN-nya."""
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        staff_users = User.objects.filter(
            profile__role__in=['owner', 'admin', 'kasir']
        ).select_related('profile').order_by('username')
        return Response(StaffListSerializer(staff_users, many=True).data)


class AdminSetPinView(APIView):
    """
    Owner set ulang PIN staff — gak perlu tau PIN lama sama sekali,
    karena owner udah terverifikasi lewat sesi login dia sendiri.
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request):
        serializer = AdminSetPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            target_user = User.objects.get(pk=serializer.validated_data['user_id'])
            profile = target_user.profile
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            return Response({"detail": "Staff tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

        profile.set_pin(serializer.validated_data['new_pin'])
        profile.save()

        return Response({
            "message": f"PIN untuk {target_user.username} berhasil di-reset. Beritahu PIN baru ini ke staff secara langsung."
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwner])
def admin_reset_password_view(request):
    """
    Owner reset password staff langsung, tanpa email/OTP — karena
    yang ngelakuin ini udah pasti owner yang sudah login & terverifikasi.
    """
    user_id = request.data.get('user_id')
    new_password = request.data.get('new_password')

    if not user_id or not new_password:
        return Response({"detail": "user_id dan new_password wajib diisi."}, status=status.HTTP_400_BAD_REQUEST)
    if len(new_password) < 6:
        return Response({"detail": "Password baru minimal 6 karakter."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"detail": "Staff tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

    target_user.set_password(new_password)
    target_user.save()

    return Response({"message": f"Password {target_user.username} berhasil di-reset oleh owner."}, status=status.HTTP_200_OK)