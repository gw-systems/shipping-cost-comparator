from django.contrib import admin
from .models import Order, OrderStatus, PaymentMode


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Django Admin configuration for Order model"""

    list_display = [
        'order_number', 'recipient_name', 'recipient_contact',
        'status', 'selected_carrier', 'total_cost', 'created_at'
    ]

    list_filter = [
        'status', 'payment_mode', 'selected_carrier',
        'mode', 'created_at', 'booked_at'
    ]

    search_fields = [
        'order_number', 'recipient_name', 'recipient_contact',
        'recipient_email', 'awb_number'
    ]

    readonly_fields = [
        'order_number', 'volumetric_weight', 'applicable_weight',
        'created_at', 'updated_at', 'booked_at'
    ]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'notes')
        }),
        ('Recipient Details', {
            'fields': (
                'recipient_name', 'recipient_contact', 'recipient_email',
                'recipient_address', 'recipient_pincode', 'recipient_city',
                'recipient_state', 'recipient_phone'
            )
        }),
        ('Sender Details', {
            'fields': (
                'sender_name', 'sender_pincode', 'sender_address', 'sender_phone'
            )
        }),
        ('Package Details', {
            'fields': (
                'weight', 'length', 'width', 'height',
                'volumetric_weight', 'applicable_weight'
            )
        }),
        ('Item Details', {
            'fields': (
                'item_type', 'sku', 'quantity', 'item_amount'
            )
        }),
        ('Payment', {
            'fields': ('payment_mode', 'order_value')
        }),
        ('Shipping Details', {
            'fields': (
                'selected_carrier', 'mode', 'zone_applied',
                'total_cost', 'cost_breakdown', 'awb_number'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'booked_at')
        }),
    )

    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50

    def has_delete_permission(self, request, obj=None):
        # Only allow deletion of DRAFT orders
        if obj and obj.status != OrderStatus.DRAFT:
            return False
        return super().has_delete_permission(request, obj)
