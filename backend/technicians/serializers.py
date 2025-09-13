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
    # Provide skills by names only; create any that don't exist
    skill_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    years_experience = serializers.IntegerField(min_value=0, max_value=60, required=False)
    # Read-only for consistency with list/detail
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    rating_avg = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    rating_count = serializers.IntegerField(read_only=True)

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
            "is_approved",
            "rating_avg",
            "rating_count",
        ]
        extra_kwargs = {
            "certificates": {"required": False, "allow_null": True},
            "bio": {"required": False, "allow_blank": True},
            "location": {"required": False, "allow_blank": True},
        }

    def update(self, instance, validated_data):
        # Handle nested user fields
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

        return super().update(instance, validated_data)


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
        # technician provided via view context; reviewer is request.user
        technician_profile = self.context.get("technician")
        if not technician_profile:
            raise serializers.ValidationError({"technician": "Technician not found or not provided"})
        reviewer = self.context["request"].user
        return Review.objects.create(technician=technician_profile, reviewer=reviewer, **validated_data)
