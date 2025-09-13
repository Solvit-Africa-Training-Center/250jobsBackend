from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, decorators, response, status, filters

from accounts.models import User
from technicians.models import TechnicianProfile
from jobs.models import Job
from payments.models import Payment, Subscription

from .permissions import IsAdminRoleOrStaff
from .serializers import (
    UserAdminSerializer,
    TechnicianProfileAdminSerializer,
    TechnicianAdminMinimalSerializer,
    SubscriptionAdminSerializer,
)
from drf_yasg.utils import swagger_auto_schema


class UserAdminViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminRoleOrStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["username", "email", "phone_number", "location"]
    filterset_fields = ["role", "is_active", "is_staff", "is_superuser"]


class TechnicianProfileAdminViewSet(viewsets.ModelViewSet):
    queryset = TechnicianProfile.objects.select_related("user").prefetch_related("skills").all()
    serializer_class = TechnicianProfileAdminSerializer
    permission_classes = [IsAdminRoleOrStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["is_approved", "location", "years_experience"]
    search_fields = ["user__username", "user__email", "location", "skills__name"]
    # Read-only for CRUD, but allow POST for custom actions (approve/pause/resume/revoke)
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        # For action endpoints, show only minimal, read-only fields to avoid confusing inputs
        if getattr(self, "action", None) in {"approve", "revoke", "pause", "resume"}:
            return TechnicianAdminMinimalSerializer
        return super().get_serializer_class()

    @decorators.action(detail=True, methods=["post"], url_path="approve")
    @swagger_auto_schema(request_body=None)
    def approve(self, request, pk=None):
        from datetime import timedelta
        from django.utils import timezone

        profile = self.get_object()
        profile.is_approved = True
        # Start 30-day trial from approval time
        profile.trial_ends_at = timezone.now() + timedelta(days=30)
        # Ensure not paused on approval
        profile.is_paused = False
        profile.save(update_fields=["is_approved", "trial_ends_at", "is_paused"])
        return response.Response({
            "status": "approved",
            "trial_ends_at": profile.trial_ends_at,
        })

    @decorators.action(detail=True, methods=["post"], url_path="revoke")
    @swagger_auto_schema(request_body=None)
    def revoke(self, request, pk=None):
        profile = self.get_object()
        profile.is_approved = False
        profile.save(update_fields=["is_approved"])
        return response.Response({"status": "revoked"})

    @decorators.action(detail=True, methods=["post"], url_path="pause")
    @swagger_auto_schema(request_body=None)
    def pause(self, request, pk=None):
        profile = self.get_object()
        profile.is_paused = True
        profile.save(update_fields=["is_paused"])
        return response.Response({"status": "paused"})

    @decorators.action(detail=True, methods=["post"], url_path="resume")
    @swagger_auto_schema(request_body=None)
    def resume(self, request, pk=None):
        profile = self.get_object()
        profile.is_paused = False
        profile.save(update_fields=["is_paused"])
        return response.Response({"status": "resumed"})

    @decorators.action(detail=False, methods=["get"], url_path="pending")
    def pending(self, request):
        qs = self.get_queryset().filter(is_approved=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return response.Response(ser.data)


class JobAdminViewSet(viewsets.ModelViewSet):
    # Removed per scope simplification
    pass


class JobApplicationAdminViewSet(viewsets.ModelViewSet):
    # Removed per scope simplification
    pass


class PaymentAdminViewSet(viewsets.ModelViewSet):
    # Removed per scope simplification
    pass


    # Removed per scope simplification
    pass


class SubscriptionAdminViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("user", "plan").all()
    serializer_class = SubscriptionAdminSerializer
    permission_classes = [IsAdminRoleOrStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["user__username", "plan__name"]
    filterset_fields = ["status", "plan", "user"]
    http_method_names = ["get", "head", "options"]  # read-only for admin


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminRoleOrStaff]

    @decorators.action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        data = {
            "total_users": User.objects.count(),
            "posted_jobs": Job.objects.count(),
            "total_revenue": Payment.objects.filter(status=Payment.Status.COMPLETED).aggregate(total=Sum("amount"))["total"] or 0,
            "pending_approvals": TechnicianProfile.objects.filter(is_approved=False).count(),
        }
        return response.Response(data, status=status.HTTP_200_OK)
