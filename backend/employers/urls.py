from django.urls import path
from .views import (
    MyEmployerProfileView, EmployerTechnicianListView, EmployerPostJobView,
    EmployerApplicantsListView, set_application_status,
    EmployerMyJobsView, EmployerJobDetailView,
    EmployerCreateReviewView,
)

urlpatterns = [
    path("me/", MyEmployerProfileView.as_view(), name="employer-me"),
    path("technicians/", EmployerTechnicianListView.as_view(), name="employer-technicians"),
    path("technicians/<int:pk>/reviews/", EmployerCreateReviewView.as_view(), name="employer-tech-review"),
    path("jobs/", EmployerPostJobView.as_view(), name="employer-post-job"),
    
    path("jobs/mine/", EmployerMyJobsView.as_view(), name="employer-my-jobs"),
    path("jobs/<int:pk>/", EmployerJobDetailView.as_view(), name="employer-job-detail"),
    path("applicants/", EmployerApplicantsListView.as_view(), name="employer-applicants"),
    path("applicants/<int:application_id>/status/<str:new_status>/", set_application_status, name="employer-set-status"),
]
