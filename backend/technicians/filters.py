import django_filters
from .models import TechnicianProfile

class TechnicianFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    skill = django_filters.CharFilter(method="filter_skill")  # by name (icontains)
    skill_id = django_filters.NumberFilter(field_name="skills__id")

    class Meta:
        model = TechnicianProfile
        fields = ["location", "skill", "skill_id", "is_approved"]

    def filter_skill(self, queryset, name, value):
        return queryset.filter(skills__name__icontains=value)
