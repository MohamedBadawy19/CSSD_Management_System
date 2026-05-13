"""
tests/test_proj31_integration.py
PROJ-31: Search Instrument Audit History — Integration Tests

End-to-end integration tests that verify the audit history feature works
correctly with the rest of the system (dev branch features).

Test scenarios:
  1. Full lifecycle flow: Nurse creates request → Tech processes through all
     stages (Collected → Cleaned → Sterilized → Packed → Delivered) →
     Hospital Admin searches audit and sees the complete timeline.
  2. Cross-role access: Verify each role sees only what they should.
  3. Dashboard routing integration: Hospital Admin is routed to report, not CSSD.
  4. Audit search works with requests created via the actual request-submission
     endpoint (not just ORM fixtures).
  5. Multiple requests and instruments: Audit search returns correct results
     when multiple requests exist.
  6. Interaction with batches: Sterilization batch operator info appears in audit.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser,
    InventoryItem,
    InstrumentRequest,
    RequestItem,
    SterilizationBatch,
    Notification,
)

# ── Shared password ──────────────────────────────────────────────────────────
PASSWORD = "TestPass123!"


# ══════════════════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def nurse(db):
    return CustomUser.objects.create_user(
        email="int_nurse@test.com", password=PASSWORD,
        first_name="Jane", last_name="Nurse",
        role="Department Nurse", department="Emergency",
    )


@pytest.fixture
def tech(db):
    return CustomUser.objects.create_user(
        email="int_tech@test.com", password=PASSWORD,
        first_name="John", last_name="Tech",
        role="CSSD Technician", department="CSSD",
    )


@pytest.fixture
def hospital_admin(db):
    return CustomUser.objects.create_user(
        email="int_hadmin@test.com", password=PASSWORD,
        first_name="Hospital", last_name="Admin",
        role="Hospital Administrator", department="Administration",
    )


@pytest.fixture
def sys_admin(db):
    return CustomUser.objects.create_user(
        email="int_sysadmin@test.com", password=PASSWORD,
        first_name="Sys", last_name="Admin",
        role="System Administrator", department="IT", is_staff=True,
    )


@pytest.fixture
def nurse_client(nurse):
    c = Client()
    c.login(email=nurse.email, password=PASSWORD)
    return c


@pytest.fixture
def tech_client(tech):
    c = Client()
    c.login(email=tech.email, password=PASSWORD)
    return c


@pytest.fixture
def hospital_client(hospital_admin):
    c = Client()
    c.login(email=hospital_admin.email, password=PASSWORD)
    return c


@pytest.fixture
def admin_client(sys_admin):
    c = Client()
    c.login(email=sys_admin.email, password=PASSWORD)
    return c


@pytest.fixture
def inventory(db):
    """Seed inventory items with sufficient stock for requests."""
    return {
        "scalpel": InventoryItem.objects.create(
            name="Surgical Scalpel", category="Cutting",
            current_stock=50, min_threshold=10,
        ),
        "forceps": InventoryItem.objects.create(
            name="Forceps", category="Grasping",
            current_stock=30, min_threshold=10,
        ),
        "retractor": InventoryItem.objects.create(
            name="Retractor", category="Retraction",
            current_stock=20, min_threshold=5,
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  1. FULL LIFECYCLE → AUDIT SEARCH (End-to-End)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestFullLifecycleAudit:
    """
    End-to-end: Nurse submits → Tech processes through all stages →
    Hospital Admin searches audit and sees the complete timeline.
    """

    def _submit_request(self, nurse_client, instruments_with_qty, priority="Normal"):
        """Helper: nurse submits an instrument request via POST."""
        post_data = {
            "priority": priority,
            "notes": f"Integration test - {priority}",
            "instruments": [name for name, _ in instruments_with_qty],
        }
        for name, qty in instruments_with_qty:
            post_data[f"quantity_{name}"] = str(qty)
        return nurse_client.post(reverse("save_instrument_request"), data=post_data)

    @pytest.mark.integration
    def test_nurse_submit_tech_process_admin_audit(
        self, nurse_client, tech_client, hospital_client, nurse, tech, inventory
    ):
        """
        Full flow:
        1. Nurse submits a request with instruments
        2. Tech marks as Collected → Cleaned → Sterilized → Packed
        3. Nurse marks as Delivered
        4. Hospital Admin searches audit by request ID and sees full timeline
        """
        # Step 1: Nurse submits request
        self._submit_request(nurse_client, [("Surgical Scalpel", 2)])
        req = InstrumentRequest.objects.filter(requester=nurse).first()
        assert req is not None
        assert req.status == "Requested"

        # Step 2: Tech processes through stages via the unified update endpoint
        # Mark as Collected
        url = reverse("cssd_update_request_status", kwargs={"pk": req.pk, "status": "Collected"})
        resp = tech_client.post(url)
        assert resp.status_code == 302
        req.refresh_from_db()
        assert req.status == "Collected"
        assert req.collected_at is not None

        # Mark as Cleaned
        url = reverse("cssd_update_request_status", kwargs={"pk": req.pk, "status": "Cleaned"})
        resp = tech_client.post(url)
        assert resp.status_code == 302
        req.refresh_from_db()
        assert req.status == "Cleaned"
        assert req.cleaned_at is not None

        # Create a batch for sterilization
        batch = SterilizationBatch.objects.create(
            operator=tech, temperature=134.0, cycle_duration=18.0, status="Completed",
        )

        # Mark as Sterilized (with batch)
        url = reverse("cssd_update_request_status", kwargs={"pk": req.pk, "status": "Sterilized"})
        resp = tech_client.post(url, {"batch_id": batch.pk})
        assert resp.status_code == 302
        req.refresh_from_db()
        assert req.status == "Sterilized"
        assert req.sterilized_at is not None
        assert req.batch == batch

        # Mark as Packed
        url = reverse("cssd_update_request_status", kwargs={"pk": req.pk, "status": "Packed"})
        resp = tech_client.post(url)
        assert resp.status_code == 302
        req.refresh_from_db()
        assert req.status == "Packed"
        assert req.packed_at is not None

        # Step 3: Nurse confirms delivery
        url = reverse("mark_delivered", kwargs={"request_id": req.pk})
        resp = nurse_client.post(url)
        assert resp.status_code == 302
        req.refresh_from_db()
        assert req.status == "Delivered"
        assert req.delivered_at is not None

        # Step 4: Hospital Admin searches audit by request ID
        audit_url = reverse("hospital_audit")
        resp = hospital_client.get(audit_url, {"q": str(req.pk)})
        assert resp.status_code == 200
        results = list(resp.context["results"])
        assert len(results) == 1

        result = results[0]
        assert result.pk == req.pk
        assert result.submitted_at is not None
        assert result.collected_at is not None
        assert result.cleaned_at is not None
        assert result.sterilized_at is not None
        assert result.packed_at is not None
        assert result.delivered_at is not None
        assert result.batch is not None
        assert result.batch.operator.email == tech.email

    @pytest.mark.integration
    def test_audit_search_by_instrument_name_after_workflow(
        self, nurse_client, hospital_client, nurse, inventory
    ):
        """
        Nurse submits request with 'Surgical Scalpel' →
        Hospital Admin searches by instrument name → finds it.
        """
        self._submit_request(nurse_client, [("Surgical Scalpel", 3)])
        req = InstrumentRequest.objects.filter(requester=nurse).first()

        audit_url = reverse("hospital_audit")
        resp = hospital_client.get(audit_url, {"q": "Scalpel"})
        assert resp.status_code == 200
        results = list(resp.context["results"])
        assert req in results

    @pytest.mark.integration
    def test_audit_shows_req_id_format_in_response(
        self, nurse_client, hospital_client, nurse, inventory
    ):
        """Audit page HTML contains the formatted request ID (REQ-XXXX)."""
        self._submit_request(nurse_client, [("Forceps", 1)])
        req = InstrumentRequest.objects.filter(requester=nurse).first()

        audit_url = reverse("hospital_audit")
        resp = hospital_client.get(audit_url, {"q": str(req.pk)})
        content = resp.content.decode()
        assert f"REQ-{req.pk:04d}" in content


# ══════════════════════════════════════════════════════════════════════════════
#  2. CROSS-ROLE ACCESS CONTROL INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCrossRoleAccess:
    """
    Verify that each role can only access its authorized endpoints.
    Tests the interaction between PROJ-31 and existing role restrictions.
    """

    @pytest.mark.integration
    def test_nurse_cannot_access_hospital_report(self, nurse_client):
        """Nurses cannot see the hospital report dashboard."""
        resp = nurse_client.get(reverse("hospital_report"))
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_nurse_cannot_access_hospital_audit(self, nurse_client):
        """Nurses cannot search the audit history."""
        resp = nurse_client.get(reverse("hospital_audit"))
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_tech_cannot_access_hospital_report(self, tech_client):
        """CSSD techs cannot see the hospital report dashboard."""
        resp = tech_client.get(reverse("hospital_report"))
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_tech_cannot_access_hospital_audit(self, tech_client):
        """CSSD techs cannot search the audit history."""
        resp = tech_client.get(reverse("hospital_audit"))
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_hospital_admin_can_view_cssd_batch_create(self, hospital_client):
        """Hospital admins pass cssd_staff_required (only nurses are blocked)."""
        resp = hospital_client.get(reverse("cssd_batch_create"))
        # cssd_staff_required only blocks Department Nurse role
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_hospital_admin_can_access_cssd_update(self, hospital_client, nurse):
        """Hospital admins pass cssd_staff_required for request updates."""
        req = InstrumentRequest.objects.create(
            requester=nurse, priority="Normal", status="Requested",
            department="Emergency",
        )
        url = reverse("cssd_update_request_status", kwargs={"pk": req.pk, "status": "Collected"})
        resp = hospital_client.post(url)
        # cssd_staff_required allows non-nurse roles; response is 302 redirect on success
        assert resp.status_code == 302


# ══════════════════════════════════════════════════════════════════════════════
#  3. DASHBOARD ROUTING INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDashboardRoutingIntegration:
    """
    Verify that the updated dashboard_router correctly routes
    all roles after the PROJ-31 changes.
    """

    @pytest.mark.integration
    def test_hospital_admin_routed_to_hospital_report(self, hospital_client):
        """Hospital Admin → redirected to /dashboard/hospital/."""
        resp = hospital_client.get(reverse("dashboard_router"))
        assert resp.status_code == 302
        assert "/dashboard/hospital/" in resp.url

    @pytest.mark.integration
    def test_cssd_tech_still_gets_cssd_dashboard(self, tech_client):
        """CSSD Tech → still renders cssd-dashboard.html (no regression)."""
        resp = tech_client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        template_names = [t.name for t in resp.templates]
        assert "cssd-dashboard.html" in template_names

    @pytest.mark.integration
    def test_nurse_still_redirected_to_nurse_dashboard(self, nurse_client):
        """Nurse → still renders nurse dashboard (no regression)."""
        resp = nurse_client.get(reverse("dashboard_router"))
        # Nurse gets the nurse dashboard directly rendered
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_sys_admin_still_gets_cssd_dashboard(self, admin_client):
        """System Admin → still renders cssd-dashboard.html (no regression)."""
        resp = admin_client.get(reverse("dashboard_router"))
        assert resp.status_code == 200
        template_names = [t.name for t in resp.templates]
        assert "cssd-dashboard.html" in template_names

    @pytest.mark.integration
    def test_hospital_report_links_to_audit(self, hospital_client):
        """Hospital report page contains a link to the audit page."""
        resp = hospital_client.get(reverse("hospital_report"))
        content = resp.content.decode()
        assert reverse("hospital_audit") in content


# ══════════════════════════════════════════════════════════════════════════════
#  4. MULTIPLE REQUESTS & INSTRUMENTS
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestMultipleRequestsAudit:
    """
    Integration tests for audit search behavior when multiple requests
    and instruments exist in the system.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self, db, nurse, tech, inventory):
        """Create multiple requests with different instruments and states."""
        self.req1 = InstrumentRequest.objects.create(
            requester=nurse, priority="Normal", status="Delivered",
            department="Emergency", notes="Morning surgery",
            submitted_at=timezone.now(), collected_at=timezone.now(),
            cleaned_at=timezone.now(), sterilized_at=timezone.now(),
            packed_at=timezone.now(), delivered_at=timezone.now(),
        )
        RequestItem.objects.create(
            request=self.req1, inventory_item=inventory["scalpel"], quantity=2,
        )

        self.req2 = InstrumentRequest.objects.create(
            requester=nurse, priority="Urgent", status="Collected",
            department="Emergency", notes="Emergency case",
            submitted_at=timezone.now(), collected_at=timezone.now(),
        )
        RequestItem.objects.create(
            request=self.req2, inventory_item=inventory["forceps"], quantity=5,
        )
        RequestItem.objects.create(
            request=self.req2, inventory_item=inventory["retractor"], quantity=1,
        )

        self.req3 = InstrumentRequest.objects.create(
            requester=nurse, priority="Normal", status="Requested",
            department="Emergency", notes="Afternoon schedule",
        )
        RequestItem.objects.create(
            request=self.req3, inventory_item=inventory["scalpel"], quantity=3,
        )

    @pytest.mark.integration
    def test_search_scalpel_returns_two_requests(self, hospital_client):
        """Searching 'Scalpel' finds req1 and req3 (both have scalpels)."""
        resp = hospital_client.get(reverse("hospital_audit"), {"q": "Scalpel"})
        results = list(resp.context["results"])
        result_pks = [r.pk for r in results]
        assert self.req1.pk in result_pks
        assert self.req3.pk in result_pks
        assert self.req2.pk not in result_pks  # req2 has forceps, not scalpel

    @pytest.mark.integration
    def test_search_forceps_returns_one_request(self, hospital_client):
        """Searching 'Forceps' only finds req2."""
        resp = hospital_client.get(reverse("hospital_audit"), {"q": "Forceps"})
        results = list(resp.context["results"])
        result_pks = [r.pk for r in results]
        assert self.req2.pk in result_pks
        assert self.req1.pk not in result_pks

    @pytest.mark.integration
    def test_search_specific_id_returns_only_that_request(self, hospital_client):
        """Searching by a specific ID returns exactly one result."""
        resp = hospital_client.get(reverse("hospital_audit"), {"q": str(self.req2.pk)})
        results = list(resp.context["results"])
        assert len(results) == 1
        assert results[0].pk == self.req2.pk

    @pytest.mark.integration
    def test_delivered_request_shows_complete_timeline(self, hospital_client):
        """A delivered request has all 6 timestamps in the audit results."""
        resp = hospital_client.get(reverse("hospital_audit"), {"q": str(self.req1.pk)})
        result = list(resp.context["results"])[0]
        assert result.submitted_at is not None
        assert result.collected_at is not None
        assert result.cleaned_at is not None
        assert result.sterilized_at is not None
        assert result.packed_at is not None
        assert result.delivered_at is not None

    @pytest.mark.integration
    def test_partial_lifecycle_shows_only_reached_stages(self, hospital_client):
        """A Collected request only has submitted_at and collected_at set."""
        resp = hospital_client.get(reverse("hospital_audit"), {"q": str(self.req2.pk)})
        result = list(resp.context["results"])[0]
        assert result.submitted_at is not None
        assert result.collected_at is not None
        assert result.cleaned_at is None
        assert result.sterilized_at is None
        assert result.packed_at is None
        assert result.delivered_at is None


