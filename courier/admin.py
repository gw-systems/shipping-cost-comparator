from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Order, OrderStatus, PaymentMode, FTLOrder, Courier, CourierZoneRate, CityRoute, CustomZone, CustomZoneRate, DeliverySlab, SystemConfig
from .models_refactored import FeeStructure, ServiceConstraints, FuelConfiguration, RoutingLogic

class FeeStructureInline(admin.StackedInline):
    model = FeeStructure
    verbose_name = "Fee Structure Configuration"
    can_delete = False

class ServiceConstraintsInline(admin.StackedInline):
    model = ServiceConstraints
    verbose_name = "Service Constraints"
    can_delete = False

class FuelConfigurationInline(admin.StackedInline):
    model = FuelConfiguration
    verbose_name = "Fuel Surcharge Configuration"
    can_delete = False

class RoutingLogicInline(admin.StackedInline):
    model = RoutingLogic
    verbose_name = "Routing Logic Config"
    can_delete = False

class CourierZoneRateInline(admin.TabularInline):
    model = CourierZoneRate
    extra = 0
    fields = ['zone_code', 'rate_type', 'rate']
    verbose_name = "Standard Zone Rate"
    verbose_name_plural = "Standard Zone Rates (Zones A-F)"
    ordering = ['zone_code', 'rate_type']


class CityRouteInline(admin.TabularInline):
    model = CityRoute
    extra = 1
    fields = ['city_name', 'rate_per_kg']
    verbose_name = "City Route"
    verbose_name_plural = "City Routes (add all destination cities and their rates)"


class CustomZoneInline(admin.TabularInline):
    model = CustomZone
    extra = 1
    fields = ['location_name', 'zone_code']
    verbose_name = "Zone Mapping"
    verbose_name_plural = "Zone Mappings (map locations to zone codes)"


class CustomZoneRateInline(admin.TabularInline):
    model = CustomZoneRate
    extra = 1
    fields = ['from_zone', 'to_zone', 'rate_per_kg']
    verbose_name = "Zone Rate"
    verbose_name_plural = "Zone Matrix (rates between zone pairs)"


class DeliverySlabInline(admin.TabularInline):
    model = DeliverySlab
    extra = 1
    fields = ['min_weight', 'max_weight', 'rate']
    verbose_name = "Delivery Slab"
    verbose_name_plural = "Delivery Slabs (City-to-City Weight Brackets)"


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    # Only show main fields, hide legacy big list
    list_display = ['name', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name']
    
    inlines = [
        FeeStructureInline,
        ServiceConstraintsInline,
        FuelConfigurationInline,
        RoutingLogicInline,
        # Conditional inlines are tricky if not dynamic, but we can just add them all 
        # or keep the get_inlines logic from before but appended
    ]

    def get_inlines(self, request, obj=None):
        """Show different inlines based on routing logic"""
        default_inlines = [
            FeeStructureInline,
            ServiceConstraintsInline,
            FuelConfigurationInline,
            RoutingLogicInline
        ]
        
        # We need to check obj.routing_config.logic_type if moved, or obj.rate_logic fallback using property
        # For now assume legacy column usage for logic checking
        if obj and obj.rate_logic == 'City_To_City':
            return default_inlines + [CityRouteInline, DeliverySlabInline]
        elif obj and obj.rate_logic == 'Zonal_Custom':
            return default_inlines + [CustomZoneInline, CustomZoneRateInline]
        elif obj and obj.rate_logic == 'Zonal_Standard':
            return default_inlines + [CourierZoneRateInline]
        return default_inlines
    
    # We remove the fieldsets that referenced legacy fields because they will error if fields are deleted
    # Instead rely on Inlines


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order management"""
    list_display = [
        'order_number', 'recipient_name', 'status', 'carrier', 
        'payment_mode', 'total_cost', 'created_at', 'booked_at'
    ]
    list_filter = ['status', 'carrier', 'payment_mode', 'created_at']
    search_fields = ['order_number', 'recipient_name', 'awb_number', 'recipient_contact']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'volumetric_weight', 'applicable_weight']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'carrier', 'awb_number')
        }),
        ('Recipient Details', {
            'fields': (
                'recipient_name', 'recipient_contact', 'recipient_phone', 'recipient_email',
                'recipient_address', 'recipient_pincode', 'recipient_city', 'recipient_state'
            )
        }),
        ('Sender Details', {
            'fields': ('sender_name', 'sender_address', 'sender_pincode', 'sender_phone')
        }),
        ('Package Details', {
            'fields': (
                'weight', 'length', 'width', 'height', 
                'volumetric_weight', 'applicable_weight'
            )
        }),
        ('Item Details', {
            'fields': ('item_type', 'sku', 'quantity', 'item_amount')
        }),
        ('Payment & Pricing', {
            'fields': ('payment_mode', 'order_value', 'total_cost', 'cost_breakdown')
        }),
        ('Shipment Details', {
            'fields': ('zone_applied', 'mode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'booked_at')
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on order status"""
        readonly = list(self.readonly_fields)
        
        # If order is booked or later, make booked_at readonly too
        if obj and obj.status != OrderStatus.DRAFT:
            if 'booked_at' not in readonly:
                readonly.append('booked_at')
        
        return readonly
    
    actions = ['mark_as_booked', 'mark_as_cancelled']
    
    def mark_as_booked(self, request, queryset):
        """Mark selected orders as booked"""
        from django.utils import timezone
        count = 0
        for order in queryset:
            if order.status == OrderStatus.DRAFT:
                order.status = OrderStatus.BOOKED
                order.booked_at = timezone.now()
                order.save()
                count += 1
        self.message_user(request, f'{count} order(s) marked as booked.')
    mark_as_booked.short_description = "Mark selected orders as BOOKED"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected orders as cancelled"""
        count = queryset.update(status=OrderStatus.CANCELLED)
        self.message_user(request, f'{count} order(s) marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected orders as CANCELLED"


@admin.register(FTLOrder)
class FTLOrderAdmin(admin.ModelAdmin):
    """Admin interface for FTL Order management"""
    list_display = [
        'order_number', 'name', 'source_city', 'destination_city',
        'container_type', 'status', 'total_price', 'created_at', 'booked_at'
    ]
    list_filter = ['status', 'container_type', 'created_at']
    search_fields = ['order_number', 'name', 'email', 'phone', 'source_city', 'destination_city']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status')
        }),
        ('Contact Details', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Source Location', {
            'fields': ('source_city', 'source_address', 'source_pincode')
        }),
        ('Destination Location', {
            'fields': ('destination_city', 'destination_address', 'destination_pincode')
        }),
        ('Container & Pricing', {
            'fields': (
                'container_type', 'base_price', 'escalation_amount',
                'price_with_escalation', 'gst_amount', 'total_price'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'booked_at')
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_booked', 'mark_as_cancelled']
    
    def mark_as_booked(self, request, queryset):
        """Mark selected FTL orders as booked"""
        from django.utils import timezone
        count = 0
        for order in queryset:
            if order.status == OrderStatus.DRAFT:
                order.status = OrderStatus.BOOKED
                order.booked_at = timezone.now()
                order.save()
                count += 1
        self.message_user(request, f'{count} FTL order(s) marked as booked.')
    mark_as_booked.short_description = "Mark selected FTL orders as BOOKED"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected FTL orders as cancelled"""
        count = queryset.update(status=OrderStatus.CANCELLED)
        self.message_user(request, f'{count} FTL order(s) marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected FTL orders as CANCELLED"
