from rest_framework import serializers
from .models import EmployerProfile
from technicians.models import TechnicianProfile, Skill
from jobs.models import Job, JobApplication

# Employer profile
class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerProfile
        fields = ["id","company_name","company_description","location","logo"]

# Read-only technician mini (for employer lists)
class SkillMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id","name"]

class TechnicianMiniSerializer(serializers.ModelSerializer):
    # username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    skills = SkillMiniSerializer(many=True, read_only=True)
    class Meta:
        model = TechnicianProfile
        fields = ["first_name","last_name","location","years_experience","rating_avg","rating_count","skills","is_approved"]

# Job create for employer (saved in Jobs app)
class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["id","title","description","category","location","budget","currency","is_active"]
        read_only_fields = ["id","is_active"]

    def create(self, validated_data):
        user = self.context["request"].user
        return Job.objects.create(employer=user, **validated_data)

# Applications (employer view)
class EmployerApplicationSerializer(serializers.ModelSerializer):
    technician_profile = TechnicianMiniSerializer(source="technician.technician_profile", read_only=True)
    class Meta:
        model = JobApplication
        fields = ["id","job","technician","technician_profile","cover_letter","status","created_at"]
        read_only_fields = ["id","job","technician","created_at","status"]
