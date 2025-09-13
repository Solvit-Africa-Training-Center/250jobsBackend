from django.urls import path
from .views import (
    JobListView, JobRetrieveView
)

urlpatterns = [
    # Public
    path("", JobListView.as_view(), name="job-list"),
    path("<int:pk>/", JobRetrieveView.as_view(), name="job-detail"),
]
