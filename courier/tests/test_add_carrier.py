"""
Tests for the Add Carrier endpoint
Migrated from FastAPI to Django
"""

import pytest
import json
from django.urls import reverse
from courier.models import Courier

@pytest.mark.django_db
class TestAddCarrier:
    """Tests for adding carriers"""

    def test_add_carrier_success(self, client, admin_token, valid_carrier_data):
        """Test successful addition of a new carrier"""
        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code in [200, 201]  # Accept both OK and Created
        data = response.json()
        assert data["status"] == "success"
        assert "added successfully" in data["message"]

        # Verify carrier was added to DB
        assert Courier.objects.filter(name="Test Express").exists()
        courier = Courier.objects.get(name="Test Express")
        assert courier.carrier_mode == "Surface"

    def test_add_carrier_duplicate_name(self, client, admin_token, valid_carrier_data):
        """Test rejection of duplicate carrier name"""
        # First add the carrier to DB directly
        Courier.objects.create(name="Test Express", carrier_mode="Surface", min_weight=0.5)

        # Try to add again via API
        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_add_carrier_no_auth(self, client, valid_carrier_data):
        """Test that endpoint requires authentication"""
        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json'
        )

        assert response.status_code in [401, 403]  # Accept both Unauthorized and Forbidden

    def test_add_carrier_invalid_auth(self, client, valid_carrier_data):
        """Test that endpoint rejects invalid token"""
        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN="wrong-token"
        )

        assert response.status_code in [401, 403]  # Accept both Unauthorized and Forbidden

    def test_add_carrier_missing_required_field(self, client, admin_token, valid_carrier_data):
        """Test validation when required field is missing"""
        del valid_carrier_data["carrier_name"]

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400

    def test_add_carrier_empty_name(self, client, admin_token, valid_carrier_data):
        """Test validation rejects empty carrier name"""
        valid_carrier_data["carrier_name"] = ""

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400

    def test_add_carrier_invalid_mode(self, client, admin_token, valid_carrier_data):
        """Test validation rejects invalid mode"""
        valid_carrier_data["mode"] = "Express"  # Only Surface/Air allowed

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400

    def test_add_carrier_negative_min_weight(self, client, admin_token, valid_carrier_data):
        """Test validation rejects negative min_weight"""
        valid_carrier_data["min_weight"] = -0.5

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400

    def test_add_carrier_zero_min_weight(self, client, admin_token, valid_carrier_data):
        """Test validation rejects zero min_weight"""
        valid_carrier_data["min_weight"] = 0

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400

    def test_add_carrier_negative_forward_rate(self, client, admin_token, valid_carrier_data):
        """Test validation rejects negative forward rates"""
        valid_carrier_data["forward_rates"]["z_a"] = -10.0

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400

    def test_add_carrier_air_mode(self, client, admin_token, valid_carrier_data):
        """Test adding carrier with Air mode"""
        valid_carrier_data["mode"] = "Air"
        valid_carrier_data["carrier_name"] = "Air Express"

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code in [200, 201]
        assert "Air Express" in response.json()["message"]
        assert Courier.objects.filter(name="Air Express", carrier_mode="Air").exists()

    def test_add_carrier_missing_forward_rate_zone(self, client, admin_token, valid_carrier_data):
        """Test validation when a forward rate zone is missing"""
        del valid_carrier_data["forward_rates"]["z_f"]

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code == 400
