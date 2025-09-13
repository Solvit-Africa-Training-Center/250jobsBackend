from django.contrib import admin
from .models import Payment, SubscriptionPlan, Subscription

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payer",
        "payer_full_name",
        "payee",
        "payee_full_name",
        "amount",
        "currency",
        "status",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = (
        "payer__username",
        "payer__first_name",
        "payer__last_name",
        "payee__username",
        "payee__first_name",
        "payee__last_name",
    )
    list_select_related = ("payer", "payee", "job", "application")
    @admin.action(description="Mark selected payments as COMPLETED")
    def mark_selected_completed(self, request, queryset):
        updated = queryset.update(status=Payment.Status.COMPLETED)
        self.message_user(request, f"Marked {updated} payment(s) as COMPLETED.")
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "duration_months", "price", "currency", "stripe_price_id")
    list_filter = ("duration_months", "currency")
    search_fields = ("name",)
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan", "status", "start_date", "end_date")
    list_filter = ("status", "plan", "start_date", "end_date")
    search_fields = ("user__username", "plan__name")
    @admin.action(description="Mark selected subscriptions as CANCELED")
    def mark_selected_canceled(self, request, queryset):
        updated = queryset.update(status=Subscription.Status.CANCELED)
        self.message_user(request, f"Canceled {updated} subscription(s).")