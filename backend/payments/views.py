import os
import uuid
from datetime import timedelta
import stripe

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from accounts.models import User
from .models import Payment, Subscription, SubscriptionPlan
from .serializers import SubscribeInitSerializer, PaymentInitResponseSerializer, SubscriptionSerializer
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class IsTechnician(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "technician")


class SubscribeInitView(views.APIView):
    permission_classes = [IsTechnician]

    @swagger_auto_schema(
        operation_summary="Initialize subscription payment",
        request_body=SubscribeInitSerializer,
        responses={200: PaymentInitResponseSerializer},
        tags=["Payments"],
    )
    def post(self, request):
        serializer = SubscribeInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan: SubscriptionPlan = serializer.validated_data["plan"]

        user: User = request.user
        stripe_secret = os.getenv("STRIPE_SECRET_KEY", "")
        # Ensure plan has a Stripe price id; allow env fallback by duration
        if not getattr(plan, "stripe_price_id", ""):
            env_key = None
            if plan.duration_months == 1:
                env_key = "STRIPE_PRICE_MONTHLY"
            elif plan.duration_months == 6:
                env_key = "STRIPE_PRICE_6MONTHS"
            elif plan.duration_months == 12:
                env_key = "STRIPE_PRICE_YEARLY"
            if env_key and os.getenv(env_key):
                plan.stripe_price_id = os.getenv(env_key)
                try:
                    plan.save(update_fields=["stripe_price_id"])
                except Exception:
                    pass
        success_url = os.getenv("STRIPE_SUCCESS_URL", "") or os.getenv("FLW_REDIRECT_URL", "")
        cancel_url = os.getenv("STRIPE_CANCEL_URL", "") or success_url or ""
        if not stripe_secret or not plan.stripe_price_id:
            # Dev fallback: return mock session URL (no external call)
            tx_ref = f"sub-{user.id}-{uuid.uuid4().hex[:10]}"
            Payment.objects.create(
                payer=user,
                payee=None,
                job=None,
                application=None,
                amount=plan.price,
                currency=plan.currency,
                status=Payment.Status.PENDING,
                tx_ref=tx_ref,
            )
            return Response({"checkout_url": f"https://stripe.mock/checkout/{tx_ref}", "tx_ref": tx_ref}, status=200)

        try:
            stripe.api_key = stripe_secret
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
                success_url=success_url or "https://example.com/success",
                cancel_url=cancel_url or "https://example.com/cancel",
                metadata={"user_id": user.id, "plan_id": plan.id},
            )
            Payment.objects.create(
                payer=user,
                payee=None,
                job=None,
                application=None,
                amount=plan.price,
                currency=plan.currency,
                status=Payment.Status.PENDING,
                tx_ref=session.id,
                provider_tx_id=session.payment_intent or "",
            )
            return Response({"checkout_url": session.url, "tx_ref": session.id}, status=200)
        except Exception:
            return Response({"detail": "Stripe init error."}, status=502)


plan_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "type": openapi.Schema(type=openapi.TYPE_STRING, description="stripe event type"),
        "data": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "object": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_STRING, description="checkout.session id"),
                        "metadata": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "plan_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            },
                        ),
                    },
                )
            },
        ),
    },
)


@csrf_exempt
@swagger_auto_schema(method="post", request_body=plan_schema, tags=["Payments"])
@api_view(["POST"])
@permission_classes([])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except Exception:
            return HttpResponse(status=400)
    else:
        import json
        try:
            event = json.loads(payload.decode() or "{}")
        except Exception:
            return HttpResponse(status=400)

    event_type = event.get("type")
    data_object = (event.get("data") or {}).get("object") or {}
    session_id = data_object.get("id")
    metadata = data_object.get("metadata") or {}
    user_id = metadata.get("user_id")
    plan_id = metadata.get("plan_id")

    if not session_id:
        return HttpResponse(status=400)

    try:
        payment = Payment.objects.get(tx_ref=session_id)
    except Payment.DoesNotExist:
        payment = None

    if event_type in ("checkout.session.completed", "invoice.payment_succeeded"):
        if payment:
            # In subscription mode, payment_intent may be None on the session; fall back to invoice or subscription id
            provider_tx_id = (
                data_object.get("payment_intent")
                or data_object.get("invoice")
                or data_object.get("subscription")
                or ""
            )
            payment.status = Payment.Status.COMPLETED
            payment.provider_tx_id = provider_tx_id
            payment.completed_at = timezone.now()
            payment.save(update_fields=["status", "provider_tx_id", "completed_at"])

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            user = User.objects.get(id=user_id)
        except Exception:
            return HttpResponse(status=200)

        start = timezone.now()
        end = start + timedelta(days=30 * int(plan.duration_months))
        Subscription.objects.create(
            user=user,
            plan=plan,
            start_date=start,
            end_date=end,
            status=Subscription.Status.ACTIVE,
        )
    else:
        if payment:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])

    return HttpResponse(status=200)

class MySubscriptionsView(views.APIView):
    permission_classes = [IsTechnician]

    @swagger_auto_schema(tags=["Payments"])
    def get(self, request):
        subs = Subscription.objects.filter(user=request.user).select_related("plan").order_by("-start_date")
        return Response(SubscriptionSerializer(subs, many=True).data)


class PlansListView(views.APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Payments"])
    def get(self, request):
        plans = SubscriptionPlan.objects.all().order_by("price")
        data = [
            {
                "id": p.id,
                "name": p.name,
                "duration_months": p.duration_months,
                "price": str(p.price),
                "currency": p.currency,
                "stripe_price_id": p.stripe_price_id,
            }
            for p in plans
        ]
        return Response(data, status=200)


class PaymentsConfigView(views.APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Payments"])
    def get(self, request):
        return Response({
            "stripe_publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
        })
