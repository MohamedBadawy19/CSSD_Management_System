import pytest
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import RequestItem, SterilizationBatch


@pytest.mark.django_db
def test_daily_report_shows_nurse_submitted_requests(hospital_admin_client, sample_request):
    report_date = timezone.localdate()

    response = hospital_admin_client.get(
        f"{reverse('hospital_report')}?date={report_date.isoformat()}"
    )

    assert response.status_code == 200
    assert b"Nurse Requests Submitted" in response.content
    assert f"REQ-{sample_request.id:04d}".encode() in response.content
    assert sample_request.requester.email.encode() in response.content
    assert sample_request.department.encode() in response.content


@pytest.mark.django_db
def test_daily_report_shows_technician_work(
    hospital_admin_client,
    sample_request,
    cssd_technician_user,
):
    now = timezone.now()
    batch = SterilizationBatch.objects.create(
        operator=cssd_technician_user,
        temperature=134,
        cycle_duration=45,
        status="Completed",
    )
    sample_request.status = "Sterilized"
    sample_request.batch = batch
    sample_request.last_operator = cssd_technician_user
    sample_request.collected_at = now
    sample_request.cleaned_at = now
    sample_request.sterilized_at = now
    sample_request.save()

    response = hospital_admin_client.get(
        f"{reverse('hospital_report')}?date={timezone.localdate().isoformat()}"
    )

    assert response.status_code == 200
    assert b"Technician Work" in response.content
    assert b"Collected" in response.content
    assert b"Cleaned" in response.content
    assert b"Sterilized" in response.content
    assert cssd_technician_user.email.encode() in response.content


@pytest.mark.django_db
def test_daily_report_item_total_still_counts_sterilized_quantities(
    hospital_admin_client,
    sample_request,
    cssd_technician_user,
):
    sample_request.status = "Sterilized"
    sample_request.last_operator = cssd_technician_user
    sample_request.sterilized_at = timezone.now()
    sample_request.save()
    expected_quantity = sum(
        RequestItem.objects.filter(request=sample_request).values_list("quantity", flat=True)
    )

    response = hospital_admin_client.get(
        f"{reverse('hospital_report')}?date={timezone.localdate().isoformat()}"
    )

    assert response.status_code == 200
    assert response.context["total_sterilized"] == expected_quantity
