import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.accounts.models import User
from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserMeSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    AvatarUploadSerializer,
)
from apps.events.emitter import emit
from apps.events.types import (
    USER_REGISTERED, USER_LOGGED_IN, USER_LOGGED_OUT, USER_PROFILE_UPDATED
)

logger = logging.getLogger(__name__)


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@extend_schema(tags=["Auth"])
class RegisterView(APIView):
    """POST /api/v1/auth/register/ — Create a new user account."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserMeSerializer},
        summary="Register a new user",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
            # Emit USER_REGISTERED event
            try:
                emit(
                    event_type=USER_REGISTERED,
                    category="user",
                    user=user,
                    target_type="user",
                    target_id=str(user.id),
                    data={"email": user.email, "source": "register_view"},
                    request=request,
                )
            except Exception:
                pass
            tokens = get_tokens_for_user(user)
            user_data = UserMeSerializer(user, context={"request": request}).data
            return Response(
                {
                    "success": True,
                    "data": {"user": user_data, **tokens},
                    "message": "Account created successfully.",
                    "errors": None,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.exception("Registration error")
            return Response(
                {"success": False, "data": None, "message": str(e), "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(tags=["Auth"])
class LoginView(APIView):
    """POST /api/v1/auth/login/ — Login with email + password, receive JWT tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        request=LoginSerializer,
        summary="Login with email and password",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        # Emit USER_LOGGED_IN event
        try:
            emit(
                event_type=USER_LOGGED_IN,
                category="user",
                user=user,
                target_type="user",
                target_id=str(user.id),
                data={"source": "login_view"},
                request=request,
            )
        except Exception:
            pass
        tokens = get_tokens_for_user(user)
        user_data = UserMeSerializer(user, context={"request": request}).data
        return Response(
            {
                "success": True,
                "data": {"user": user_data, **tokens},
                "message": "Logged in successfully.",
                "errors": None,
            }
        )


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — Blacklist the refresh token."""

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Logout and invalidate refresh token")
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "data": None, "message": "Refresh token required.", "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            # Emit USER_LOGGED_OUT event
            try:
                emit(
                    event_type=USER_LOGGED_OUT,
                    category="user",
                    user=request.user,
                    target_type="user",
                    target_id=str(request.user.id),
                    data={"source": "logout_view"},
                    request=request,
                )
            except Exception:
                pass
        except TokenError as e:
            return Response(
                {"success": False, "data": None, "message": str(e), "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"success": True, "data": None, "message": "Logged out successfully.", "errors": None}
        )


@extend_schema(tags=["Auth"])
class TokenRefreshView(APIView):
    """POST /api/v1/auth/token/refresh/ — Get a new access token using a refresh token."""

    permission_classes = [AllowAny]

    @extend_schema(summary="Refresh access token")
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "data": None, "message": "Refresh token required.", "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            new_access = str(token.access_token)
            new_refresh = str(token)
            return Response(
                {
                    "success": True,
                    "data": {"access": new_access, "refresh": new_refresh},
                    "message": "Token refreshed.",
                    "errors": None,
                }
            )
        except TokenError as e:
            return Response(
                {"success": False, "data": None, "message": "Invalid or expired refresh token.", "errors": None},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@extend_schema(tags=["Auth"])
class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password/reset/ — Send a password reset email."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        request=PasswordResetRequestSerializer,
        summary="Request a password reset email",
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        # Always return 200 to avoid user enumeration
        try:
            user = User.objects.get(email=email, is_deleted=False)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
            reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"
            html_message = render_to_string(
                "emails/password_reset.html",
                {"user": user, "reset_link": reset_link},
            )
            send_mail(
                subject="Reset your USAM password",
                message=f"Click to reset your password: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass
        except Exception:
            logger.exception("Password reset email error")

        return Response(
            {
                "success": True,
                "data": None,
                "message": "If an account exists with that email, a reset link has been sent.",
                "errors": None,
            }
        )


@extend_schema(tags=["Auth"])
class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password/reset/confirm/ — Confirm password reset with token."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        summary="Confirm password reset",
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"success": False, "data": None, "message": "Invalid reset link.", "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response(
                {"success": False, "data": None, "message": "Reset link is invalid or has expired.", "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(
            {"success": True, "data": None, "message": "Password reset successfully.", "errors": None}
        )


@extend_schema(tags=["Users"])
class MeView(APIView):
    """GET/PATCH/DELETE /api/v1/users/me/ — Current user profile."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserMeSerializer}, summary="Get current user profile")
    def get(self, request):
        serializer = UserMeSerializer(request.user, context={"request": request})
        return Response(
            {"success": True, "data": serializer.data, "message": "", "errors": None}
        )

    @extend_schema(request=UserMeSerializer, responses={200: UserMeSerializer}, summary="Update profile")
    def patch(self, request):
        serializer = UserMeSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        # Emit USER_PROFILE_UPDATED event
        try:
            emit(
                event_type=USER_PROFILE_UPDATED,
                category="user",
                user=request.user,
                target_type="user",
                target_id=str(request.user.id),
                data={"source": "me_view", "fields": list(request.data.keys())},
                request=request,
            )
        except Exception:
            pass
        serializer.save()
        return Response(
            {"success": True, "data": serializer.data, "message": "Profile updated.", "errors": None}
        )

    @extend_schema(summary="Soft-delete current user account")
    def delete(self, request):
        request.user.soft_delete()
        return Response(
            {"success": True, "data": None, "message": "Account deleted.", "errors": None},
            status=status.HTTP_204_NO_CONTENT,
        )


