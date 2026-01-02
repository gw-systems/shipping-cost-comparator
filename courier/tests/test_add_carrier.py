"""
Tests for the Add Carrier endpoint
Migrated from FastAPI to Django
"""

import pytest
import json
import os
from django.urls import reverse
from django.conf import settings


RATE_CARD_PATH = os.path.join(settings.BASE_DIR, "courier", "data", "rate_cards.json")


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

        # Verify carrier was added to file
        with open(RATE_CARD_PATH, "r") as f:
            rates = json.load(f)

        carrier_names = [c["carrier_name"] for c in rates]
        assert "Test Express" in carrier_names

    def test_add_carrier_duplicate_name(self, client, admin_token, valid_carrier_data):
        """Test rejection of duplicate carrier name"""
        # First add the carrier
        client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        # Try to add again with same name
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
        assert response.json()["carrier"]["mode"] == "Air"

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

    def test_add_carrier_backup_created(self, client, admin_token, valid_carrier_data):
        """Test that backup file is created before adding carrier"""
        backup_path = RATE_CARD_PATH + ".bak"
        valid_carrier_data["carrier_name"] = "Backup Test Carrier"

        # Remove backup if exists
        if os.path.exists(backup_path):
            os.remove(backup_path)

        response = client.post(
            reverse('courier:admin-add-carrier'),
            data=json.dumps(valid_carrier_data),
            content_type='application/json',
            HTTP_X_ADMIN_TOKEN=admin_token
        )

        assert response.status_code in [200, 201]
        assert os.path.exists(backup_path), "Backup file should be created"
