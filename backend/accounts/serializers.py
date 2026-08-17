from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    full_name = serializers.CharField(required=False, allow_blank=True)  # ← tambah ini

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'full_name']  # ← tambah full_name

    def create(self, validated_data):
        role      = validated_data.pop('role')
        full_name = validated_data.pop('full_name', '')          # ← ambil & hapus dari data
        user      = User.objects.create_user(**validated_data)
        
        # Pecah full_name ke first_name & last_name (Django User standar)
        if full_name:
            parts = full_name.strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name  = parts[1] if len(parts) > 1 else ''
            user.save()
        
        UserProfile.objects.create(user=user, role=role)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password lama lo salah.")
        return value

    def validate(self, data):
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError("Password baru gak boleh sama dengan password lama.")
        return data