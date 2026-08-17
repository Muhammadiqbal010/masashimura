# accounts/urls.py
from django.urls import path
from .views import LoginView, create_user_view, ChangePasswordView, UpdateUsernameView, UserProfileUpdateView

urlpatterns = [
    path('login/', LoginView.as_view(), name='api-login'),
    path('users/create/', create_user_view, name='api-create-user'),
    path('register-internal/', create_user_view, name='api-register-internal'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='api-profile-update'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='api-change-password'),
    path('profile/update-username/', UpdateUsernameView.as_view(), name='api-update-username'),
]