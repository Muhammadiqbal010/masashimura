from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication

from .serializers import UserCreateSerializer, LoginSerializer, ChangePasswordSerializer
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

        if user_obj and user_obj.check_password(password):
            user = user_obj
        else:
            user = None

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
    permission_classes = [IsAuthenticated]  # Wajib login

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {"message": "Password berhasil diperbarui!"}, 
                status=status.HTTP_200_OK
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2. VIEW UNTUK UBAH USERNAME
class UpdateUsernameView(APIView):
    permission_classes = [IsAuthenticated]  # Wajib login

    def post(self, request, *args, **kwargs):
        new_username = request.data.get('username')
        
        if not new_username:
            return Response(
                {"username": ["Username baru wajib diisi."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Cek apakah username sudah dipakai orang lain
        if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
            return Response(
                {"username": ["Username ini udah dipake orang lain . Cari nama lain!"]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = request.user
        user.username = new_username
        user.save()
        
        return Response({
            "message": "Username berhasil diganti!",
            "username": user.username
        }, status=status.HTTP_200_OK)

class UserProfileUpdateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]  # Wajib kirim token di header

    def put(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        # 1. Ambil input dari frontend
        username = data.get('username')
        email = data.get('email')
        new_password = data.get('password') or data.get('new_password')

        # 2. Validasi Username (jika diubah)
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response(
                    {"username": ["Username ini udah dipake orang lain, Bal."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.username = username

        # 3. Validasi Email (jika diubah)
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response(
                    {"email": ["Email ini sudah terdaftar di akun lain."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email = email

        # 4. Validasi & Set Password Baru (jika user ngisi kolom password)
        if new_password:
            user.set_password(new_password)

        # 5. Simpan perubahan ke database
        user.save()

        # 6. Return response payload sukses yang ramah buat Frontend Vue lo
        return Response({
            "message": "Profil berhasil diperbarui, Bal!",
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.get_full_name() or user.username,
                "email": user.email,
            }
        }, status=status.HTTP_200_OK)