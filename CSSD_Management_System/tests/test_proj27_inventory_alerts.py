import pytest
from django.urls import reverse
from CSSD_Management_System.models import CustomUser, InventoryItem


@pytest.fixture
def cssd_user(db):
    return CustomUser.objects.create_user(
        email="cssd@test.com",
        password="Test1234!",
        role="CSSD Technician",
        department="CSSD",
    )


@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email="nurse@test.com",
        password="Test1234!",
        role="Department Nurse",
        department="ICU",
    )


@pytest.fixture
def inventory_items(db):
    """
    Creates:
    - Clamp Set → stock=0 → Out of Stock
    - Forceps → stock=2 < threshold=5 → Critical
    - Scalpel Set → stock=20 > threshold → should NOT appear
    """
    clamp = InventoryItem.objects.create(
        name="Clamp Set",
        category="Clamps",
        current_stock=0,
        min_threshold=3,
    )
    forceps = InventoryItem.objects.create(
        name="Forceps",
        category="Surgical",
        current_stock=2,
        min_threshold=5,
    )
    scalpel = InventoryItem.objects.create(
        name="Scalpel Set",
        category="Surgical",
        current_stock=20,
        min_threshold=5,
    )
    return clamp, forceps, scalpel


@pytest.mark.django_db
class TestInventoryAlerts:

    def test_cssd_can_view_alerts(self, client, cssd_user, inventory_items):
        client.login(email="cssd@test.com", password="Test1234!")

        response = client.get("/dashboard/cssd/alerts/")

        assert response.status_code == 200


    def test_only_low_stock_items_are_shown(self, client, cssd_user, inventory_items):
        client.login(email="cssd@test.com", password="Test1234!")

        response = client.get("/dashboard/cssd/alerts/")

        content = response.content.decode()

        # Should appear
        assert "Clamp Set" in content
        assert "Forceps" in content

        # Should NOT appear
        assert "Scalpel Set" not in content


    def test_out_of_stock_label(self, client, cssd_user, inventory_items):
        client.login(email="cssd@test.com", password="Test1234!")

        response = client.get("/dashboard/cssd/alerts/")
        content = response.content.decode()

        assert "Clamp Set" in content
        assert "Out of Stock" in content


    def test_critical_label(self, client, cssd_user, inventory_items):
        client.login(email="cssd@test.com", password="Test1234!")

        response = client.get("/dashboard/cssd/alerts/")
        content = response.content.decode()

        assert "Forceps" in content
        assert "Critical" in content


    def test_category_filter(self, client, cssd_user, inventory_items):
        client.login(email="cssd@test.com", password="Test1234!")

        # Filter by "Clamps"
        response = client.get("/dashboard/cssd/alerts/?category=Clamps")
        content = response.content.decode()

        assert "Clamp Set" in content
        assert "Forceps" not in content


    def test_nurse_forbidden(self, client, nurse_user, inventory_items):
        client.login(email="nurse@test.com", password="Test1234!")

        response = client.get("/dashboard/cssd/alerts/")

        assert response.status_code == 403


    def test_unauthenticated_redirect(self, client, inventory_items):
        response = client.get("/dashboard/cssd/alerts/")

        assert response.status_code in (302, 301)
        assert "/login" in response.url