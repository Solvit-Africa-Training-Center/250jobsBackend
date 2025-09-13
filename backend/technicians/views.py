from rest_framework import generics, permissions, filters
from django.utils import timezone
from django.db.models import Q
from .models import TechnicianProfile, Review
from .serializers import (
    TechnicianListSerializer, TechnicianDetailSerializer, TechnicianProfileEditSerializer, ReviewSerializer
)
from .filters import TechnicianFilter
from .pagination import NinePerPagePagination
from .permissions import IsTechnician
from employers.permissions import IsEmployer
from django_filters.rest_framework import DjangoFilterBackend
from jobs.models import Job, JobApplication
from jobs.serializers import JobApplicationSerializer
from rest_framework import serializers as drf_serializers

# PUBLIC: List technicians (approved only) with pagination, filter, search
class TechnicianListView(generics.ListAPIView):
    serializer_class = TechnicianListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = NinePerPagePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TechnicianFilter
    search_fields = ["user__username", "bio", "location", "skills__name"]
    ordering_fields = ["rating_avg", "years_experience"]
    ordering = ["-rating_avg"]

    def get_queryset(self):
        now = timezone.now()
        return (
            TechnicianProfile.objects
            .filter(is_approved=True, is_paused=False)
            .filter(
                Q(trial_ends_at__gte=now) |
                Q(user__subscriptions__status="ACTIVE", user__subscriptions__end_date__gte=now)
            )
            .select_related("user").prefetch_related("skills").distinct()
        )

# PUBLIC: Detail page for a technician
class TechnicianDetailView(generics.RetrieveAPIView):
    queryset = TechnicianProfile.objects.filter(is_approved=True).select_related("user").prefetch_related("skills")
    serializer_class = TechnicianDetailSerializer
    permission_classes = [permissions.AllowAny]

# TECHNICIAN: My profile (create-once via signal elsewhere), view & update
class MyTechnicianProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = TechnicianProfileEditSerializer
    permission_classes = [IsTechnician]

    def get_object(self):
        # Ensure a technician profile exists for the authenticated technician
        profile, _ = TechnicianProfile.objects.get_or_create(user=self.request.user)
        # Auto-pause if trial expired and no active subscription; unpause if active
        try:
            from payments.models import Subscription
            now = timezone.now()
            has_active = Subscription.objects.filter(
                user=self.request.user,
                status=Subscription.Status.ACTIVE,
                end_date__gte=now,
            ).exists()
            on_trial = bool(profile.trial_ends_at and profile.trial_ends_at >= now)
            new_paused = not (has_active or on_trial)
            if profile.is_paused != new_paused:
                profile.is_paused = new_paused
                profile.save(update_fields=["is_paused"])
        except Exception:
            pass
        return profile


class TechnicianReviewsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        # When generating swagger schema, there is no URL kwarg
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        tech_id = self.kwargs.get("pk")
        if not tech_id:
            return Review.objects.none()
        return (
            Review.objects
            .filter(technician_id=tech_id)
            .select_related("reviewer", "technician")
            .order_by("-created_at")
        )


# TECHNICIAN: apply to a job
class TechnicianApplyToJobView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsTechnician]

    def perform_create(self, serializer):
        try:
            job = Job.objects.get(pk=self.kwargs["job_id"], is_active=True)
        except Job.DoesNotExist:
            raise drf_serializers.ValidationError({"detail": "Job not found or inactive."})
        from django.db import IntegrityError
        try:
            serializer.save(job=job, technician=self.request.user)
        except IntegrityError:
            raise drf_serializers.ValidationError({"detail": "You have already applied to this job."})


# TECHNICIAN: my applications
class TechnicianMyApplicationsView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsTechnician]
    pagination_class = NinePerPagePagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return JobApplication.objects.none()
        return (JobApplication.objects
                .filter(technician_id=self.request.user.id)
                .select_related("job")
                .order_by("-created_at"))
