"""
test_dashboards.py — Unit + Integration tests for PROJ-8 Dashboards.

Covers:
  • Unit tests   — model helpers, ETA calculation, inventory status property,
                   role routing logic, request filtering.
  • Integration  — full HTTP request/response cycle for CSSD and Nurse
                   dashboards with seeded users, inventory, and requests.

Test flow mirrors the SRS acceptance criteria:
  1. Seed users (CSSD tech, nurse) + inventory items
  2. Nurse submits 2–3 requests (Normal + Urgent)
  3. CSSD staff logs in → sees /dashboard/ (cssd-dashboard template)
  4. Nurse logs in → sees /dashboard/ (nurse-dashboard template)
"""

import pytest
from django.test import Client
from django.urls import reverse

from CSSD_Management_System.models import (
    CustomUser,
    InventoryItem,
    InstrumentRequest,
    RequestItem,
    InstrumentSet,
    SterilizationBatch,
    Notification,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
TEST_PASSWORD = "TestPass123!"


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestInventoryItemStatus:
    """Unit tests for the InventoryItem.status computed property."""

    @pytest.mark.django_db
    def test_status_available_when_stock_above_threshold(self):
        item = InventoryItem.objects.create(
            name="Scalpel", category="Cutting",
            current_stock=50, min_threshold=10,
        )
        assert item.status == "Available"

    @pytest.mark.django_db
    def test_status_limited_when_stock_at_threshold(self):
        item = InventoryItem.objects.create(
            name="Forceps", category="Grasping",
            current_stock=10, min_threshold=10,
        )
        assert item.status == "Limited"

    @pytest.mark.django_db
    def test_status_limited_when_stock_below_threshold(self):
        item = InventoryItem.objects.create(
            name="Retractor", category="Retraction",
            current_stock=3, min_threshold=10,
        )
        assert item.status == "Limited"

    @pytest.mark.django_db
    def test_status_out_of_stock_when_zero(self):
        item = InventoryItem.objects.create(
            name="Needle", category="Suturing",
            current_stock=0, min_threshold=10,
        )
        assert item.status == "Out of Stock"


class TestInventoryItemPercentage:
    """Unit tests for the InventoryItem.percentage computed property."""

    @pytest.mark.django_db
    def test_percentage_capped_at_100(self):
        item = InventoryItem.objects.create(
            name="Scalpel", category="Cutting",
            current_stock=100, min_threshold=10,
        )
        assert item.percentage == 100

    @pytest.mark.django_db
    def test_percentage_half(self):
        item = InventoryItem.objects.create(
            name="Forceps", category="Grasping",
            current_stock=5, min_threshold=10,
        )
        assert item.percentage == 50.0

    @pytest.mark.django_db
    def test_percentage_zero_stock(self):
        item = InventoryItem.objects.create(
            name="Needle", category="Suturing",
            current_stock=0, min_threshold=10,
        )
        assert item.percentage == 0.0

    @pytest.mark.django_db
    def test_percentage_zero_threshold_returns_100(self):
        item = InventoryItem.objects.create(
            name="Clamp", category="Clamping",
            current_stock=5, min_threshold=0,
        )
        assert item.percentage == 100


class TestInstrumentRequestETA:
    """Unit tests for InstrumentRequest.get_eta() method."""

    @pytest.mark.django_db
    def test_eta_delivered_returns_ready(self):
        user = CustomUser.objects.create_user(
            email="eta_nurse@test.com", password=TEST_PASSWORD,
            role="Department Nurse", department="ER",
        )
        req = InstrumentRequest.objects.create(
            requester=user, priority="Normal", status="Delivered",
            department="ER",
        )
        assert req.get_eta() == "Ready"

    @pytest.mark.django_db
    def test_eta_requested_returns_ready_by(self):
        user = CustomUser.objects.create_user(
            email="eta_nurse2@test.com", password=TEST_PASSWORD,
            role="Department Nurse", department="ER",
        )
        req = InstrumentRequest.objects.create(
            requester=user, priority="Normal", status="Requested",
            department="ER",
        )
        eta = req.get_eta()
        assert "Ready by ~" in eta

    @pytest.mark.django_db
    def test_eta_packed_returns_ready_by(self):
        user = CustomUser.objects.create_user(
            email="eta_nurse3@test.com", password=TEST_PASSWORD,
            role="Department Nurse", department="ER",
        )
        req = InstrumentRequest.objects.create(
            requester=user, priority="Normal", status="Packed",
            department="ER",
        )
        eta = req.get_eta()
        assert "Ready by ~" in eta


class TestInstrumentRequestStr:
    """Unit tests for InstrumentRequest.__str__() method."""

    @pytest.mark.django_db
    def test_str_format(self):
        user = CustomUser.objects.create_user(
            email="str_nurse@test.com", password=TEST_PASSWORD,
            role="Department Nurse", department="ER",
        )
        req = InstrumentRequest.objects.create(
            requester=user, priority="Normal", status="Requested",
            department="ER",
        )
        expected = f"REQ-{req.id:04d} - Requested"
        assert str(req) == expected


class TestRequestItemStr:
    """Unit tests for RequestItem.__str__() method."""

    @pytest.mark.django_db
    def test_str_format(self):
        user = CustomUser.objects.create_user(
            email="ri_nurse@test.com", password=TEST_PASSWORD,
            role="Department Nurse", department="ER",
        )
        item = InventoryItem.objects.create(
            name="Scalpel", category="Cutting",
            current_stock=50, min_threshold=10,
        )
        req = InstrumentRequest.objects.create(
            requester=user, department="ER",
        )
        ri = RequestItem.objects.create(request=req, inventory_item=item, quantity=3)
        assert str(ri) == "3x Scalpel"


class TestRoleBasedRouting:
    """
    Unit-level tests for the dashboard_router view logic.
    Verifies that each role sees the correct template.
    """

    @pytest.mark.django_db
    def test_cssd_technician_sees_cssd_dashboard(self):
        user = CustomUser.objects.create_user(
            email="cssd@test.com", password=TEST_PASSWORD,
            role="CSSD Technician", department="CSSD",
        )
        client = Client()
        client.login(email="cssd@test.com", password=TEST_PASSWORD)
        resp = client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        assert "cssd-dashboard.html" in [t.name for t in resp.templates]

    @pytest.mark.django_db
    def test_admin_sees_cssd_dashboard(self):
        user = CustomUser.objects.create_user(
            email="admin@test.com", password=TEST_PASSWORD,
            role="System Administrator", department="IT", is_staff=True,
        )
        client = Client()
        client.login(email="admin@test.com", password=TEST_PASSWORD)
        resp = client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        assert "cssd-dashboard.html" in [t.name for t in resp.templates]

    @pytest.mark.django_db
    def test_nurse_sees_nurse_dashboard(self):
        user = CustomUser.objects.create_user(
            email="nurse@test.com", password=TEST_PASSWORD,
            role="Department Nurse", department="ER",
        )
        client = Client()
        client.login(email="nurse@test.com", password=TEST_PASSWORD)
        resp = client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        assert "nurse-dashboard.html" in [t.name for t in resp.templates]

    @pytest.mark.django_db
    def test_hospital_admin_sees_cssd_dashboard(self):
        user = CustomUser.objects.create_user(
            email="hadmin@test.com", password=TEST_PASSWORD,
            role="Hospital Administrator", department="Admin",
        )
        client = Client()
        client.login(email="hadmin@test.com", password=TEST_PASSWORD)
        resp = client.get(reverse("dashboard_router"))
        assert resp.status_code == 302
        assert "/dashboard/hospital/" in resp.url

    @pytest.mark.django_db
    def test_unauthenticated_user_redirected_to_login(self):
        client = Client()
        resp = client.get(reverse("dashboard_router"))
        assert resp.status_code == 302
        assert "/login/" in resp.url


# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDashboardIntegration:
    """
    Full integration test suite for the dashboard feature.

    Test flow:
      1. Seed a CSSD tech user, a nurse user, and inventory items
      2. Nurse submits 3 instrument requests (2 Normal, 1 Urgent)
      3. Verify CSSD staff login → /dashboard/ renders cssd-dashboard
      4. Verify Nurse login → /dashboard/ renders nurse-dashboard
      5. Verify nurse dashboard context contains the submitted requests
    """

    @pytest.fixture(autouse=True)
    def setup_users_and_inventory(self, db):
        """Seed users + inventory items for every test in this class."""
        # ── Users ──
        self.cssd_user = CustomUser.objects.create_user(
            email="cssd@test.com",
            password=TEST_PASSWORD,
            role="CSSD Technician",
            department="CSSD",
        )
        self.nurse_user = CustomUser.objects.create_user(
            email="nurse@test.com",
            password=TEST_PASSWORD,
            role="Department Nurse",
            department="Emergency",
        )

        # ── Inventory ──
        self.scalpel = InventoryItem.objects.create(
            name="Surgical Scalpel", category="Cutting",
            current_stock=50, min_threshold=10,
        )
        self.forceps = InventoryItem.objects.create(
            name="Forceps", category="Grasping",
            current_stock=30, min_threshold=10,
        )
        self.retractor = InventoryItem.objects.create(
            name="Retractor", category="Retraction",
            current_stock=20, min_threshold=5,
        )

        # ── Clients ──
        self.cssd_client = Client()
        self.cssd_client.login(email="cssd@test.com", password=TEST_PASSWORD)

        self.nurse_client = Client()
        self.nurse_client.login(email="nurse@test.com", password=TEST_PASSWORD)

    def _submit_request(self, priority, instruments_with_qty):
        """
        Helper: submits an instrument request as the nurse via POST.
        instruments_with_qty: list of (name, quantity) tuples.
        """
        post_data = {
            "priority": priority,
            "notes": f"Test request - {priority}",
            "instruments": [name for name, _ in instruments_with_qty],
        }
        for name, qty in instruments_with_qty:
            post_data[f"quantity_{name}"] = str(qty)

        return self.nurse_client.post(
            reverse("save_instrument_request"),
            data=post_data,
        )

    # ── Step 2: Nurse submits requests ──────────────────────────────────────

    def test_nurse_can_submit_normal_request(self):
        """Nurse submits a Normal priority request → redirect + DB record."""
        resp = self._submit_request("Normal", [("Surgical Scalpel", 2)])
        assert resp.status_code == 302  # redirect after POST
        assert InstrumentRequest.objects.filter(
            requester=self.nurse_user, priority="Normal"
        ).exists()

    def test_nurse_can_submit_urgent_request(self):
        """Nurse submits an Urgent priority request → redirect + DB record."""
        resp = self._submit_request("Urgent", [("Forceps", 1)])
        assert resp.status_code == 302
        assert InstrumentRequest.objects.filter(
            requester=self.nurse_user, priority="Urgent"
        ).exists()

    def test_nurse_submits_multiple_requests(self):
        """Nurse submits 3 requests (2 Normal + 1 Urgent) → all created."""
        self._submit_request("Normal", [("Surgical Scalpel", 2)])
        self._submit_request("Normal", [("Retractor", 1)])
        self._submit_request("Urgent", [("Forceps", 3)])

        all_requests = InstrumentRequest.objects.filter(requester=self.nurse_user)
        assert all_requests.count() == 3
        assert all_requests.filter(priority="Normal").count() == 2
        assert all_requests.filter(priority="Urgent").count() == 1

    def test_inventory_decremented_after_request(self):
        """After submitting a request, inventory stock is reduced."""
        self._submit_request("Normal", [("Surgical Scalpel", 5)])
        self.scalpel.refresh_from_db()
        assert self.scalpel.current_stock == 45  # 50 - 5

    def test_request_items_created_correctly(self):
        """RequestItem line items are linked to the correct request."""
        self._submit_request("Normal", [
            ("Surgical Scalpel", 2),
            ("Forceps", 3),
        ])
        req = InstrumentRequest.objects.filter(requester=self.nurse_user).first()
        items = RequestItem.objects.filter(request=req)
        assert items.count() == 2
        names = [ri.inventory_item.name for ri in items]
        assert "Surgical Scalpel" in names
        assert "Forceps" in names

    # ── Step 3: CSSD staff login → /dashboard/ ─────────────────────────────

    def test_cssd_staff_sees_cssd_dashboard(self):
        """CSSD tech logs in → /dashboard/ renders cssd-dashboard.html."""
        resp = self.cssd_client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        template_names = [t.name for t in resp.templates]
        assert "cssd-dashboard.html" in template_names

    def test_cssd_dashboard_accessible_after_requests_submitted(self):
        """
        After nurse submits requests, CSSD dashboard still loads correctly.
        The requests exist in the database for the CSSD dashboard to display.
        """
        self._submit_request("Normal", [("Surgical Scalpel", 2)])
        self._submit_request("Urgent", [("Forceps", 1)])

        resp = self.cssd_client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        assert InstrumentRequest.objects.count() == 2

    def test_cssd_dashboard_shows_shortage_alerts_with_set_name_and_count(self):
        """
        CSSD Tech sees dashboard alerts when available stock drops below 3 units.
        """
        InventoryItem.objects.create(
            name="Biopsy Tray",
            category="Surgical",
            current_stock=2,
            min_threshold=3,
        )
        InventoryItem.objects.create(
            name="Suture Tray",
            category="Surgical",
            current_stock=3,
            min_threshold=3,
        )

        resp = self.cssd_client.get(reverse("dashboard_router"))
        content = resp.content.decode()

        assert resp.status_code == 200
        assert "Instrument set shortage alerts" in content
        assert "Biopsy Tray" in content
        assert "Current count: 2" in content
        assert "Dismiss Biopsy Tray shortage alert" in content
        assert "Suture Tray" not in content

    def test_dismissed_dashboard_shortage_alert_reappears_on_reload_if_stock_still_low(self):
        """
        Dismissal is intentionally temporary: the server renders the alert again
        while stock remains below 3 units.
        """
        InventoryItem.objects.create(
            name="Trauma Tray",
            category="Emergency",
            current_stock=1,
            min_threshold=3,
        )

        first_resp = self.cssd_client.get(reverse("dashboard_router"))
        second_resp = self.cssd_client.get(reverse("dashboard_router"))

        assert "Trauma Tray" in first_resp.content.decode()
        assert "Trauma Tray" in second_resp.content.decode()

    def test_direct_cssd_dashboard_shows_shortage_alerts_after_login_redirect(self):
        InventoryItem.objects.create(
            name="Ortho Mini Set",
            category="Orthopedic",
            current_stock=0,
            min_threshold=3,
        )

        resp = self.cssd_client.get(reverse("cssd_dashboard"))
        content = resp.content.decode()

        assert resp.status_code == 200
        assert "Ortho Mini Set" in content
        assert "Current count: 0" in content

    # ── Step 4: Nurse login → /dashboard/ ──────────────────────────────────

    def test_nurse_sees_nurse_dashboard(self):
        """Nurse logs in → /dashboard/ renders nurse-dashboard.html."""
        resp = self.nurse_client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        template_names = [t.name for t in resp.templates]
        assert "nurse-dashboard.html" in template_names

    def test_nurse_dashboard_shows_own_requests(self):
        """
        After nurse submits requests and visits /nurse_dashboard/,
        context should contain the requests.
        """
        self._submit_request("Normal", [("Surgical Scalpel", 2)])
        self._submit_request("Urgent", [("Forceps", 1)])
        self._submit_request("Normal", [("Retractor", 1)])

        resp = self.nurse_client.get(reverse("nurse_dashboard"))
        assert resp.status_code == 200
        # Verify context has request data
        assert "requests" in resp.context
        assert resp.context["total"] == 3
        assert resp.context["urgent"] == 1

    def test_nurse_dashboard_shows_correct_counts(self):
        """Verify the nurse dashboard stats match the actual data."""
        self._submit_request("Normal", [("Surgical Scalpel", 2)])
        self._submit_request("Urgent", [("Forceps", 1)])

        resp = self.nurse_client.get(reverse("nurse_dashboard"))
        assert resp.context["total"] == 2
        assert resp.context["urgent"] == 1
        assert resp.context["in_progress"] == 0  # all are in 'Requested' state
        assert resp.context["delivered"] == 0

    # ── Access control ─────────────────────────────────────────────────────

    def test_unauthenticated_cannot_access_dashboard(self):
        """Anonymous user → redirect to login."""
        anon_client = Client()
        resp = anon_client.get(reverse("dashboard_router"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_unauthenticated_cannot_access_nurse_dashboard(self):
        """Anonymous user → redirect to login for nurse dashboard."""
        anon_client = Client()
        resp = anon_client.get(reverse("nurse_dashboard"))
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_nurse_create_request_page_loads(self):
        """Nurse can access the create-request page."""
        resp = self.nurse_client.get(reverse("nurse_create_request"))
        assert resp.status_code == 200
        assert "instruments" in resp.context

    def test_nurse_create_request_lists_inventory(self):
        """Create-request page context includes all inventory items."""
        resp = self.nurse_client.get(reverse("nurse_create_request"))
        instrument_names = [i["name"] for i in resp.context["instruments"]]
        assert "Surgical Scalpel" in instrument_names
        assert "Forceps" in instrument_names
        assert "Retractor" in instrument_names

    def test_request_rejected_when_stock_insufficient(self):
        """Submitting a quantity > stock renders a warning instead of redirect."""
        resp = self._submit_request("Normal", [("Surgical Scalpel", 999)])
        # Should redirect back to create request with a django message warning
        assert resp.status_code == 302
        assert reverse("nurse_create_request") in resp.url