# ══════════════════════════════════════════════════════════════════════════════
#  5. BATCH & OPERATOR INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestBatchOperatorAudit:
    """
    Integration tests verifying that sterilization batch and operator
    information flows correctly into the audit view.
    """

    @pytest.mark.integration
    def test_batch_operator_in_audit_results(
        self, hospital_client, nurse, tech, inventory
    ):
        """
        A request sterilized with a batch shows the batch operator
        in the audit results.
        """
        batch = SterilizationBatch.objects.create(
            operator=tech, temperature=134.0, cycle_duration=18.0,
            status="Completed",
        )
        req = InstrumentRequest.objects.create(
            requester=nurse, priority="Normal", status="Sterilized",
            department="Emergency", batch=batch, last_operator=tech,
            submitted_at=timezone.now(), collected_at=timezone.now(),
            cleaned_at=timezone.now(), sterilized_at=timezone.now(),
        )
        RequestItem.objects.create(
            request=req, inventory_item=inventory["scalpel"], quantity=1,
        )

        resp = hospital_client.get(reverse("hospital_audit"), {"q": str(req.pk)})
        content = resp.content.decode()

        # Batch info should be visible
        assert f"Batch #{batch.pk}" in content
        assert tech.email in content

    @pytest.mark.integration
    def test_request_without_batch_shows_no_batch_info(
        self, hospital_client, nurse, inventory
    ):
        """
        A request that hasn't been sterilized yet shows no batch info.
        """
        req = InstrumentRequest.objects.create(
            requester=nurse, priority="Normal", status="Collected",
            department="Emergency",
            submitted_at=timezone.now(), collected_at=timezone.now(),
        )
        RequestItem.objects.create(
            request=req, inventory_item=inventory["forceps"], quantity=1,
        )

        resp = hospital_client.get(reverse("hospital_audit"), {"q": str(req.pk)})
        content = resp.content.decode()
        assert "Batch #" not in content


