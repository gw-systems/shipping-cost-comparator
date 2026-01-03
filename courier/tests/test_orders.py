"""
Tests for order CRUD endpoints
Migrated from FastAPI to Django
"""

import pytest
from django.urls import reverse
import json
from courier.models import Order, OrderStatus, PaymentMode


@pytest.mark.django_db
class TestCreateOrder:
    """Tests for creating orders"""

    def test_create_order_success(self, client, sample_order_data):
        """Test creating a new order"""
        response = client.post(
            reverse('courier:order-list'),
            data=json.dumps(sample_order_data),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.json()

        assert "order_number" in data
        assert data["status"] in ["pending", "draft"]
        assert data["sender_pincode"] == sample_order_data["sender_pincode"]
        assert data["recipient_pincode"] == sample_order_data["recipient_pincode"]

    def test_create_order_generates_order_number(self, client, sample_order_data):
        """Test that order number is auto-generated"""
        response = client.post(
            reverse('courier:order-list'),
            data=json.dumps(sample_order_data),
            content_type='application/json'
        )
        data = response.json()

        assert data["order_number"] is not None
        assert len(data["order_number"]) > 0

    def test_create_order_with_cod(self, client, sample_order_data):
        """Test creating COD order"""
        sample_order_data["payment_mode"] = "cod"
        response = client.post(
            reverse('courier:order-list'),
            data=json.dumps(sample_order_data),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.json()
        assert data["payment_mode"] == "cod"

    def test_create_order_invalid_payment_mode(self, client, sample_order_data):
        """Test invalid payment mode fails validation"""
        sample_order_data["payment_mode"] = "invalid"
        response = client.post(
            reverse('courier:order-list'),
            data=json.dumps(sample_order_data),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_order_missing_required_fields(self, client):
        """Test creating order with missing fields fails"""
        incomplete_data = {
            "sender_pincode": 400001
            # Missing other required fields
        }
        response = client.post(
            reverse('courier:order-list'),
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_order_negative_weight(self, client, sample_order_data):
        """Test negative weight validation"""
        sample_order_data["weight"] = -1.5
        response = client.post(
            reverse('courier:order-list'),
            data=json.dumps(sample_order_data),
            content_type='application/json'
        )

        # Should reject with 400 Bad Request
        assert response.status_code in [400, 422]  # Accept validation error codes


@pytest.mark.django_db
class TestGetOrders:
    """Tests for retrieving orders"""

    def test_get_all_orders(self, client):
        """Test getting all orders (public endpoint)"""
        response = client.get(reverse('courier:order-list'))

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)  # Could be paginated

    def test_get_order_by_id(self, client, sample_order):
        """Test getting a specific order by ID"""
        response = client.get(reverse('courier:order-detail', args=[sample_order.id]))

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_order.id

    def test_get_nonexistent_order(self, client):
        """Test getting non-existent order returns 404"""
        response = client.get(reverse('courier:order-detail', args=[99999]))

        assert response.status_code == 404


@pytest.mark.django_db
class TestUpdateOrder:
    """Tests for updating orders"""

    def test_update_order(self, client):
        """Test updating DRAFT order succeeds"""
        # Create a DRAFT order
        from courier.models import Order, OrderStatus, PaymentMode
        from datetime import datetime

        order = Order.objects.create(
            order_number=f"ORD-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            sender_pincode=400001,
            recipient_pincode=110001,
            recipient_name="Test Recipient",
            recipient_contact="9876543211",
            recipient_address="Test Address",
            weight=1.5,
            length=30.0,
            width=20.0,
            height=10.0,
            payment_mode=PaymentMode.PREPAID,
            status=OrderStatus.DRAFT,
        )

        update_data = {"recipient_name": "Updated Name"}

        response = client.patch(
            reverse('courier:order-detail', args=[order.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Cleanup
        order.delete()

    def test_update_order_carrier(self, client):
        """Test updating DRAFT order carrier info"""
        # Create a DRAFT order
        from courier.models import Order, OrderStatus, PaymentMode
        from datetime import datetime

        order = Order.objects.create(
            order_number=f"ORD-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            sender_pincode=400001,
            recipient_pincode=110001,
            recipient_name="Test Recipient",
            recipient_contact="9876543211",
            recipient_address="Test Address",
            weight=1.5,
            length=30.0,
            width=20.0,
            height=10.0,
            payment_mode=PaymentMode.PREPAID,
            status=OrderStatus.DRAFT,
        )

        update_data = {"recipient_address": "Updated Address"}

        response = client.patch(
            reverse('courier:order-detail', args=[order.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Cleanup
        order.delete()

    def test_update_non_draft_order_fails(self, client, sample_booked_order):
        """Test that updating non-DRAFT order fails"""
        update_data = {"recipient_name": "Should Fail"}

        response = client.patch(
            reverse('courier:order-detail', args=[sample_booked_order.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        # Should be forbidden since sample_booked_order is BOOKED
        assert response.status_code == 403

    def test_update_nonexistent_order(self, client):
        """Test updating non-existent order returns 404"""
        update_data = {"status": "in_transit"}

        response = client.patch(
            reverse('courier:order-detail', args=[99999]),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestOrderValidation:
    """Tests for order validation logic"""

    def test_order_date_created(self, client, sample_order_data):
        """Test that created_at timestamp is set"""
        response = client.post(
            reverse('courier:order-list'),
            data=json.dumps(sample_order_data),
            content_type='application/json'
        )
        data = response.json()

        assert "created_at" in data
