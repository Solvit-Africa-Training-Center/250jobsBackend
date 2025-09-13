from django.urls import path
from .views import SubscribeInitView, stripe_webhook, MySubscriptionsView, PlansListView, PaymentsConfigView

urlpatterns = [
    path("subscribe/", SubscribeInitView.as_view(), name="payments-subscribe"),
    path("webhook/stripe/", stripe_webhook, name="payments-webhook-stripe"),
    path("me/subscriptions/", MySubscriptionsView.as_view(), name="payments-my-subs"),
    path("plans/", PlansListView.as_view(), name="payments-plans"),
    path("config/", PaymentsConfigView.as_view(), name="payments-config"),
]
