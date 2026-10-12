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


def _profile_role(user):
    """Role dari UserProfile ('owner'/'admin'/'kasir'/'pelanggan') atau None."""
    profile = getattr(user, 'profile', None)
    return getattr(profile, 'role', None)


class IsStaffLevel(permissions.BasePermission):
    """
    Semua staff: owner, admin, kasir. Dipakai endpoint operasional (POS, tagihan,
    pesanan aktif). Pengganti IsAdminUser, yang hanya mengecek is_staff padahal
    akun staff buatan form Staff tidak pernah diberi is_staff. Akun is_staff /
    superuser yang sudah ada tetap lolos, jadi tidak ada yang kehilangan akses.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return _profile_role(user) in ('owner', 'admin', 'kasir')


class IsAdminLevel(permissions.BasePermission):
    """
    Owner atau admin saja (kasir TIDAK termasuk). Dipakai laporan, statistik,
    keuangan, pengaturan, dan prediksi. Pengganti IsAdminUser (lihat IsStaffLevel).
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return _profile_role(user) in ('owner', 'admin')