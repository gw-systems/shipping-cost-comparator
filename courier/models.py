from django.db import models
from django.utils import timezone


class OrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"
    BOOKED = "booked", "Booked"
    IN_TRANSIT = "in_transit", "In Transit"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class PaymentMode(models.TextChoices):
    COD = "cod", "Cash on Delivery"
    PREPAID = "prepaid", "Prepaid"


class Order(models.Model):
    """
    Order model for logistics management.
    Converted from SQLAlchemy to Django ORM.
    """
    # Auto-generated fields
    id = models.BigAutoField(primary_key=True)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)

    # Recipient Details
    recipient_name = models.CharField(max_length=255)
    recipient_contact = models.CharField(max_length=15)  # Mandatory contact number
    recipient_address = models.TextField()
    recipient_pincode = models.IntegerField()
    recipient_city = models.CharField(max_length=100, blank=True, null=True)  # Auto-filled
    recipient_state = models.CharField(max_length=100, blank=True, null=True)  # Auto-filled
    recipient_phone = models.CharField(max_length=15, blank=True, null=True)
    recipient_email = models.EmailField(blank=True, null=True)

    # Sender Details
    sender_pincode = models.IntegerField()
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_address = models.TextField(blank=True, null=True)
    sender_phone = models.CharField(max_length=15, blank=True, null=True)

    # Box Details
    weight = models.FloatField()  # Actual weight in kg
    length = models.FloatField()  # Length in cm (mandatory)
    width = models.FloatField()   # Width in cm (mandatory)
    height = models.FloatField()  # Height in cm (mandatory)
    volumetric_weight = models.FloatField(blank=True, null=True)  # Calculated: (L x W x H) / 5000
    applicable_weight = models.FloatField(blank=True, null=True)  # max(actual_weight, volumetric_weight)

    # Payment
    payment_mode = models.CharField(
        max_length=10,
        choices=PaymentMode.choices,
        default=PaymentMode.PREPAID
    )
    order_value = models.FloatField(default=0.0)  # For COD

    # Items Info
    item_type = models.CharField(max_length=100, blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    item_amount = models.FloatField(default=0.0)

    # Order Status & Tracking
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT
    )

    # Shipment Details (filled after carrier selection)
    selected_carrier = models.CharField(max_length=100, blank=True, null=True)
    total_cost = models.FloatField(blank=True, null=True)
    cost_breakdown = models.JSONField(blank=True, null=True)  # Stores the full breakdown
    awb_number = models.CharField(max_length=100, blank=True, null=True)  # Air Waybill number
    zone_applied = models.CharField(max_length=100, blank=True, null=True)
    mode = models.CharField(max_length=20, blank=True, null=True)  # Surface/Air

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    booked_at = models.DateTimeField(blank=True, null=True)

    # Additional metadata
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['selected_carrier']),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.recipient_name}"

    def save(self, *args, **kwargs):
        # Calculate volumetric weight if dimensions are provided
        if self.length and self.width and self.height:
            self.volumetric_weight = (self.length * self.width * self.height) / 5000
            self.applicable_weight = max(self.weight, self.volumetric_weight)
        else:
            self.applicable_weight = self.weight

        super().save(*args, **kwargs)
