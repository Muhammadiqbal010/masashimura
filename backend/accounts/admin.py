from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Info'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_role', 'is_staff', 'is_superuser')
    
    def get_role(self, instance):
        return instance.profile.role if hasattr(instance, 'profile') else 'Pelanggan'
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)