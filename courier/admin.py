from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Order, OrderStatus, PaymentMode, FTLOrder


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Django Admin configuration for Order model"""

    list_display = [
        'order_number', 'recipient_name', 'recipient_contact',
        'status_badge', 'selected_carrier', 'mode', 'total_cost_display', 'created_at'
    ]

    list_filter = [
        'status', 'payment_mode', 'selected_carrier',
        'mode', 'created_at', 'booked_at'
    ]

    search_fields = [
        'order_number', 'recipient_name', 'recipient_contact',
        'recipient_email', 'awb_number', 'sender_name'
    ]

    readonly_fields = [
        'order_number', 'volumetric_weight', 'applicable_weight',
        'created_at', 'updated_at', 'booked_at', 'cost_breakdown'
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
            'fields': ('created_at', 'updated_at', 'booked_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    actions = ['mark_as_booked', 'mark_as_cancelled']

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'draft': '#6c757d',
            'booked': '#007bff',
            'manifested': '#17a2b8',
            'picked_up': '#ffc107',
            'out_for_delivery': '#fd7e14',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
            'pickup_exception': '#e83e8c',
            'ndr': '#6f42c1',
            'rto': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def total_cost_display(self, obj):
        """Display cost with currency formatting"""
        if obj.total_cost:
            return format_html('₹{:.2f}', obj.total_cost)
        return '-'
    total_cost_display.short_description = 'Total Cost'
    total_cost_display.admin_order_field = 'total_cost'

    def has_delete_permission(self, request, obj=None):
        # Only allow deletion of DRAFT orders
        if obj and obj.status != OrderStatus.DRAFT:
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description='Mark selected orders as BOOKED')
    def mark_as_booked(self, request, queryset):
        updated = queryset.filter(status=OrderStatus.DRAFT).update(status=OrderStatus.BOOKED)
        self.message_user(request, f'{updated} order(s) marked as booked.')

    @admin.action(description='Mark selected orders as CANCELLED')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.exclude(
            status__in=[OrderStatus.DELIVERED, OrderStatus.PICKED_UP]
        ).update(status=OrderStatus.CANCELLED)
        self.message_user(request, f'{updated} order(s) marked as cancelled.')


@admin.register(FTLOrder)
class FTLOrderAdmin(admin.ModelAdmin):
    """Django Admin configuration for FTL Order model"""

    list_display = [
        'order_number', 'name', 'phone', 'source_city', 'destination_city',
        'container_type', 'status_badge', 'total_price_display', 'created_at'
    ]

    list_filter = [
        'status', 'container_type', 'source_city', 'destination_city',
        'created_at', 'booked_at'
    ]

    search_fields = [
        'order_number', 'name', 'phone', 'email', 'source_city', 'destination_city'
    ]

    readonly_fields = [
        'order_number', 'base_price', 'escalation_amount',
        'price_with_escalation', 'gst_amount', 'total_price',
        'created_at', 'updated_at', 'booked_at'
    ]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'notes')
        }),
        ('Customer Details', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Route Details', {
            'fields': (
                ('source_city', 'source_pincode'),
                'source_address',
                ('destination_city', 'destination_pincode')
            )
        }),
        ('Container & Pricing', {
            'fields': (
                'container_type',
                ('base_price', 'escalation_amount'),
                ('price_with_escalation', 'gst_amount'),
                'total_price'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'booked_at'),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    actions = ['mark_as_booked', 'mark_as_cancelled']

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'draft': '#6c757d',
            'booked': '#007bff',
            'manifested': '#17a2b8',
            'picked_up': '#ffc107',
            'out_for_delivery': '#fd7e14',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def total_price_display(self, obj):
        """Display price with currency formatting"""
        if obj.total_price:
            return format_html('₹{:.2f}', obj.total_price)
        return '-'
    total_price_display.short_description = 'Total Price'
    total_price_display.admin_order_field = 'total_price'

    def has_delete_permission(self, request, obj=None):
        # Only allow deletion of DRAFT or CANCELLED orders
        if obj and obj.status not in [OrderStatus.DRAFT, OrderStatus.CANCELLED]:
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description='Mark selected orders as BOOKED')
    def mark_as_booked(self, request, queryset):
        updated = queryset.filter(status=OrderStatus.DRAFT).update(status=OrderStatus.BOOKED)
        self.message_user(request, f'{updated} FTL order(s) marked as booked.')

    @admin.action(description='Mark selected orders as CANCELLED')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status=OrderStatus.DRAFT).update(status=OrderStatus.CANCELLED)
        self.message_user(request, f'{updated} FTL order(s) marked as cancelled.')


# Customize admin site header
admin.site.site_header = 'LogiRate Admin'
admin.site.site_title = 'LogiRate Admin Portal'
admin.site.index_title = 'Order & Carrier Management'
