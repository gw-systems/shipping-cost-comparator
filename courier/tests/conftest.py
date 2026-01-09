"""
Pytest configuration and fixtures for Courier Module tests
Migrated from FastAPI to Django
"""

import pytest
import os
import json
import shutil
from django.conf import settings
from django.test import Client
from courier.models import Order, OrderStatus, PaymentMode, FTLOrder, Courier, CourierZoneRate, SystemConfig
from datetime import datetime
from django.utils import timezone
from courier.models import Order, OrderStatus, PaymentMode, FTLOrder, Courier, CourierZoneRate, SystemConfig, FeeStructure, FuelConfiguration, ServiceConstraints, RoutingLogic, CityRoute


# Path to rate cards
RATE_CARD_PATH = os.path.join(settings.BASE_DIR, "courier", "data", "rate_cards.json")


@pytest.fixture(scope="session")
@pytest.mark.django_db
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Setup test database with required data
    """
    with django_db_blocker.unblock():
        # Create SystemConfig if it doesn't exist
        SystemConfig.objects.get_or_create(
            pk=1,
            defaults={
                'diesel_price_current': 95.0,
                'base_diesel_price': 90.0,
                'escalation_rate': 0.15,
                'gst_rate': 0.18
            }
        )


@pytest.fixture
def client():
    """
    Django test client fixture
    """
    return Client()


@pytest.fixture
def admin_token():
    """
    Admin authentication token for protected routes.
    Returns the plaintext password (not the hash).
    The authentication system will hash it and compare with ADMIN_PASSWORD_HASH.
    """
    # For tests, we use the known password that matches the hash in .env
    # In production, users provide their actual password which gets hashed and compared
    return "AdminSecure@2025"


@pytest.fixture
def sample_rate_request():
    """
    Sample valid rate comparison request
    """
    return {
        "source_pincode": 400001,  # Mumbai
        "dest_pincode": 110001,  # Delhi
        "weight": 1.5,
        "is_cod": True,
        "order_value": 2000,
        "mode": "Both",
    }


@pytest.fixture
def sample_carrier_data():
    """
    Sample carrier configuration for testing calculations
    """
    return {
        "carrier_name": "Test Carrier",
        "mode": "Surface",
        "min_weight": 0.5,
        "forward_rates": {
            "z_a": 30.0,
            "z_b": 35.0,
            "z_c": 40.0,
            "z_d": 45.0,
            "z_f": 60.0,
        },
        "additional_rates": {
            "z_a": 25.0,
            "z_b": 28.0,
            "z_c": 32.0,
            "z_d": 36.0,
            "z_f": 45.0,
        },
        "cod_fixed": 30.0,
        "cod_percent": 0.015,
    }


@pytest.fixture
def mock_rate_cards(tmp_path):
    """
    Create a temporary rate cards JSON file for testing
    """
    rate_cards = [
        {
            "carrier_name": "Test Surface",
            "mode": "Surface",
            "active": True,
            "min_weight": 0.5,
            "forward_rates": {
                "z_a": 29.43,
                "z_b": 32.1,
                "z_c": 38.79,
                "z_d": 44.14,
                "z_f": 56.18,
            },
            "additional_rates": {
                "z_a": 25.41,
                "z_b": 28.09,
                "z_c": 33.44,
                "z_d": 36.11,
                "z_f": 40.13,
            },
            "cod_fixed": 27.69,
            "cod_percent": 0.0188,
        }
    ]

    file_path = tmp_path / "rate_cards.json"
    with open(file_path, "w") as f:
        json.dump(rate_cards, f)

    return str(file_path)


@pytest.fixture(scope="function", autouse=True)
def restore_rate_cards():
    """
    Backup and restore rate_cards.json before and after each test
    This ensures test isolation for add/update carrier tests
    """
    backup_path = RATE_CARD_PATH + ".test_backup"

    # Backup before test
    if os.path.exists(RATE_CARD_PATH):
        shutil.copy(RATE_CARD_PATH, backup_path)

    yield

    # Restore after test
    if os.path.exists(backup_path):
        shutil.copy(backup_path, RATE_CARD_PATH)
        os.remove(backup_path)


@pytest.fixture
@pytest.mark.django_db
def sample_order(db):
    """
    Create a sample order in the database for testing
    """
    order = Order.objects.create(
        order_number=f"ORD-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        sender_pincode=400001,
        sender_name="Test Sender",
        sender_phone="9876543210",
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

    yield order

    # Cleanup
    order.delete()


@pytest.fixture
@pytest.mark.django_db
def sample_booked_order(db):
    """
    Create a booked order for testing analytics
    """
    order = Order.objects.create(
        order_number=f"ORD-BOOKED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        sender_pincode=400001,
        sender_name="Test Sender",
        sender_phone="9876543210",
        recipient_pincode=110001,
        recipient_name="Test Recipient",
        recipient_contact="9876543211",
        recipient_address="Test Address",
        weight=2.0,
        length=30.0,
        width=20.0,
        height=10.0,
        payment_mode=PaymentMode.COD,
        status=OrderStatus.BOOKED,
        mode="Surface",
        zone_applied="Zone C",
        total_cost=150.00,
    )

    yield order

    # Cleanup
    order.delete()


@pytest.fixture
def sample_order_data():
    """
    Sample order data for creating new orders
    """
    return {
        "sender_pincode": 400001,
        "sender_name": "John Doe",
        "sender_phone": "9876543210",
        "recipient_pincode": 110001,
        "recipient_name": "Jane Smith",
        "recipient_contact": "9876543211",
        "recipient_address": "123 Test Street, Test Area",
        "weight": 1.5,
        "length": 30.0,
        "width": 20.0,
        "height": 10.0,
        "payment_mode": "prepaid",
        "order_value": 1000.0,
    }


@pytest.fixture
def valid_carrier_data():
    """Fixture providing valid carrier data for testing"""
    return {
        "carrier_name": "Test Express",
        "mode": "Surface",
        "min_weight": 0.5,
        "active": True,
        "forward_rates": {
            "z_a": 35.0,
            "z_b": 40.0,
            "z_c": 45.0,
            "z_d": 50.0,
            "z_f": 55.0,
        },
        "additional_rates": {
            "z_a": 5.0,
            "z_b": 6.0,
            "z_c": 7.0,
            "z_d": 8.0,
            "z_f": 9.0,
        },
        "cod_fixed": 25.0,
        "cod_percent": 0.015,
    }


@pytest.fixture
@pytest.mark.django_db
def sample_ftl_order(db):
    """
    Create a sample FTL order in DRAFT status for testing
    """
    order = FTLOrder.objects.create(
        order_number=f"FTL-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name="Test Customer",
        email="test@example.com",
        phone="9876543210",
        source_city="Bangalore",
        source_address="123 Test Street, Bangalore, Karnataka",
        source_pincode=560001,
        destination_city="Bhiwandi",
        destination_pincode=421302,
        container_type="20FT",
        base_price=25000.00,
        escalation_amount=3750.00,  # 15% of base
        price_with_escalation=28750.00,  # base + escalation
        gst_amount=5175.00,  # 18% of price_with_escalation
        total_price=33925.00,  # price_with_escalation + gst
        status=OrderStatus.DRAFT,
    )

    yield order

    # Cleanup
    order.delete()


@pytest.fixture
@pytest.mark.django_db
def sample_booked_ftl_order(db):
    """
    Create a sample FTL order in BOOKED status for testing
    """
    order = FTLOrder.objects.create(
        order_number=f"FTL-BOOKED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name="Booked Customer",
        email="booked@example.com",
        phone="9123456789",
        source_city="Bangalore",
        source_address="456 Booked Avenue, Bangalore, Karnataka",
        source_pincode=560001,
        destination_city="Noida",
        destination_pincode=201301,
        container_type="20FT",
        base_price=30000.00,
        escalation_amount=4500.00,  # 15% of base
        price_with_escalation=34500.00,  # base + escalation
        gst_amount=6210.00,  # 18% of price_with_escalation
        total_price=40710.00,  # price_with_escalation + gst
        status=OrderStatus.BOOKED,
        booked_at=timezone.now(),
    )

    yield order

    # Cleanup
    order.delete()


# ============================================================================
# COURIER FIXTURES FOR PRICE VERIFICATION TESTS
# ============================================================================

def create_courier_with_zones(name, mode, min_weight, zone_rates_data):
    """
    Helper function to create a courier with zone rates
    
    Args:
        name: Courier name
        mode: Surface or Air
        min_weight: Minimum weight slab
        zone_rates_data: Dict with 'forward' and 'additional' zone rates
    """
    courier = Courier.objects.create(
        name=name,
        carrier_type="Courier",
        carrier_mode=mode,
        is_active=True,
        min_weight=min_weight,
        volumetric_divisor=4500
    )
    
    # Create forward rates
    for zone_code, rate in zone_rates_data['forward'].items():
        CourierZoneRate.objects.create(
            courier=courier,
            zone_code=zone_code,
            rate_type=CourierZoneRate.RateType.FORWARD,
            rate=rate
        )
    
    # Create additional rates
    for zone_code, rate in zone_rates_data['additional'].items():
        CourierZoneRate.objects.create(
            courier=courier,
            zone_code=zone_code,
            rate_type=CourierZoneRate.RateType.ADDITIONAL,
            rate=rate
        )
    
    return courier


@pytest.fixture(scope="session")
@pytest.mark.django_db
def setup_test_couriers(django_db_setup, django_db_blocker):
    """
    Create all required couriers for price verification tests
    This runs once per test session
    """
    with django_db_blocker.unblock():
        # Delhivery Surface 0.5kg
        if not Courier.objects.filter(name='Delhivery Surface 0.5kg').exists():
            delhivery = create_courier_with_zones(
                name='Delhivery Surface 0.5kg',
                mode='Surface',
                min_weight=0.5,
                zone_rates_data={
                    'forward': {'z_a': 27.0, 'z_b': 30.0, 'z_c': 36.0, 'z_d': 41.0, 'z_e': 69.0, 'z_f': 69.0},
                    'additional': {'z_a': 26.0, 'z_b': 32.0, 'z_c': 36.0, 'z_d': 42.0, 'z_e': 67.0, 'z_f': 67.0}
                }
            )
            try:
                if not hasattr(delhivery, 'fees_config'):
                    FeeStructure.objects.create(
                        courier_link=delhivery,
                        cod_fixed=29.0,
                        cod_percent=1.5
                    )
                else:
                    # If it exists (e.g. signal created it), update it
                    delhivery.fees_config.cod_fixed = 29.0
                    delhivery.fees_config.cod_percent = 1.5
                    delhivery.fees_config.save()
            except Exception:
                 # Fallback if hasattr fails (shouldn't)
                 FeeStructure.objects.create(
                        courier_link=delhivery,
                        cod_fixed=29.0,
                        cod_percent=1.5
                 )
            
            delhivery.save()
        
        # ACPL Surface 50kg
        if not Courier.objects.filter(name='ACPL Surface 50kg').exists():
            # Create a mock CSV for testing (using a unique name to avoid conflicts)
            csv_path = os.path.join(settings.BASE_DIR, "courier", "data", "ACPL_Test_Pincodes.csv")
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            with open(csv_path, "w") as f:
                f.write("Pincode,CITY,State\n")
                f.write("370201,GANDHIDHAM,Gujarat\n")
                f.write("421308,BHIWANDI,Maharashtra\n")

            acpl = create_courier_with_zones(
                name='ACPL Surface 50kg',
                mode='Surface',
                min_weight=50.0,
                zone_rates_data={
                    'forward': {'z_a': 200.0, 'z_b': 250.0, 'z_c': 300.0, 'z_d': 350.0, 'z_f': 450.0},
                    'additional': {'z_a': 18.0, 'z_b': 22.0, 'z_c': 26.0, 'z_d': 30.0, 'z_f': 40.0}
                }
            )
            
            # Configure Routing Logic (City to City)
            # CourierManager creates a default RoutingLogic, so we must update it
            rl = acpl.routing_config
            rl.logic_type = "City_To_City"
            rl.hub_city = "bhiwandi"
            rl.serviceable_pincode_csv = "ACPL_Test_Pincodes.csv"
            rl.save()

            # Configure Fees
            fees = acpl.fees_config
            fees.hamali_per_kg = 0.5
            fees.min_hamali = 50.0
            fees.docket_fee = 50.0
            fees.save()
            
            # Configure Fuel
            fuel = acpl.fuel_config_obj
            fuel.is_dynamic = False
            fuel.surcharge_percent = 0.10  # 10%
            fuel.save()
            
            # Also set City Rates (Forward Rates are used as fallback or mapped? 
            # In City-to-City, the zone_id usually becomes the City Name.
            # So we need rates for 'gandhidham'.
            CityRoute.objects.create(courier=acpl, city_name='gandhidham', rate_per_kg=5.0) 
            # Note: City-to-city usually uses Per KG rate, not slab. Let's assume standard per-kg for now.
            
            acpl.save()
        
        # Blue Dart
        if not Courier.objects.filter(name='Blue Dart').exists():
            # Create Mock CSV
            csv_path = os.path.join(settings.BASE_DIR, "courier", "data", "BlueDart_Test_Pincodes.csv")
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            with open(csv_path, "w") as f:
                f.write("Pincode,REGION,STATE,Extended Delivery Location,EDL Distance\n")
                f.write("421308,WEST,MAHARASHTRA,N,0\n")
                f.write("110001,NORTH,DELHI,N,0\n")
                f.write("781001,EAST,ASSAM,Y,10\n") # Example EDL

            bluedart = create_courier_with_zones(
                name='Blue Dart',
                mode='Air',
                min_weight=0.5,
                zone_rates_data={
                    'forward': {'WEST': 50.0, 'NORTH': 60.0, 'EAST': 70.0, 'SOUTH': 80.0},
                    'additional': {'WEST': 40.0, 'NORTH': 50.0, 'EAST': 60.0, 'SOUTH': 70.0}
                }
            )
            
            # Update Routing Logic
            rl = bluedart.routing_config
            rl.logic_type = "Region_CSV"
            rl.serviceable_pincode_csv = "BlueDart_Test_Pincodes.csv"
            rl.save()

            # Configure Fees
            fees = bluedart.fees_config
            fees.docket_fee = 100.0
            fees.cod_fixed = 50.0
            fees.cod_percent = 2.0
            fees.save()
            
            # Configure Fuel
            fuel = bluedart.fuel_config_obj
            fuel.is_dynamic = False
            fuel.surcharge_percent = 0.556 # 55.6%
            fuel.save()
            
            bluedart.save()
        
        # Shadowfax Surface 0.5kg
        if not Courier.objects.filter(name='Shadowfax Surface 0.5kg').exists():
            shadowfax = create_courier_with_zones(
                name='Shadowfax Surface 0.5kg',
                mode='Surface',
                min_weight=0.5,
                zone_rates_data={
                    'forward': {'z_a': 30.0, 'z_b': 35.0, 'z_c': 40.0, 'z_d': 45.0, 'z_f': 60.0},
                    'additional': {'z_a': 25.0, 'z_b': 28.0, 'z_c': 32.0, 'z_d': 36.0, 'z_f': 45.0}
                }
            )
            
            # Configure Fees - Handle potential existing config (from signals etc)
            try:
                if hasattr(shadowfax, 'fees_config'):
                    fees = shadowfax.fees_config
                    fees.cod_fixed = 30.0
                    fees.cod_percent = 1.5
                    fees.save()
                else:
                    FeeStructure.objects.create(
                        courier_link=shadowfax,
                        cod_fixed=30.0,
                        cod_percent=1.5
                    )
            except Exception:
                 # Fallback if hasattr fails (shouldn't)
                 FeeStructure.objects.create(
                    courier_link=shadowfax,
                    cod_fixed=30.0,
                    cod_percent=1.5
                 )
        
        # V-Trans 100kg
        if not Courier.objects.filter(name='V-Trans 100kg').exists():
            vtrans = create_courier_with_zones(
                name='V-Trans 100kg',
                mode='Surface',
                min_weight=100.0,
                zone_rates_data={
                    'forward': {'z_a': 300.0, 'z_b': 350.0, 'z_c': 400.0, 'z_d': 450.0, 'z_f': 550.0},
                    'additional': {'z_a': 20.0, 'z_b': 25.0, 'z_c': 30.0, 'z_d': 35.0, 'z_f': 45.0}
                }
            )


@pytest.fixture(autouse=True)
@pytest.mark.django_db
def ensure_test_couriers(db, setup_test_couriers):
    """
    Ensure test couriers are available for each test
    This fixture runs automatically for all tests
    """
    pass
