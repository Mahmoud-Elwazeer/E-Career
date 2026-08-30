from django.urls import path
from apps.accounts.views import (
    RegisterView,
    LoginView,
    LogoutView,
    TokenRefreshView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerifyView,
    ResendVerificationView,
    GoogleAuthView,
    GoogleCallbackView,
    MeView,
    ChangePasswordView,
    AdminUserListView,
    AdminUserDetailView,
)

app_name = "accounts"

urlpatterns = [
    # Core auth
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Password reset
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),

    # Email verification
    path("verify-email/<str:key>/", EmailVerifyView.as_view(), name="verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),

    # Social auth (Google)
    path("social/google/", GoogleAuthView.as_view(), name="social-google"),
    path("social/google/callback/", GoogleCallbackView.as_view(), name="social-google-callback"),

    # Profile & password (test-expected aliases)
    path("me/", MeView.as_view(), name="profile-detail"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),

    # Admin user management (test-expected)
    path("users/", AdminUserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", AdminUserDetailView.as_view(), name="user-detail"),
]
