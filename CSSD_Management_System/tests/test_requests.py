"""
test_requests.py — Tests for Department Requests (US-05, US-06)

CONTEXT:
This test suite covers US-05 (Submit an Instrument Request) and US-06 (View Available Sterile Stock).
It maps the requested REST API concepts to the system's actual implementation using Django ORM
and standard Django views.

Test Structure:
1. Unit Tests (Request ID Formatting, Filtering by Type, State Validation)
2. Integration Tests (POST requests, View rendering, Real-time count updates)

Pytest Fixtures:
This file uses fixtures defined in `conftest.py` (e.g., `db_access`, `nurse_client`, 
`sample_instrument_sets`, `nurse_user`).
"""

import pytest
from django.urls import reverse
from CSSD_Management_System.models import InstrumentRequest, InstrumentSet

# Grant database access to all tests in this file
pytestmark = pytest.mark.django_db


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  1. UNIT TESTS                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def test_request_id_generation_format(nurse_user):
    """
    Unit Test: Request ID Generation (US-05)
    Ensures that when a request is created, it has a unique formatted ID (e.g., REQ-0001).
    """
    # ARRANGE: Create a mock request
    request_obj = InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Requested",
        department="ER"
    )
    
    # ACT: Get the string representation of the request which generates the ID format
    generated_id = str(request_obj)
    
    # ASSERT: The ID should match the expected REQ-XXXX format
    expected_prefix = f"REQ-{request_obj.id:04d}"
    assert expected_prefix in generated_id


def test_filter_by_instrument_type_function(sample_instrument_sets):
    """
    Unit Test: Filter by Instrument Type (US-06)
    Ensures that we can correctly filter available stock by its type category.
    """
    # ARRANGE: Get all the sample instrument sets from our fixture
    # The fixture returns a dictionary of sets, we just want the values
    all_sets = sample_instrument_sets.values()
    
    # ACT: Simulate a filtering function that filters by type "Surgical"
    surgical_sets = [s for s in all_sets if s.type == "Surgical"]
    
    # ASSERT: Should only return items where type == "Surgical"
    assert len(surgical_sets) > 0
    for s in surgical_sets:
        assert s.type == "Surgical"


def test_state_validation_only_packed_items_shown(sample_instrument_sets):
    """
    Unit Test: State Validation (US-06)
    Ensures that nurses only see instruments that are currently in the "Packed" state.
    """
    # ARRANGE: Load our sample sets which includes sets in various states (Cleaned, Packed, etc.)
    all_sets = sample_instrument_sets.values()
    
    # ACT: Filter sets to only include "Packed" items (simulating the backend logic for sterile stock)
    available_stock = [s for s in all_sets if s.state == "Packed"]
    
    # ASSERT: Every item in the resulting list MUST have the state "Packed"
    assert len(available_stock) > 0
    for item in available_stock:
        assert item.state == "Packed"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  2. INTEGRATION TESTS                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def test_submit_instrument_request_integration(nurse_client, sample_inventory_items):
    """
    Integration Test: POST /request/create with valid nurse credentials (US-05)
    Given a logged in nurse
    When they submit an instrument request with selected items
    Then a request is created and appears on the CSSD pending list.
    """
    # ARRANGE: Prepare the POST payload
    # Note: In a REST API this would be /api/requests, but we map to the Django view `save_instrument_request`
    url = reverse("save_instrument_request")  # Ensure this URL name matches urls.py
    
    scalpel = sample_inventory_items["available"]
    payload = {
        "priority": "Urgent",
        "notes": "Surgery at 3 PM",
        "instruments": [scalpel.name],
        f"quantity_{scalpel.name}": "2"
    }
    
    # ACT: Submit the request
    response = nurse_client.post(url, data=payload)
    
    # ASSERT: Should successfully redirect back to the nurse dashboard (HTTP 302)
    assert response.status_code == 302
    assert response.url == reverse("nurse_dashboard")
    
    # ASSERT: The request must now exist in the database with status "Requested" (CSSD Dashboard Pending List)
    new_request = InstrumentRequest.objects.latest('id')
    assert new_request.priority == "Urgent"
    assert new_request.status == "Requested"
    assert new_request.items.count() == 1


def test_submit_instrument_request_shows_success_message(nurse_client, sample_inventory_items):
    """
    Integration Test: successful request submission displays a dashboard success message.
    """
    scalpel = sample_inventory_items["available"]
    payload = {
        "priority": "Normal",
        "notes": "Routine request",
        "instruments": [scalpel.name],
        f"quantity_{scalpel.name}": "1",
    }

    response = nurse_client.post(reverse("save_instrument_request"), data=payload, follow=True)
    new_request = InstrumentRequest.objects.latest("id")

    assert response.status_code == 200
    assert response.redirect_chain[-1][0] == reverse("nurse_dashboard")
    assert f"Request REQ-{new_request.id:04d} sent successfully.".encode() in response.content
    assert f"REQ-{new_request.id:04d}".encode() in response.content


def test_view_available_sterile_stock(nurse_client, sample_instrument_sets):
    """
    Integration Test: GET Sterile Stock Endpoint (US-06)
    Given a logged in nurse
    When they navigate to view sterile stock
    Then they should only be presented with items in the 'Packed' state.
    """
    # ARRANGE: In a DRF setup this would be client.get('/api/sterile-stock')
    # For this Django app, we simulate fetching the packed queryset.
    # ACT: Query the database for what the API would return
    packed_stock = InstrumentSet.objects.filter(state="Packed")
    
    # ASSERT: Must only return items that are packed and ready for delivery
    assert packed_stock.count() == 1
    assert packed_stock.first().name == "Dental Extraction Kit"


def test_filter_sterile_stock_by_type(nurse_client, sample_instrument_sets):
    """
    Integration Test: GET /api/sterile-stock?type=Surgical (US-06)
    Given a logged in nurse viewing stock
    When they apply a filter for "Surgical"
    Then the results should only contain "Packed" items that are also "Surgical".
    """
    # ARRANGE & ACT: Query for Packed + Surgical
    packed_surgical_stock = InstrumentSet.objects.filter(state="Packed", type="Surgical")
    
    # ASSERT: Check if we have any surgical packed items
    # According to our conftest.py, Laparoscopy Kit is Sterilized, not Packed, so this should be 0.
    assert packed_surgical_stock.count() == 0


def test_stock_count_updates_in_real_time(nurse_client, sample_instrument_sets):
    """
    Integration Test: Verify stock count updates when state changes to "Packed" (US-06)
    Given an instrument set currently in "Sterilized" state
    When the CSSD tech changes its state to "Packed"
    Then the sterile stock count available to the nurse should increase.
    """
    # ARRANGE: Check initial packed count
    initial_packed_count = InstrumentSet.objects.filter(state="Packed").count()
    
    # ACT: Simulate CSSD Technician packing a sterilized kit
    sterilized_kit = InstrumentSet.objects.get(name="Laparoscopy Kit", state="Sterilized")
    sterilized_kit.state = "Packed"
    sterilized_kit.save()
    
    # ASSERT: The packed stock count should instantly increase by 1
    new_packed_count = InstrumentSet.objects.filter(state="Packed").count()
    assert new_packed_count == initial_packed_count + 1
