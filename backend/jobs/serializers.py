from rest_framework import serializers
from .models import Job, JobApplication

class JobSerializer(serializers.ModelSerializer):
    employer_id = serializers.IntegerField(source="employer.id", read_only=True)
    applications_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "employer_id", "title", "description", "category", "location",
            "budget", "currency", "is_active", "created_at", "applications_count"
        ]
        read_only_fields = ["id", "employer_id", "created_at", "applications_count", "is_active"]

class JobCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["title", "description", "category", "location", "budget", "currency", "is_active"]

# jobs/serializers.py
class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    technician_id = serializers.IntegerField(source="technician.id", read_only=True)

    class Meta:
        model = JobApplication
        fields = ["id","job","job_title","technician","technician_id",
                  "cover_letter","status","shortlisted_at","hired_at","created_at"]
        read_only_fields = ["id","job","technician","technician_id",
                            "status","shortlisted_at","hired_at","created_at","job_title"]
