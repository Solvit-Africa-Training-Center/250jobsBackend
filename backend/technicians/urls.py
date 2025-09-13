from django.urls import path
from .views import (
    TechnicianListView, TechnicianDetailView, MyTechnicianProfileView, TechnicianReviewsView,
    TechnicianApplyToJobView, TechnicianMyApplicationsView
)

urlpatterns = [
    path("", TechnicianListView.as_view(), name="technician-list"),                 # /api/technicians/?location=Kigali&skill=Plumber
    path("<int:pk>/", TechnicianDetailView.as_view(), name="technician-detail"),    # /api/technicians/12/
    path("me/", MyTechnicianProfileView.as_view(), name="technician-me"),           # GET/PATCH
    path("<int:pk>/reviews/", TechnicianReviewsView.as_view(), name="technician-reviews"), # GET/POST
    # Technician-scoped job actions
    path("jobs/<int:job_id>/apply/", TechnicianApplyToJobView.as_view(), name="technician-job-apply"),
    path("applications/mine/", TechnicianMyApplicationsView.as_view(), name="technician-my-applications"),
]
