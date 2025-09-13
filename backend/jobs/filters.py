import django_filters
from .models import Job

class JobFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="category", lookup_expr="icontains")
    min_budget = django_filters.NumberFilter(field_name="budget", lookup_expr="gte")
    max_budget = django_filters.NumberFilter(field_name="budget", lookup_expr="lte")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Job
        fields = ["location", "category", "is_active"]

    def filter_q(self, queryset, name, value):
        return queryset.filter(
            title__icontains=value
        ) | queryset.filter(description__icontains=value)
