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

class IsAdminOrOwner(permissions.BasePermission):
    """
    Hanya Owner atau Admin yang bisa akses. Kasir TIDAK termasuk.
    Dipakai untuk endpoint CMS (homepage, bento, gallery) yang di
    frontend memang cuma ditampilkan ke owner & admin.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['owner', 'admin']

        return False