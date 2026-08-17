# accounts/permissions.py
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Izin kustom: Hanya Owner (superuser) yang dapat mengakses.
    Digunakan untuk endpoint yang krusial seperti pembuatan user baru.
    """
    def has_permission(self, request, view):
        # Memastikan user sudah terautentikasi dan memiliki status superuser
        return bool(request.user and request.user.is_superuser)