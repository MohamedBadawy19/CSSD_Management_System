import pytest
from django.urls import reverse
from CSSD_Management_System.models import CustomUser, SterilizationBatch


# =========================================================
# Fixtures
# =========================================================

@pytest.fixture
def client():
    from django.test import Client
    return Client()


@pytest.fixture
def cssd_user(db):
    return CustomUser.objects.create_user(
        email="cssd@test.com",
        password="Test1234!",
        role="CSSD Technician",
        department="CSSD",
        first_name="Ali"
    )


@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email="nurse@test.com",
        password="Test1234!",
        role="Department Nurse",
        department="ICU",
        first_name="Sara"
    )


# =========================================================
# 1. Batch Creation
# =========================================================

@pytest.mark.django_db
def test_valid_batch_creation(client, cssd_user):
    client.login(username="cssd@test.com", password="Test1234!")

    response = client.post(reverse("cssd_batch_create"), {
        "temperature": 134,
        "cycle_duration": 30
    })

    assert response.status_code == 302
    assert SterilizationBatch.objects.count() == 1


@pytest.mark.django_db
def test_operator_auto_assigned(client, cssd_user):
    client.login(username="cssd@test.com", password="Test1234!")

    client.post(reverse("cssd_batch_create"), {
        "temperature": 134,
        "cycle_duration": 30
    })

    batch = SterilizationBatch.objects.first()
    assert batch.operator == cssd_user


@pytest.mark.django_db
def test_invalid_temperature_rejected(client, cssd_user):
    client.login(username="cssd@test.com", password="Test1234!")

    client.post(reverse("cssd_batch_create"), {
        "temperature": 100,
        "cycle_duration": 30
    })

    assert SterilizationBatch.objects.count() == 0


@pytest.mark.django_db
def test_invalid_duration_rejected(client, cssd_user):
    client.login(username="cssd@test.com", password="Test1234!")

    client.post(reverse("cssd_batch_create"), {
        "temperature": 134,
        "cycle_duration": 0
    })

    assert SterilizationBatch.objects.count() == 0


@pytest.mark.django_db
def test_nurse_cannot_create_batch(client, nurse_user):
    client.login(username="nurse@test.com", password="Test1234!")

    response = client.get(reverse("cssd_batch_create"))

    assert response.status_code == 403


# =========================================================
# 2. Batch List
# =========================================================

@pytest.mark.django_db
def test_cssd_can_view_batch_list(client, cssd_user):
    client.login(username="cssd@test.com", password="Test1234!")

    response = client.get(reverse("cssd_batch_list"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_nurse_cannot_view_batch_list(client, nurse_user):
    client.login(username="nurse@test.com", password="Test1234!")

    response = client.get(reverse("cssd_batch_list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_batch_appears_in_list(client, cssd_user):
    client.login(username="cssd@test.com", password="Test1234!")

    SterilizationBatch.objects.create(
        operator=cssd_user,
        temperature=134,
        cycle_duration=30
    )

    response = client.get(reverse("cssd_batch_list"))

    assert response.status_code == 200
    assert SterilizationBatch.objects.count() == 1


# =========================================================
# 3. Batch Detail
# =========================================================

@pytest.mark.django_db
def test_cssd_can_view_batch_detail(client, cssd_user):
    batch = SterilizationBatch.objects.create(
        operator=cssd_user,
        temperature=134,
        cycle_duration=30
    )

    client.login(username="cssd@test.com", password="Test1234!")

    response = client.get(reverse("cssd_batch_detail", args=[batch.pk]))

    assert response.status_code == 200


@pytest.mark.django_db
def test_nurse_forbidden_from_detail(client, nurse_user, cssd_user):
    batch = SterilizationBatch.objects.create(
        operator=cssd_user,
        temperature=134,
        cycle_duration=30
    )

    client.login(username="nurse@test.com", password="Test1234!")

    response = client.get(reverse("cssd_batch_detail", args=[batch.pk]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_nonexistent_batch_returns_404(client, cssd_user):
    client.login(username="cssd@test.com", password="Test1234!")

    response = client.get(reverse("cssd_batch_detail", args=[999]))

    assert response.status_code == 404