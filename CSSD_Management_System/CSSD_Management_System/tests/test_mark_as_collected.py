"""
Unit Tests — US-17: Mark Instrument Request as Collected
Branch: feature/Proj-17-Mark-as-Collected

Coverage:
  1. Happy path: Requested → Collected
  2. Invalid transition: non-Requested statuses blocked
  3. Invalid status slug: only 'Collected' accepted in this branch
  4. Unauthenticated access: redirect to login
  5. Nurse access: 403 Forbidden
  6. Notification created on success
  7. Timestamps and operator recorded on success
  8. Non-existent request: 404
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser, InventoryItem, InstrumentRequest, RequestItem, Notification
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_cssd(email='cssd@test.com', password='Test1234!'):
    u = CustomUser.objects.create_user(
        email=email, password=password,
        role='CSSD Technician', department='CSSD', first_name='Ali'
    )
    return u, password


def make_nurse(email='nurse@test.com', password='Test1234!'):
    u = CustomUser.objects.create_user(
        email=email, password=password,
        role='Department Nurse', department='ICU', first_name='Sara'
    )
    return u, password


def make_request(nurse, status='Requested'):
    item = InventoryItem.objects.create(
        name='Scalpel Set', category='Surgical',
        current_stock=10, min_threshold=2
    )
    req = InstrumentRequest.objects.create(
        requester=nurse,
        department=nurse.department,
        priority='Normal',
        status=status,
    )
    RequestItem.objects.create(request=req, inventory_item=item, quantity=2)
    return req


def collect_url(pk):
    return reverse('cssd_update_request_status', kwargs={'pk': pk, 'status': 'Collected'})


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class MarkAsCollectedHappyPathTest(TestCase):
    """US-17 core: a CSSD technician can move Requested → Collected."""

    def setUp(self):
        self.client = Client()
        self.cssd_user, self.pwd = make_cssd()
        self.nurse, _ = make_nurse()
        self.req = make_request(self.nurse, status='Requested')
        self.client.login(email=self.cssd_user.email, password=self.pwd)

    def test_status_changes_to_collected(self):
        """After POST, request status must be 'Collected'."""
        self.client.post(collect_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Collected')

    def test_collected_at_timestamp_set(self):
        """collected_at must be populated after the transition."""
        before = timezone.now()
        self.client.post(collect_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertIsNotNone(self.req.collected_at)
        self.assertGreaterEqual(self.req.collected_at, before)

    def test_last_operator_recorded(self):
        """last_operator must be set to the acting CSSD user."""
        self.client.post(collect_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.last_operator, self.cssd_user)

    def test_redirects_to_request_detail(self):
        """On success, response must redirect to the request's detail page."""
        response = self.client.post(collect_url(self.req.pk))
        self.assertRedirects(
            response,
            reverse('cssd_request_detail', kwargs={'pk': self.req.pk}),
            fetch_redirect_response=False,
        )

    def test_success_message_displayed(self):
        """A success flash message must be added after collection."""
        response = self.client.post(collect_url(self.req.pk), follow=True)
        messages = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('Collected' in m for m in messages),
            f"Expected a success message containing 'Collected', got: {messages}"
        )

    def test_notification_created_for_nurse(self):
        """A Notification must be sent to the requesting nurse."""
        self.client.post(collect_url(self.req.pk))
        notif = Notification.objects.filter(
            recipient=self.nurse, request=self.req
        ).first()
        self.assertIsNotNone(notif, "No notification was created for the nurse.")
        self.assertIn('collected', notif.message.lower())

    def test_notification_is_unread_by_default(self):
        """Newly created notification must be unread."""
        self.client.post(collect_url(self.req.pk))
        notif = Notification.objects.get(recipient=self.nurse, request=self.req)
        self.assertFalse(notif.is_read)


