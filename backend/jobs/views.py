from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend

from .models import Job, JobApplication
from .serializers import (
    JobSerializer, JobCreateUpdateSerializer, JobApplicationSerializer
)
from .filters import JobFilter
from .pagination import JobsPagination
from django.db import IntegrityError
from rest_framework import serializers

try:
    # Prefer shared permissions if you already created them
    from employers.permissions import IsEmployer
    from technicians.permissions import IsTechnician
except Exception:
    from .permissions import IsEmployer, IsTechnician



# PUBLIC list of active jobs with filters/search/order/pagination
class JobListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = JobsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "description", "category", "location"]
    ordering_fields = ["created_at", "budget", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Job.objects.filter(is_active=True)
            .annotate(applications_count=Count("applications"))
            .select_related("employer")
        )


# EMPLOYER create a job (you also have an endpoint inside employers app; both can coexist)
class JobCreateView(generics.CreateAPIView):
    serializer_class = JobCreateUpdateSerializer
    permission_classes = [IsEmployer]

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user)


# PUBLIC retrieve a job
class JobRetrieveView(generics.RetrieveAPIView):
    queryset = Job.objects.all().annotate(applications_count=Count("applications")).select_related("employer")
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]


# EMPLOYER update or delete own job
class JobUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobCreateUpdateSerializer
    permission_classes = [IsEmployer]

    def perform_update(self, serializer):
        job = self.get_object()
        if job.employer != self.request.user:
            raise PermissionDenied("You can edit only your jobs.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.employer != self.request.user:
            raise PermissionDenied("You can delete only your jobs.")
        instance.delete()


# TECHNICIAN apply to a job
class ApplyToJobView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsTechnician]

    def perform_create(self, serializer):
        job = Job.objects.get(pk=self.kwargs["job_id"], is_active=True)
        try:
            serializer.save(job=job, technician=self.request.user)  # ✅ sets the right tech
        except IntegrityError:
            raise serializers.ValidationError({"detail": "You have already applied to this job."})


# TECHNICIAN: my applications
class MyApplicationsView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsTechnician]
    pagination_class = JobsPagination

    def get_queryset(self):
        return (JobApplication.objects
                .filter(technician_id=self.request.user.id)  # ✅ robust filter
                .select_related("job")                       # ✅ needed for job_title
                .order_by("-created_at"))

# EMPLOYER: applications for a given job I own
class ApplicationsForMyJobView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsEmployer]
    pagination_class = JobsPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["cover_letter", "technician__username", "technician__email"]

    def get_queryset(self):
        job_id = self.kwargs.get("job_id")
        try:
            job = Job.objects.get(id=job_id, employer=self.request.user)
        except Job.DoesNotExist:
            raise NotFound("Job not found or you are not the owner.")
        return JobApplication.objects.filter(job=job)\
            .select_related("technician", "job").order_by("-created_at")


# EMPLOYER: list all my jobs (with applications_count)
class MyJobsView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsEmployer]
    pagination_class = JobsPagination
    ordering = ["-created_at"]

    def get_queryset(self):
        return Job.objects.filter(employer=self.request.user)\
            .annotate(applications_count=Count("applications"))\
            .order_by("-created_at")

