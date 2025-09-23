from rest_framework import serializers
from .models import TechnicianProfile, Skill, Review
from rest_framework import validators

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]

class TechnicianListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = TechnicianProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "location",
            "years_experience",
            "rating_avg",
            "rating_count",
            "is_approved",
            "skills",
            "certificates",
        ]

class TechnicianDetailSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = TechnicianProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "bio",
            "years_experience",
            "location",
            "rating_avg",
            "rating_count",
            "is_approved",
            "skills",
            "certificates",
        ]

class TechnicianProfileEditSerializer(serializers.ModelSerializer):
    skill_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    years_experience = serializers.IntegerField(min_value=0, max_value=60, required=False)

    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    rating_avg = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    criminal_record_uploaded_at = serializers.DateTimeField(read_only=True)
    criminal_record_expires_at = serializers.DateTimeField(read_only=True)
    criminal_record_is_expired = serializers.SerializerMethodField()
    criminal_record_expiry_notice = serializers.SerializerMethodField()

    class Meta:
        model = TechnicianProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "bio",
            "years_experience",
            "location",
            "skills",
            "skill_names",
            "certificates",
            "criminal_record",
            "criminal_record_uploaded_at",
            "criminal_record_expires_at",
            "criminal_record_is_expired",
            "criminal_record_expiry_notice",
            "national_id_document",
            "is_approved",
            "rating_avg",
            "rating_count",
        ]
        extra_kwargs = {
            "certificates": {"required": False, "allow_null": True},
            "criminal_record": {"required": False, "allow_null": True},
            "national_id_document": {"required": False, "allow_null": True},
            "bio": {"required": False, "allow_blank": True},
            "location": {"required": False, "allow_blank": True},
        }

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")
        if first_name is not None:
            instance.user.first_name = first_name
        if last_name is not None:
            instance.user.last_name = last_name
        if first_name is not None or last_name is not None:
            instance.user.save(update_fields=[f for f, v in [("first_name", first_name), ("last_name", last_name)] if v is not None])

        # Handle skills by names if provided
        skill_names = validated_data.pop("skill_names", None)
        if skill_names is not None:
            skill_objs = []
            for name in skill_names:
                name = (name or "").strip()
                if not name:
                    continue
                obj, _ = Skill.objects.get_or_create(name=name)
                skill_objs.append(obj)
            instance.skills.set(skill_objs)

        if "criminal_record" in validated_data and not validated_data["criminal_record"]:
            if instance.criminal_record:
                instance.criminal_record.delete(save=False)
            instance.criminal_record = None

        if "national_id_document" in validated_data and not validated_data["national_id_document"]:
            if instance.national_id_document:
                instance.national_id_document.delete(save=False)
            instance.national_id_document = None

        return super().update(instance, validated_data)

    def get_criminal_record_is_expired(self, obj):
        return obj.criminal_record_is_expired

    def get_criminal_record_expiry_notice(self, obj):
        expires_at = obj.criminal_record_expires_at
        if expires_at:
            return f"Criminal record expires on {expires_at.isoformat()} (valid for 6 months)."
        return "Criminal record not submitted yet. Once uploaded it remains valid for 6 months."

class ReviewSerializer(serializers.ModelSerializer):
    technician_id = serializers.IntegerField(source="technician.id", read_only=True)
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "technician", "technician_id", "reviewer", "reviewer_username", "rating", "comment", "created_at"]
        read_only_fields = ["id", "technician_id", "reviewer_username", "created_at", "reviewer", "technician"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def create(self, validated_data):
        technician_profile = self.context.get("technician")
        if not technician_profile:
            raise serializers.ValidationError({"technician": "Technician not found or not provided"})
        reviewer = self.context["request"].user
        return Review.objects.create(technician=technician_profile, reviewer=reviewer, **validated_data)