class MarkAsCollectedInvalidTransitionTest(TestCase):
    """US-17 guard: only Requested requests may be collected."""

    def setUp(self):
        self.client = Client()
        self.cssd_user, self.pwd = make_cssd()
        self.nurse, _ = make_nurse()
        self.client.login(email=self.cssd_user.email, password=self.pwd)

    def _assert_blocked(self, initial_status):
        req = make_request(self.nurse, status=initial_status)
        response = self.client.post(collect_url(req.pk), follow=True)
        req.refresh_from_db()
        # Status must NOT change
        self.assertEqual(
            req.status, initial_status,
            f"Status changed from '{initial_status}' — transition should be blocked."
        )
        # An error message must be shown
        msgs = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('only' in m.lower() or 'current status' in m.lower() for m in msgs),
            f"Expected an error message for blocked transition from '{initial_status}', got: {msgs}"
        )

    def test_cannot_collect_already_collected(self):
        self._assert_blocked('Collected')

    def test_cannot_collect_cleaned(self):
        self._assert_blocked('Cleaned')

    def test_cannot_collect_sterilized(self):
        self._assert_blocked('Sterilized')

    def test_cannot_collect_packed(self):
        self._assert_blocked('Packed')

    def test_cannot_collect_delivered(self):
        self._assert_blocked('Delivered')


class MarkAsCollectedInvalidStatusSlugTest(TestCase):
    """US-17 branch-scope guard: only 'Collected' slug is accepted."""

    def setUp(self):
        self.client = Client()
        self.cssd_user, self.pwd = make_cssd()
        self.nurse, _ = make_nurse()
        self.req = make_request(self.nurse, status='Requested')
        self.client.login(email=self.cssd_user.email, password=self.pwd)

    def _post_with_slug(self, slug):
        url = reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': slug})
        return self.client.post(url, follow=True)

    def test_cleaned_slug_rejected(self):
        response = self._post_with_slug('Cleaned')
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Requested')
        msgs = [str(m) for m in response.context['messages']]
        self.assertTrue(any('Collected' in m for m in msgs))

    def test_sterilized_slug_rejected(self):
        response = self._post_with_slug('Sterilized')
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Requested')

    def test_packed_slug_rejected(self):
        response = self._post_with_slug('Packed')
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Requested')


class MarkAsCollectedAccessControlTest(TestCase):
    """Authentication and role-based access guards."""

    def setUp(self):
        self.client = Client()
        self.cssd_user, self.cssd_pwd = make_cssd()
        self.nurse, self.nurse_pwd = make_nurse()
        self.req = make_request(self.nurse, status='Requested')

    def test_unauthenticated_redirects_to_login(self):
        """Anonymous user must be redirected to the login page."""
        response = self.client.post(collect_url(self.req.pk))
        login_url = reverse('login')
        self.assertIn(response.status_code, [301, 302])
        self.assertIn(login_url, response['Location'])

    def test_nurse_gets_403(self):
        """A Department Nurse must receive 403 Forbidden."""
        self.client.login(email=self.nurse.email, password=self.nurse_pwd)
        response = self.client.post(collect_url(self.req.pk))
        self.assertEqual(response.status_code, 403)

    def test_nurse_cannot_change_status(self):
        """Status must remain unchanged after a nurse's blocked attempt."""
        self.client.login(email=self.nurse.email, password=self.nurse_pwd)
        self.client.post(collect_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Requested')

    def test_cssd_technician_allowed(self):
        """A CSSD Technician must be able to perform the transition."""
        self.client.login(email=self.cssd_user.email, password=self.cssd_pwd)
        self.client.post(collect_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Collected')


class MarkAsCollectedEdgeCasesTest(TestCase):
    """Edge cases and robustness checks."""

    def setUp(self):
        self.client = Client()
        self.cssd_user, self.pwd = make_cssd()
        self.nurse, _ = make_nurse()
        self.client.login(email=self.cssd_user.email, password=self.pwd)

    def test_nonexistent_request_returns_404(self):
        """Attempting to collect a non-existent request must return 404."""
        url = reverse('cssd_update_request_status', kwargs={'pk': 99999, 'status': 'Collected'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_request_does_not_mutate_status(self):
        """GET to the update endpoint must return 405 and leave status unchanged."""
        req = make_request(self.nurse, status='Requested')
        response = self.client.get(collect_url(req.pk))
        self.assertEqual(response.status_code, 405, "GET must return 405 Method Not Allowed.")
        req.refresh_from_db()
        self.assertEqual(req.status, 'Requested', "GET must not trigger a state transition.")

    def test_double_collect_blocked(self):
        """Collecting an already-Collected request a second time must be blocked."""
        req = make_request(self.nurse, status='Requested')
        self.client.post(collect_url(req.pk))   # first — succeeds
        self.client.post(collect_url(req.pk))   # second — should be blocked
        # Only one notification should exist
        notif_count = Notification.objects.filter(recipient=self.nurse, request=req).count()
        self.assertEqual(notif_count, 1, "Double-collect must not create duplicate notifications.")
