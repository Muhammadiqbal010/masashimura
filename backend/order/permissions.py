# order/permissions.py
from rest_framework import permissions

class IsStaffOrOwner(permissions.BasePermission):
    """
    Hanya Owner, Admin, atau Kasir yang dapat mengakses.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        is_owner = request.user.is_superuser
        has_valid_role = False
        if hasattr(request.user, 'profile'):
            if request.user.profile.role in ['owner', 'admin', 'kasir']:
                has_valid_role = True
        
        return is_owner or has_valid_role

class PublicReadStaffWrite(permissions.BasePermission):
    """
    Mengizinkan publik untuk membaca (GET), 
    tapi hanya staf (Owner/Admin/Kasir) untuk menulis/menghapus.
    """
    def has_permission(self, request, view):
        # Jika metode adalah GET/HEAD/OPTIONS, izinkan semua (Public Read)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Jika metode selain itu (POST/PUT/DELETE), lakukan validasi staf
        if not request.user or not request.user.is_authenticated:
            return False
            
        is_owner = request.user.is_superuser
        has_valid_role = False
        if hasattr(request.user, 'profile'):
            if request.user.profile.role in ['owner', 'admin', 'kasir']:
                has_valid_role = True
        
        return is_owner or has_valid_role