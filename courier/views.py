"""
Django REST Framework Views.
Converted from FastAPI routes to DRF ViewSets and APIViews.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.http import FileResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json
import os
import shutil
import logging

from .models import Order, OrderStatus, PaymentMode
from .serializers import (
    OrderSerializer, OrderUpdateSerializer, RateRequestSerializer,
    CarrierSelectionSerializer, NewCarrierSerializer
)
from .permissions import IsAdminToken
from .engine import calculate_cost
from .zones import get_zone_column, PINCODE_LOOKUP
from django.conf import settings

logger = logging.getLogger('courier')

# Path configurations
BASE_DIR = settings.BASE_DIR
RATE_CARD_PATH = os.path.join(BASE_DIR, "courier", "data", "rate_cards.json")


def load_rates():
    """Load rate cards with error handling"""
    try:
        if not os.path.exists(RATE_CARD_PATH):
            logger.warning(f"Rate card file not found at {RATE_CARD_PATH}, returning empty list")
            return []

        with open(RATE_CARD_PATH, "r") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rate card file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading rate cards: {e}")
        return []


def generate_order_number():
    """Generate unique order number"""
    today = timezone.now()
    prefix = f"ORD-{today.year}-"

    # Get the latest order number for today
    latest_order = (
        Order.objects
        .filter(order_number__startswith=prefix)
        .order_by('-id')
        .first()
    )

    if latest_order:
        try:
            last_num = int(latest_order.order_number.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1001
    else:
        new_num = 1001

    return f"{prefix}{new_num}"


# ============================================================================
# PUBLIC API ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for monitoring"""
    return Response({
        "status": "healthy",
        "pincode_db_loaded": len(PINCODE_LOOKUP) > 0,
        "pincode_count": len(PINCODE_LOOKUP),
        "rate_cards_loaded": len(load_rates()) > 0,
        "rate_card_count": len(load_rates())
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def root_redirect(request):
    """Redirect to dashboard"""
    return redirect('/static/dashboard.html')


@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
@permission_classes([AllowAny])
def compare_rates(request):
    """Compare shipping rates across carriers"""
    serializer = RateRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    zone_key, zone_label = get_zone_column(
        data['source_pincode'],
        data['dest_pincode']
    )

    rates = load_rates()
    results = []

    for carrier in rates:
        if not carrier.get("active", True):
            continue

        req_mode = data['mode'].lower()
        car_mode = carrier.get("mode", "Surface").lower()
        if req_mode != "both" and car_mode != req_mode:
            continue

        try:
            res = calculate_cost(
                weight=data['weight'],
                zone_key=zone_key,
                carrier_data=carrier,
                is_cod=data['is_cod'],
                order_value=data['order_value']
            )

            res["applied_zone"] = zone_label
            res["mode"] = carrier.get("mode", "Surface")
            results.append(res)
        except Exception as e:
            logger.error(f"CALCULATION_ERROR: Carrier {carrier.get('carrier_name')} failed. Error: {str(e)}")
            continue

    if not results:
        logger.warning(f"No carriers matched for mode: {data['mode']}")
        return Response(
            {"detail": f"No active carriers found for mode '{data['mode']}'."},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(sorted(results, key=lambda x: x["total_cost"]))


# ============================================================================
# ORDER MANAGEMENT ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def lookup_pincode(request, pincode):
    """Get city and state for a pincode"""
    pincode_data = PINCODE_LOOKUP.get(int(pincode))

    if not pincode_data:
        return Response(
            {"detail": "Pincode not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        "pincode": pincode,
        "city": pincode_data.get("district", ""),
        "state": pincode_data.get("state", ""),
        "office": pincode_data.get("office", "")
    })


class OrderViewSet(viewsets.ModelViewSet):
    """Order management ViewSet"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'partial_update' or self.action == 'update':
            return OrderUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.all()
        status_param = self.request.query_params.get('status')

        if status_param:
            try:
                queryset = queryset.filter(status=status_param)
            except ValueError:
                pass

        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Create a new order"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Generate order number
        order_number = generate_order_number()

        # Create order
        order = serializer.save(
            order_number=order_number,
            status=OrderStatus.DRAFT
        )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        """Delete an order (only if DRAFT)"""
        order = self.get_object()

        if order.status != OrderStatus.DRAFT:
            return Response(
                {"detail": "Can only delete orders in DRAFT status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='compare-carriers')
    def compare_carriers(self, request):
        """Compare carrier rates for one or more orders"""
        order_ids = request.data.get('order_ids', [])

        if not order_ids:
            return Response(
                {"detail": "No orders provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        orders = Order.objects.filter(id__in=order_ids)

        if orders.count() != len(order_ids):
            return Response(
                {"detail": "One or more orders not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Aggregate weights and use first order's pincodes
        total_weight = sum(order.applicable_weight or order.weight for order in orders)
        first_order = orders.first()
        source_pincode = first_order.sender_pincode
        dest_pincode = first_order.recipient_pincode

        # Check if COD
        is_cod = any(order.payment_mode == PaymentMode.COD for order in orders)
        total_order_value = sum(
            order.order_value for order in orders
            if order.payment_mode == PaymentMode.COD
        )

        # Get zone
        zone_key, zone_label = get_zone_column(source_pincode, dest_pincode)

        # Load carriers
        rates = load_rates()
        results = []

        for carrier in rates:
            if not carrier.get("active", True):
                continue

            try:
                res = calculate_cost(
                    weight=total_weight,
                    zone_key=zone_key,
                    carrier_data=carrier,
                    is_cod=is_cod,
                    order_value=total_order_value
                )

                res["applied_zone"] = zone_label
                res["mode"] = carrier.get("mode", "Surface")
                res["order_count"] = len(order_ids)
                res["total_weight"] = total_weight
                results.append(res)

            except Exception:
                continue

        if not results:
            return Response(
                {"detail": "No active carriers found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "orders": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "recipient_name": order.recipient_name,
                    "weight": order.applicable_weight or order.weight
                }
                for order in orders
            ],
            "carriers": sorted(results, key=lambda x: x["total_cost"]),
            "source_pincode": source_pincode,
            "dest_pincode": dest_pincode,
            "total_weight": total_weight
        })

    @action(detail=False, methods=['post'], url_path='book-carrier')
    def book_carrier(self, request):
        """Book a carrier for selected orders"""
        serializer = CarrierSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        orders = Order.objects.filter(id__in=data['order_ids'])

        if orders.count() != len(data['order_ids']):
            return Response(
                {"detail": "One or more orders not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate rates
        total_weight = sum(order.applicable_weight or order.weight for order in orders)
        first_order = orders.first()
        source_pincode = first_order.sender_pincode
        dest_pincode = first_order.recipient_pincode
        is_cod = any(order.payment_mode == PaymentMode.COD for order in orders)
        total_order_value = sum(
            order.order_value for order in orders
            if order.payment_mode == PaymentMode.COD
        )

        zone_key, zone_label = get_zone_column(source_pincode, dest_pincode)

        # Find the carrier
        rates = load_rates()
        carrier_data = None
        for carrier in rates:
            if (carrier.get("carrier_name") == data['carrier_name'] and
                    carrier.get("mode") == data['mode']):
                carrier_data = carrier
                break

        if not carrier_data:
            return Response(
                {"detail": "Carrier not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate cost
        cost_result = calculate_cost(
            weight=total_weight,
            zone_key=zone_key,
            carrier_data=carrier_data,
            is_cod=is_cod,
            order_value=total_order_value
        )

        # Update all orders
        for order in orders:
            order.selected_carrier = data['carrier_name']
            order.mode = data['mode']
            order.zone_applied = zone_label
            order.total_cost = cost_result["total_cost"]
            order.cost_breakdown = cost_result["breakdown"]
            order.status = OrderStatus.BOOKED
            order.booked_at = timezone.now()
            order.save()

        return Response({
            "status": "success",
            "message": f"{orders.count()} order(s) booked with {data['carrier_name']}",
            "orders_updated": [order.order_number for order in orders],
            "total_cost": cost_result["total_cost"],
            "carrier": data['carrier_name'],
            "mode": data['mode']
        })


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAdminToken])
def get_all_rates(request):
    """Get all carrier rates"""
    with open(RATE_CARD_PATH, "r") as f:
        return Response(json.load(f))


@api_view(['POST'])
@permission_classes([IsAdminToken])
def update_rates(request):
    """Update carrier rates"""
    try:
        new_data = request.data

        if os.path.exists(RATE_CARD_PATH):
            shutil.copy(RATE_CARD_PATH, RATE_CARD_PATH + ".bak")

        with open(RATE_CARD_PATH, "w") as f:
            json.dump(new_data, f, indent=4)

        logger.info("ADMIN_ACTION: Rates updated successfully.")
        return Response({"status": "success", "message": "Rates updated successfully"})
    except Exception as e:
        logger.error(f"ADMIN_ERROR: Failed to update rates: {str(e)}")
        return Response(
            {"detail": f"Failed to update rates: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminToken])
def add_carrier(request):
    """Add a new carrier to the rate cards"""
    serializer = NewCarrierSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    carrier_data = serializer.validated_data

    try:
        # Load existing rates
        existing_rates = load_rates()

        # Check for duplicate carrier name
        carrier_names = [c.get("carrier_name", "").lower() for c in existing_rates]
        if carrier_data['carrier_name'].lower() in carrier_names:
            logger.warning(f"ADMIN_ACTION: Duplicate carrier name attempted: {carrier_data['carrier_name']}")
            return Response(
                {"detail": f"Carrier '{carrier_data['carrier_name']}' already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Append new carrier
        existing_rates.append(carrier_data)

        # Backup and save
        if os.path.exists(RATE_CARD_PATH):
            shutil.copy(RATE_CARD_PATH, RATE_CARD_PATH + ".bak")

        with open(RATE_CARD_PATH, "w") as f:
            json.dump(existing_rates, f, indent=4)

        logger.info(f"ADMIN_ACTION: New carrier added: {carrier_data['carrier_name']}")
        return Response({
            "status": "success",
            "message": f"Carrier '{carrier_data['carrier_name']}' added successfully",
            "carrier": carrier_data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"ADMIN_ERROR: Failed to add carrier: {str(e)}")
        return Response(
            {"detail": f"Failed to add carrier: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
