import pytest
from CSSD_Management_System.models import (
    InventoryItem, InstrumentRequest, InstrumentSet, 
    SterilizationBatch, CustomUser, Notification, RequestItem
)
from django.utils import timezone

@pytest.mark.django_db
def test_inventory_item_properties():
    # Out of stock
    item1 = InventoryItem.objects.create(name="Item 1", category="Cat", current_stock=0, min_threshold=10)
    assert item1.status == "Out of Stock"
    assert item1.percentage == 0.0

    # Limited
    item2 = InventoryItem.objects.create(name="Item 2", category="Cat", current_stock=5, min_threshold=10)
    assert item2.status == "Limited"
    assert item2.percentage == 50.0

    # Available
    item3 = InventoryItem.objects.create(name="Item 3", category="Cat", current_stock=20, min_threshold=10)
    assert item3.status == "Available"
    assert item3.percentage == 100.0
    
    # Zero threshold edge case
    item4 = InventoryItem.objects.create(name="Item 4", category="Cat", current_stock=5, min_threshold=0)
    assert item4.percentage == 100

    # __str__ method
    assert str(item1) == "Item 1"

@pytest.mark.django_db
def test_instrument_request_eta(nurse_user):
    req = InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Requested",
        department="ER"
    )
    
    # Requested ETA (120 mins)
    eta_str = req.get_eta()
    assert "Ready by ~" in eta_str
    
    # Delivered ETA
    req.status = "Delivered"
    req.save()
    assert req.get_eta() == "Ready"
    
    # __str__ method
    assert str(req) == f"REQ-{req.id:04d} - Delivered"

@pytest.mark.django_db
def test_other_models_str_methods(admin_user):
    # InstrumentSet
    iset = InstrumentSet.objects.create(name="Set A", type="Surgical", quantity=5, state="Packed")
    assert str(iset) == "Set A (Packed)"
    
    # SterilizationBatch
    batch = SterilizationBatch.objects.create(operator=admin_user, temperature=134.0, cycle_duration=45.0, status="In Progress")
    assert f"Batch {batch.id}" in str(batch)
    assert "In Progress" in str(batch)
    
    # Notification
    req = InstrumentRequest.objects.create(requester=admin_user)
    notif = Notification.objects.create(recipient=admin_user, request=req, message="Hello")
    assert "Hello" in str(notif)
    
    # RequestItem
    item = InventoryItem.objects.create(name="Test Item")
    req_item = RequestItem.objects.create(request=req, inventory_item=item, quantity=3)
    assert str(req_item) == "3x Test Item"
