from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer, LoginSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(tags=["Auth"])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Auth"])
    def get(self, request):
        user = request.user
        return Response(
            {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "last_seen": getattr(user, 'last_seen', None)
            },
            status=200
        )


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Auth"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
            },
            required=["email"],
        ),
        responses={200: "Reset instructions sent if email exists."}
    )
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "If the email exists, a reset was sent."}, status=200)

        # Generate reset token & uid
        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Build reset link using FRONTEND_RESET_URL or BACKEND_RESET_URL if provided
        reset_link_base = getattr(settings, "FRONTEND_RESET_URL", None) or getattr(settings, "BACKEND_RESET_URL", None)
        if reset_link_base:
            reset_link = f"{reset_link_base}?uid={uidb64}&token={token}"
            try:
                send_mail(
                    subject="Password Reset Request",
                    message=f"Click the link to reset your password: {reset_link}",
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception:
                # Never fail hard on email in API
                pass

        # In DEBUG, also return uid/token (for API testing without email)
        payload = {"detail": "Reset instructions sent if email exists."}
        if settings.DEBUG:
            payload.update({"uid": uidb64, "token": token})
        return Response(payload, status=200)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "uid": openapi.Schema(type=openapi.TYPE_STRING),
                "token": openapi.Schema(type=openapi.TYPE_STRING),
                "new_password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
            required=["uid", "token", "new_password"],
        ),
        responses={200: "Password has been reset"}
    )
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not all([uidb64, token, new_password]):
            return Response({"detail": "uid, token and new_password are required"}, status=400)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Invalid uid"}, status=400)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"detail": "Invalid or expired token"}, status=400)

        # Set new password
        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response({"detail": "Password has been reset"}, status=200)
