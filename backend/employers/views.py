from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from .models import EmployerProfile
from .serializers import (
    EmployerProfileSerializer, JobCreateSerializer, EmployerApplicationSerializer, TechnicianMiniSerializer
)
from .permissions import IsEmployer
from technicians.models import TechnicianProfile, Review
from django.utils import timezone
from django.db.models import Q
from technicians.serializers import ReviewSerializer
from technicians.filters import TechnicianFilter
from technicians.pagination import NinePerPagePagination
from jobs.models import Job, JobApplication
from jobs.serializers import JobSerializer, JobCreateUpdateSerializer, JobApplicationSerializer
from django.utils import timezone

class MyEmployerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployerProfileSerializer
    permission_classes = [IsEmployer]
    def get_object(self):
        # Get or create an EmployerProfile
        obj, _ = EmployerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"company_name": self.request.user.username or ""},
        )
        return obj


class EmployerTechnicianListView(generics.ListAPIView):
    serializer_class = TechnicianMiniSerializer
    permission_classes = [IsEmployer]
    pagination_class = NinePerPagePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TechnicianFilter
    search_fields = ["user__username","bio","location","skills__name"]
    ordering_fields = ["rating_avg","years_experience"]
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


class EmployerPostJobView(generics.CreateAPIView):
    serializer_class = JobCreateSerializer
    permission_classes = [IsEmployer]


class EmployerApplicantsListView(generics.ListAPIView):
    serializer_class = EmployerApplicationSerializer
    permission_classes = [IsEmployer]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["technician__username","technician__email","cover_letter","job__title"]
    filterset_fields = ["status","job"]
    pagination_class = NinePerPagePagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return JobApplication.objects.none()
        return JobApplication.objects.filter(job__employer=self.request.user)\
            .select_related("job","technician","technician__technician_profile")\
            .prefetch_related("technician__technician_profile__skills")\
            .order_by("-created_at")



class EmployerMyJobsView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsEmployer]
    pagination_class = NinePerPagePagination
    ordering = ["-created_at"]

    def get_queryset(self):
        from django.db.models import Count
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Job.objects.none()
        return Job.objects.filter(employer=self.request.user)\
            .annotate(applications_count=Count("applications"))\
            .order_by("-created_at")



class EmployerJobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobCreateUpdateSerializer
    permission_classes = [IsEmployer]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Job.objects.none()
        return Job.objects.filter(employer=self.request.user)



class EmployerCreateReviewView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsEmployer]
    
    def get_queryset(self):
        return Review.objects.none()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        tech = TechnicianProfile.objects.filter(pk=self.kwargs.get("pk")).first()
        if tech:
            ctx["technician"] = tech
        return ctx


@api_view(["POST"])
@permission_classes([IsEmployer])
def set_application_status(request, application_id: int, new_status: str):
    """
    POST /api/employers/applicants/<id>/status/<PENDING|APPLIED|SHORTLISTED|HIRED|REJECTED>/
    """
    valid = {JobApplication.APPLIED, JobApplication.SHORTLISTED, JobApplication.HIRED, JobApplication.REJECTED}
    
    if new_status.upper() == "PENDING":
        new_status = JobApplication.APPLIED
    if new_status not in valid:
        return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        app = JobApplication.objects.select_related("job").get(id=application_id, job__employer=request.user)
    except JobApplication.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    app.status = new_status
    
    if new_status == JobApplication.SHORTLISTED:
        app.shortlisted_at = timezone.now()
    if new_status == JobApplication.HIRED:
        app.hired_at = timezone.now()
    app.save()
    return Response({"ok": True, "status": app.status, "application_id": app.id})