# ══════════════════════════════════════════════════════════════════════════════
#  6. NOTIFICATION COEXISTENCE
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestNotificationCoexistence:
    """
    Verify that the audit feature does not interfere with the existing
    notification system (no regressions on nurse notifications).
    """

    @pytest.mark.integration
    def test_notifications_still_created_during_workflow(
        self, nurse_client, tech_client, nurse, inventory
    ):
        """
        When tech marks request as Collected, nurse notification is still
        created (existing feature not broken by PROJ-31 changes).
        """
        # Nurse submits request
        post_data = {
            "priority": "Normal",
            "notes": "Notification test",
            "instruments": ["Surgical Scalpel"],
            "quantity_Surgical Scalpel": "1",
        }
        nurse_client.post(reverse("save_instrument_request"), data=post_data)
        req = InstrumentRequest.objects.filter(requester=nurse).first()

        # Tech marks as Collected (via unified endpoint)
        url = reverse("cssd_update_request_status", kwargs={"pk": req.pk, "status": "Collected"})
        tech_client.post(url)

        # Notification should exist for the nurse
        assert Notification.objects.filter(
            recipient=nurse, request=req,
        ).exists()

    @pytest.mark.integration
    def test_audit_does_not_create_notifications(
        self, hospital_client, nurse, inventory
    ):
        """Searching audit history does NOT create any notifications."""
        req = InstrumentRequest.objects.create(
            requester=nurse, priority="Normal", status="Requested",
            department="Emergency",
        )
        notif_count_before = Notification.objects.count()

        hospital_client.get(reverse("hospital_audit"), {"q": str(req.pk)})

        assert Notification.objects.count() == notif_count_before


