from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserAdminViewSet,
    TechnicianProfileAdminViewSet,
    SubscriptionAdminViewSet,
    AnalyticsViewSet,
)

router = DefaultRouter()
router.register(r"users", UserAdminViewSet, basename="admin-users")
router.register(r"technicians", TechnicianProfileAdminViewSet, basename="admin-technicians")
router.register(r"subscriptions", SubscriptionAdminViewSet, basename="admin-subscriptions")
router.register(r"analytics", AnalyticsViewSet, basename="admin-analytics")

urlpatterns = [
    path("", include(router.urls)),
]