@extend_schema(tags=["Users"])
class AvatarUploadView(APIView):
    """POST /api/v1/users/me/avatar/ — Upload a profile avatar."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=AvatarUploadSerializer,
        responses={200: UserMeSerializer},
        summary="Upload or replace avatar",
    )
    def post(self, request):
        serializer = AvatarUploadSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = UserMeSerializer(request.user, context={"request": request}).data
        return Response(
            {"success": True, "data": user_data, "message": "Avatar updated.", "errors": None}
        )


@extend_schema(tags=["Users"])
class ChangePasswordView(APIView):
    """POST /api/v1/users/me/change-password/ — Change password (requires current)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, summary="Change password")
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"success": True, "data": None, "message": "Password changed successfully.", "errors": None}
        )


@extend_schema(tags=["Auth"])
class EmailVerifyView(APIView):
    """GET /api/v1/auth/verify-email/<key>/ — Confirm email via allauth key."""

    permission_classes = [AllowAny]

    @extend_schema(summary="Verify email address")
    def get(self, request, key):
        from allauth.account.models import EmailConfirmationHMAC
        try:
            confirmation = EmailConfirmationHMAC.from_key(key)
            confirmation.confirm(request)
            return Response(
                {"success": True, "data": None, "message": "Email verified successfully.", "errors": None}
            )
        except Exception:
            return Response(
                {"success": False, "data": None, "message": "Invalid or expired verification link.", "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(tags=["Auth"])
class ResendVerificationView(APIView):
    """POST /api/v1/auth/resend-verification/ — Resend email verification."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(summary="Resend email verification link")
    def post(self, request):
        email = request.data.get("email", "").lower()
        if not email:
            return Response(
                {"success": False, "data": None, "message": "Email required.", "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email=email, is_deleted=False)
            from allauth.account.utils import send_email_confirmation
            send_email_confirmation(request, user)
        except User.DoesNotExist:
            pass
        except Exception:
            logger.exception("Resend verification error")
        return Response(
            {"success": True, "data": None, "message": "Verification email sent if account exists.", "errors": None}
        )


@extend_schema(tags=["Auth"])
class GoogleAuthView(APIView):
    """GET /api/v1/auth/social/google/ — Redirect to Google OAuth."""

    permission_classes = [AllowAny]

    @extend_schema(summary="Initiate Google OAuth login")
    def get(self, request):
        from django.conf import settings as django_settings
        frontend_url = getattr(django_settings, "FRONTEND_URL", "http://localhost:5173")
        return Response(
            {
                "success": True,
                "data": {"redirect_url": "/accounts/google/login/"},
                "message": "Redirect to Google OAuth.",
                "errors": None,
            }
        )


@extend_schema(tags=["Auth"])
class GoogleCallbackView(APIView):
    """GET /api/v1/auth/social/google/callback/ — Google OAuth callback info."""

    permission_classes = [AllowAny]

    @extend_schema(summary="Google OAuth callback")
    def get(self, request):
        return Response(
            {
                "success": True,
                "data": None,
                "message": "Use /accounts/google/login/ for Google OAuth.",
                "errors": None,
            }
        )


class AdminUserListView(APIView):
    """GET/POST /api/v1/auth/users/ - Admin user management."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=["Admin"], summary="List all users")
    def get(self, request):
        users = User.objects.filter(is_deleted=False)
        data = UserMeSerializer(users, many=True, context={"request": request}).data
        return Response(
            {"success": True, "data": data, "message": "", "errors": None}
        )

    @extend_schema(tags=["Admin"], summary="Create a user")
    def post(self, request):
        email = request.data.get("email", "").lower()
        password = request.data.get("password", "")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")
        role = request.data.get("role", "jobseeker")
        try:
            user = User.objects.create_user(
                email=email, password=password,
                first_name=first_name, last_name=last_name, role=role,
            )
        except Exception as e:
            return Response(
                {"success": False, "data": None, "message": str(e), "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = UserMeSerializer(user, context={"request": request}).data
        return Response(
            {"success": True, "data": data, "message": "User created.", "errors": None},
            status=status.HTTP_201_CREATED,
        )


class AdminUserDetailView(APIView):
    """PATCH/DELETE /api/v1/auth/users/<pk>/ - Admin user detail management."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=["Admin"], summary="Update a user")
    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "data": None, "message": "User not found.", "errors": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        for field in ("role", "status", "first_name", "last_name"):
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        data = UserMeSerializer(user, context={"request": request}).data
        return Response(
            {"success": True, "data": data, "message": "User updated.", "errors": None}
        )

    @extend_schema(tags=["Admin"], summary="Soft-delete a user")
    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "data": None, "message": "User not found.", "errors": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        user.soft_delete()
        return Response(
            {"success": True, "data": None, "message": "User deleted.", "errors": None}
        )
