from django.urls import path
from .views import RegisterView, LoginView, LogoutView, CustomTokenRefreshView, MeView, UpdateProfileView, ChangePasswordView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/update-profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
]
