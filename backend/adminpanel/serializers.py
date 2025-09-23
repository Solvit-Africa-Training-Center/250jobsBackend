from rest_framework import serializers
from django.utils import timezone

from accounts.models import User
from technicians.models import TechnicianProfile
from jobs.models import Job
from payments.models import Payment, Subscription, SubscriptionPlan


class UserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "location",
            "profile_picture",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TechnicianProfileAdminSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source="user.username")
    has_active_subscription = serializers.SerializerMethodField()
    criminal_record_is_expired = serializers.SerializerMethodField()
    criminal_record_expiry_notice = serializers.SerializerMethodField()

    class Meta:
        model = TechnicianProfile
        fields = [
            "id",
            "user",
            "user_username",
            "bio",
            "years_experience",
            "skills",
            "certificates",
            "criminal_record",
            "criminal_record_uploaded_at",
            "criminal_record_expires_at",
            "criminal_record_is_expired",
            "criminal_record_expiry_notice",
            "national_id_document",
            "location",
            "is_approved",
            "is_paused",
            "trial_ends_at",
            "rating_avg",
            "rating_count",
            "has_active_subscription",
        ]
        read_only_fields = [
            "user",
            "user_username",
            "certificates",
            "criminal_record",
            "criminal_record_uploaded_at",
            "criminal_record_expires_at",
            "criminal_record_is_expired",
            "criminal_record_expiry_notice",
            "national_id_document",
            "trial_ends_at",
            "rating_avg",
            "rating_count",
            "has_active_subscription",
        ]

    def get_has_active_subscription(self, obj):
        now = timezone.now()
        on_trial = bool(obj.trial_ends_at and obj.trial_ends_at >= now)
        if on_trial:
            return True
        return Subscription.objects.filter(
            user=obj.user,
            status=Subscription.Status.ACTIVE,
            end_date__gte=now,
        ).exists()

    def get_criminal_record_is_expired(self, obj):
        return obj.criminal_record_is_expired

    def get_criminal_record_expiry_notice(self, obj):
        expires_at = obj.criminal_record_expires_at
        if expires_at:
            return f"Criminal record expires on {expires_at.isoformat()} (valid for 6 months)."
        return "Criminal record missing; technicians must upload a record that is valid for 6 months."

class TechnicianAdminMinimalSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = TechnicianProfile
        fields = ["id", "user_username"]
        read_only_fields = ["id", "user_username"]



class SubscriptionAdminSerializer(serializers.ModelSerializer):
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


