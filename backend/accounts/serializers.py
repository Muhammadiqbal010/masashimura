from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    full_name = serializers.CharField(required=False, allow_blank=True)
    security_pin = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'full_name', 'security_pin']

    def validate_security_pin(self, value):
        if value and not (value.isdigit() and len(value) == 6):
            raise serializers.ValidationError("PIN harus 6 digit angka.")
        return value

    def create(self, validated_data):
        role         = validated_data.pop('role')
        full_name    = validated_data.pop('full_name', '')
        security_pin = validated_data.pop('security_pin', '')
        user         = User.objects.create_user(**validated_data)

        if full_name:
            parts = full_name.strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name  = parts[1] if len(parts) > 1 else ''
            user.save()

        profile = UserProfile.objects.create(user=user, role=role)
        if security_pin:
            profile.set_pin(security_pin)
            profile.save()

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Dipakai di UserProfile.vue — user UDAH LOGIN, verifikasi ulang
    identitasnya pakai SALAH SATU: password lama atau PIN keamanan.
    """
    old_password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    security_pin = serializers.CharField(required=False, allow_blank=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)

    def validate(self, data):
        user = self.context['request'].user
        old_password = (data.get('old_password') or '').strip()
        security_pin = (data.get('security_pin') or '').strip()

        if not old_password and not security_pin:
            raise serializers.ValidationError("Isi salah satu: password lama atau PIN keamanan.")

        verified = False
        if old_password and user.check_password(old_password):
            verified = True
        if not verified and security_pin and hasattr(user, 'profile') and user.profile.check_pin(security_pin):
            verified = True

        if not verified:
            raise serializers.ValidationError("Password lama atau PIN yang kamu masukkan salah.")

        if old_password and data['new_password'] == old_password:
            raise serializers.ValidationError("Password baru gak boleh sama dengan password lama.")

        return data


class ResetPasswordSerializer(serializers.Serializer):
    """
    Dipakai di Login.vue (modal 'Lupa password') — user BELUM LOGIN,
    jadi wajib sebutin username, verifikasi SALAH SATU: password lama
    atau PIN keamanan.
    """
    username     = serializers.CharField()
    old_password = serializers.CharField(required=False, allow_blank=True)
    security_pin = serializers.CharField(required=False, allow_blank=True)
    new_password = serializers.CharField(min_length=6)

    def validate(self, data):
        old_password = (data.get('old_password') or '').strip()
        security_pin = (data.get('security_pin') or '').strip()
        if not old_password and not security_pin:
            raise serializers.ValidationError("Isi salah satu: password lama atau PIN keamanan.")
        return data


class StaffListSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    full_name = serializers.SerializerMethodField()
    has_pin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'role', 'is_active', 'has_pin']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_has_pin(self, obj):
        # Cuma status "punya PIN apa nggak" — PIN aslinya gak pernah dikirim
        # ke frontend karena disimpan ter-hash (gak bisa "dibaca ulang").
        return bool(getattr(obj.profile, 'security_pin', ''))


class AdminSetPinSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    new_pin = serializers.CharField(min_length=6, max_length=6)

    def validate_new_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("PIN harus 6 digit angka.")
        return value