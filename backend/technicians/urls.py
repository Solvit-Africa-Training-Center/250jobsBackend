from django.urls import path
from .views import (
    TechnicianListView, TechnicianDetailView, MyTechnicianProfileView, TechnicianReviewsView,
    TechnicianApplyToJobView, TechnicianMyApplicationsView
)

urlpatterns = [
    path("", TechnicianListView.as_view(), name="technician-list"),                 
    path("<int:pk>/", TechnicianDetailView.as_view(), name="technician-detail"),    
    path("me/", MyTechnicianProfileView.as_view(), name="technician-me"),           
    path("<int:pk>/reviews/", TechnicianReviewsView.as_view(), name="technician-reviews"), 
    
    path("jobs/<int:job_id>/apply/", TechnicianApplyToJobView.as_view(), name="technician-job-apply"),
    path("applications/mine/", TechnicianMyApplicationsView.as_view(), name="technician-my-applications"),
]
