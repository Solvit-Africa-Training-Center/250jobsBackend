from rest_framework import serializers

from .models import Subscription, SubscriptionPlan, Payment


class SubscribeInitSerializer(serializers.Serializer):
    plan_id = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all(), source="plan")


class PaymentInitResponseSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()
    tx_ref = serializers.CharField()


class SubscriptionSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source="user.username")
    plan_name = serializers.ReadOnlyField(source="plan.name")
    amount = serializers.ReadOnlyField(source="plan.price")

    class Meta:
        model = Subscription
        fields = [
            "id",
            "user",
            "user_username",
            "plan",
            "plan_name",
            "amount",
            "status",
            "start_date",
            "end_date",
            "created_at",
        ]

