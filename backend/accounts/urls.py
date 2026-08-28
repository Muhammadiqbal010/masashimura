from django.urls import path
from .views import (
    LoginView, create_user_view, ChangePasswordView,
    UpdateUsernameView, UserProfileUpdateView,
    ResetPasswordWithPinView, StaffListView, AdminSetPinView,
    admin_reset_password_view,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='api-login'),
    path('users/create/', create_user_view, name='api-create-user'),
    path('register-internal/', create_user_view, name='api-register-internal'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='api-profile-update'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='api-change-password'),
    path('profile/update-username/', UpdateUsernameView.as_view(), name='api-update-username'),
    path('reset-password-pin/', ResetPasswordWithPinView.as_view(), name='api-reset-password-pin'),
    path('staff/list/', StaffListView.as_view(), name='api-staff-list'),
    path('staff/set-pin/', AdminSetPinView.as_view(), name='api-staff-set-pin'),
    path('admin/reset-password/', admin_reset_password_view, name='api-admin-reset-password'),
]