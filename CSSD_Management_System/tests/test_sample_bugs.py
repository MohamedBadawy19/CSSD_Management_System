import pytest
from django.urls import reverse

from CSSD_Management_System.models import CustomUser, InstrumentRequest, RequestItem


pytestmark = pytest.mark.django_db


def test_nurse_cannot_use_legacy_cssd_transition_views(nurse_client, sample_request):
    endpoints = [
        ("mark_collected", "Requested"),
        ("mark_cleaned", "Collected"),
        ("mark_sterilized", "Cleaned"),
        ("mark_packed", "Sterilized"),
    ]

    for name, status in endpoints:
        sample_request.status = status
        sample_request.save()
        response = nurse_client.post(reverse(name, args=[sample_request.pk]))

        assert response.status_code == 403


def test_nurse_cannot_view_legacy_cssd_request_details(nurse_client, sample_request):
    response = nurse_client.get(reverse("cssd_request_details", args=[sample_request.pk]))

    assert response.status_code == 403


def test_non_nurse_cannot_confirm_delivery(client, sample_request):
    technician = CustomUser.objects.create_user(
        email="delivery-tech@test.com",
        password="TestPass123!",
        role="CSSD Technician",
        department=sample_request.department,
    )
    sample_request.status = "Packed"
    sample_request.save()
    client.login(email=technician.email, password="TestPass123!")

    response = client.post(reverse("mark_delivered", args=[sample_request.pk]))

    assert response.status_code == 403
    sample_request.refresh_from_db()
    assert sample_request.status == "Packed"


def test_negative_request_quantity_is_rejected(nurse_client, sample_inventory_items):
    instrument = sample_inventory_items["available"]
    starting_stock = instrument.current_stock

    response = nurse_client.post(
        reverse("save_instrument_request"),
        data={
            "priority": "Normal",
            "notes": "Bad quantity",
            "instruments": [instrument.name],
            f"quantity_{instrument.name}": "-3",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("nurse_create_request")
    assert not RequestItem.objects.filter(inventory_item=instrument, quantity__lt=1).exists()
    instrument.refresh_from_db()
    assert instrument.current_stock == starting_stock


def test_staff_portal_rejects_nurse_credentials(client, nurse_user):
    response = client.post(
        reverse("login") + "?role=staff",
        data={"username": nurse_user.email, "password": "TestPass123!"},
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_nurse_portal_rejects_staff_credentials(client, cssd_technician_user):
    response = client.post(
        reverse("login") + "?role=nurse",
        data={"username": cssd_technician_user.email, "password": "TestPass123!"},
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