# ══════════════════════════════════════════════════════════════════════════════
#  7. HOSPITAL REPORT INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestHospitalReportIntegration:
    """
    Integration tests for the hospital report dashboard to ensure
    it works with actual batch and request data.
    """

    @pytest.mark.integration
    def test_report_shows_batch_count(self, hospital_client, tech):
        """Report page context includes total_batches for today's date."""
        today = timezone.now().date().strftime('%Y-%m-%d')

        SterilizationBatch.objects.create(
            operator=tech, temperature=134.0, cycle_duration=18.0,
        )
        SterilizationBatch.objects.create(
            operator=tech, temperature=121.0, cycle_duration=30.0,
        )

        resp = hospital_client.get(reverse("hospital_report"), {"date": today})
        assert resp.status_code == 200
        assert resp.context["total_batches"] == 2

    @pytest.mark.integration
    def test_report_date_filtering(self, hospital_client, tech):
        """Report filtered by date only shows batches from that date."""
        SterilizationBatch.objects.create(
            operator=tech, temperature=134.0, cycle_duration=18.0,
        )

        # Request report for a date in the past (no batches)
        resp = hospital_client.get(reverse("hospital_report"), {"date": "2020-01-01"})
        assert resp.status_code == 200
        assert resp.context["total_batches"] == 0

    @pytest.mark.integration
    def test_report_shows_operator_count(self, hospital_client, tech, nurse):
        """Report page includes the count of distinct operators."""
        today = timezone.now().date().strftime('%Y-%m-%d')

        # Create batches by the tech (only CSSD user operates batches)
        SterilizationBatch.objects.create(
            operator=tech, temperature=134.0, cycle_duration=18.0,
        )

        resp = hospital_client.get(reverse("hospital_report"), {"date": today})
        assert len(resp.context["operators"]) == 1
        assert tech.email in resp.context["operators"]
