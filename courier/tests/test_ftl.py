"""
Tests for FTL (Full Truck Load) Order functionality.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from courier.models import FTLOrder, OrderStatus


@pytest.mark.django_db
class TestFTLRoutes:
    """Test FTL routes endpoint."""

    def test_get_ftl_routes(self, client):
        """Test retrieving available FTL routes."""
        url = reverse('courier:get-ftl-routes')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert isinstance(data, dict)
        # Check that we have at least some routes
        assert len(data) > 0

        # Check that each source city has destinations
        for source_city, destinations in data.items():
            assert isinstance(destinations, list)
            assert len(destinations) > 0


@pytest.mark.django_db
class TestFTLRateCalculation:
    """Test FTL rate calculation endpoint."""

    def test_calculate_ftl_rate_success(self, client):
        """Test successful FTL rate calculation."""
        url = reverse('courier:calculate-ftl-rate')
        data = {
            'source_city': 'Bangalore',
            'destination_city': 'Bhiwandi',
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Check response structure
        assert 'source_city' in result
        assert 'destination_city' in result
        assert 'container_type' in result
        assert 'base_price' in result
        assert 'escalation_amount' in result
        assert 'price_with_escalation' in result
        assert 'gst_amount' in result
        assert 'total_price' in result

        # Check pricing calculation
        base_price = result['base_price']
        escalation = result['escalation_amount']
        assert escalation == base_price * 0.15  # 15% escalation

        price_with_escalation = result['price_with_escalation']
        assert price_with_escalation == base_price + escalation

        gst = result['gst_amount']
        assert gst == price_with_escalation * 0.18  # 18% GST

        total = result['total_price']
        assert total == price_with_escalation + gst

    def test_calculate_ftl_rate_invalid_route(self, client):
        """Test FTL rate calculation with invalid route."""
        url = reverse('courier:calculate-ftl-rate')
        data = {
            'source_city': 'InvalidCity',
            'destination_city': 'Bhiwandi',
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_calculate_ftl_rate_invalid_container(self, client):
        """Test FTL rate calculation with invalid container type."""
        url = reverse('courier:calculate-ftl-rate')
        data = {
            'source_city': 'Bangalore',
            'destination_city': 'Bhiwandi',
            'container_type': 'InvalidContainer'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestFTLOrderCreation:
    """Test FTL order creation."""

    def test_create_ftl_order_success(self, client):
        """Test successful FTL order creation."""
        url = reverse('courier:ftl-order-list')
        data = {
            'name': 'John Doe',
            'phone': '9876543210',
            'email': 'john@example.com',
            'source_city': 'Bangalore',
            'source_address': '123 Main Street, Bangalore, Karnataka',
            'source_pincode': 560001,
            'destination_city': 'Bhiwandi',
            'destination_pincode': 421302,
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()

        # Check order details
        assert result['name'] == 'John Doe'
        assert result['phone'] == '9876543210'
        assert result['email'] == 'john@example.com'
        assert result['source_city'] == 'Bangalore'
        assert result['source_address'] == '123 Main Street, Bangalore, Karnataka'
        assert result['source_pincode'] == 560001
        assert result['destination_city'] == 'Bhiwandi'
        assert result['container_type'] == '20FT'
        assert result['status'] == 'draft'
        assert 'order_number' in result
        assert result['order_number'].startswith('FTL-2026-')

        # Check pricing fields are calculated
        assert result['base_price'] > 0
        assert result['total_price'] > result['base_price']

    def test_create_ftl_order_without_email(self, client):
        """Test FTL order creation without email (optional field)."""
        url = reverse('courier:ftl-order-list')
        data = {
            'name': 'Jane Smith',
            'phone': '9123456789',
            'source_city': 'Bangalore',
            'source_address': '456 Test Road, Bangalore, Karnataka',
            'source_pincode': 560001,
            'destination_city': 'Noida',
            'destination_pincode': 201301,
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result['email'] is None

    def test_create_ftl_order_invalid_name(self, client):
        """Test FTL order creation with invalid name (contains numbers)."""
        url = reverse('courier:ftl-order-list')
        data = {
            'name': 'John123',  # Invalid: contains numbers
            'phone': '9876543210',
            'source_city': 'Bangalore',
            'source_address': '123 Main Street, Bangalore',
            'source_pincode': 560001,
            'destination_city': 'Bhiwandi',
            'destination_pincode': 421302,
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = response.json()
        assert 'name' in error

    def test_create_ftl_order_invalid_phone(self, client):
        """Test FTL order creation with invalid phone number."""
        url = reverse('courier:ftl-order-list')
        data = {
            'name': 'John Doe',
            'phone': '123',  # Invalid: not 10 digits
            'source_city': 'Bangalore',
            'source_address': '123 Main Street, Bangalore',
            'source_pincode': 560001,
            'destination_city': 'Bhiwandi',
            'destination_pincode': 421302,
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = response.json()
        assert 'phone' in error

    def test_create_ftl_order_short_address(self, client):
        """Test FTL order creation with address less than 10 characters."""
        url = reverse('courier:ftl-order-list')
        data = {
            'name': 'John Doe',
            'phone': '9876543210',
            'source_city': 'Bangalore',
            'source_address': 'Short',  # Invalid: too short
            'source_pincode': 560001,
            'destination_city': 'Bhiwandi',
            'destination_pincode': 421302,
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = response.json()
        assert 'source_address' in error

    def test_create_ftl_order_invalid_pincode(self, client):
        """Test FTL order creation with invalid pincode."""
        url = reverse('courier:ftl-order-list')
        data = {
            'name': 'John Doe',
            'phone': '9876543210',
            'source_city': 'Bangalore',
            'source_address': '123 Main Street, Bangalore',
            'source_pincode': 123,  # Invalid: not 6 digits
            'destination_city': 'Bhiwandi',
            'destination_pincode': 421302,
            'container_type': '20FT'
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = response.json()
        assert 'source_pincode' in error


@pytest.mark.django_db
class TestFTLOrderRetrieval:
    """Test FTL order retrieval."""

    def test_list_ftl_orders(self, client, sample_ftl_order):
        """Test listing all FTL orders."""
        url = reverse('courier:ftl-order-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Check for paginated response
        assert 'results' in data
        assert isinstance(data['results'], list)
        assert len(data['results']) > 0

    def test_get_ftl_order_detail(self, client, sample_ftl_order):
        """Test retrieving a specific FTL order."""
        url = reverse('courier:ftl-order-detail', kwargs={'pk': sample_ftl_order.id})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        order = response.json()
        assert order['id'] == sample_ftl_order.id
        assert order['order_number'] == sample_ftl_order.order_number

    def test_filter_ftl_orders_by_status(self, client, sample_ftl_order):
        """Test filtering FTL orders by status."""
        url = reverse('courier:ftl-order-list')
        response = client.get(url, {'status': 'draft'})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Check for paginated response
        assert 'results' in data
        orders = data['results']
        assert all(order['status'] == 'draft' for order in orders)


@pytest.mark.django_db
class TestFTLOrderUpdate:
    """Test FTL order update functionality."""

    def test_update_draft_ftl_order(self, client, sample_ftl_order):
        """Test updating a DRAFT FTL order."""
        url = reverse('courier:ftl-order-detail', kwargs={'pk': sample_ftl_order.id})
        data = {
            'name': 'Updated Name',
            'phone': '9999999999',
            'source_city': sample_ftl_order.source_city,
            'source_address': 'Updated Address Street, City',
            'source_pincode': sample_ftl_order.source_pincode,
            'destination_city': sample_ftl_order.destination_city,
            'destination_pincode': sample_ftl_order.destination_pincode,
            'container_type': sample_ftl_order.container_type
        }

        response = client.patch(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['name'] == 'Updated Name'
        assert result['phone'] == '9999999999'

    def test_update_booked_ftl_order_fails(self, client, sample_booked_ftl_order):
        """Test that updating a BOOKED FTL order fails."""
        url = reverse('courier:ftl-order-detail', kwargs={'pk': sample_booked_ftl_order.id})
        data = {
            'name': 'Updated Name'
        }

        response = client.patch(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestFTLOrderBooking:
    """Test FTL order booking functionality."""

    def test_book_ftl_orders_success(self, client, sample_ftl_order):
        """Test booking DRAFT FTL orders."""
        url = '/api/ftl-orders/book/'
        data = {
            'order_ids': [sample_ftl_order.id]
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['status'] == 'success'
        assert len(result['orders_booked']) == 1

        # Verify order status changed to BOOKED
        sample_ftl_order.refresh_from_db()
        assert sample_ftl_order.status == OrderStatus.BOOKED
        assert sample_ftl_order.booked_at is not None

    def test_book_multiple_ftl_orders(self, client):
        """Test booking multiple FTL orders at once."""
        # Create multiple FTL orders
        order1 = FTLOrder.objects.create(
            order_number='FTL-TEST-001',
            name='Test User 1',
            phone='9876543210',
            source_city='Bangalore',
            source_address='Address 1',
            source_pincode=560001,
            destination_city='Bhiwandi',
            destination_pincode=421302,
            container_type='20FT',
            base_price=25000,
            escalation_amount=3750,
            price_with_escalation=28750,
            gst_amount=5175,
            total_price=33925,
            status=OrderStatus.DRAFT
        )
        order2 = FTLOrder.objects.create(
            order_number='FTL-TEST-002',
            name='Test User 2',
            phone='9123456789',
            source_city='Bangalore',
            source_address='Address 2',
            source_pincode=560001,
            destination_city='Noida',
            destination_pincode=201301,
            container_type='20FT',
            base_price=30000,
            escalation_amount=4500,
            price_with_escalation=34500,
            gst_amount=6210,
            total_price=40710,
            status=OrderStatus.DRAFT
        )

        url = '/api/ftl-orders/book/'
        data = {
            'order_ids': [order1.id, order2.id]
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result['orders_booked']) == 2

        # Verify both orders are booked
        order1.refresh_from_db()
        order2.refresh_from_db()
        assert order1.status == OrderStatus.BOOKED
        assert order2.status == OrderStatus.BOOKED

    def test_book_already_booked_order_fails(self, client, sample_booked_ftl_order):
        """Test that booking an already BOOKED order fails."""
        url = '/api/ftl-orders/book/'
        data = {
            'order_ids': [sample_booked_ftl_order.id]
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_book_ftl_orders_no_ids(self, client):
        """Test booking FTL orders without providing IDs."""
        url = '/api/ftl-orders/book/'
        data = {
            'order_ids': []
        }

        response = client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestFTLOrderDeletion:
    """Test FTL order deletion functionality."""

    def test_delete_draft_ftl_order(self, client, sample_ftl_order):
        """Test deleting a DRAFT FTL order."""
        url = reverse('courier:ftl-order-detail', kwargs={'pk': sample_ftl_order.id})

        response = client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify order is deleted
        assert not FTLOrder.objects.filter(id=sample_ftl_order.id).exists()

    def test_delete_booked_ftl_order_fails(self, client, sample_booked_ftl_order):
        """Test that deleting a BOOKED FTL order fails."""
        url = reverse('courier:ftl-order-detail', kwargs={'pk': sample_booked_ftl_order.id})

        response = client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verify order still exists
        assert FTLOrder.objects.filter(id=sample_booked_ftl_order.id).exists()
