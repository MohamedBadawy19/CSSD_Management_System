"""
Integration Tests — Full CSSD Pipeline
Covers the complete workflow after all feature branches are merged into dev.

Flow tested:
  Nurse creates request → CSSD collects → cleans → sterilizes (batch) →
  packs → Nurse delivers → CSSD inventory alerts → batch management
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser, InventoryItem, InstrumentRequest,
    RequestItem, Notification, SterilizationBatch,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_user(email, role, dept, first_name='Test', password='Test1234!'):
    u = CustomUser.objects.create_user(
        email=email, password=password,
        role=role, department=dept, first_name=first_name,
    )
    return u, password


def make_inventory():
    i1 = InventoryItem.objects.create(name='Scalpel Set', category='Surgical', current_stock=20, min_threshold=5)
    i2 = InventoryItem.objects.create(name='Forceps',     category='Surgical', current_stock=2,  min_threshold=5)
    i3 = InventoryItem.objects.create(name='Clamp Set',  category='Clamps',   current_stock=0,  min_threshold=3)
    return i1, i2, i3


# ---------------------------------------------------------------------------
# 1. Home & Auth (PROJ-0, PROJ-4)
# ---------------------------------------------------------------------------

class HomeAndAuthTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.nurse, self.pwd = make_user('nurse@test.com', 'Department Nurse', 'ICU')
        self.cssd,  _        = make_user('cssd@test.com',  'CSSD Technician',  'CSSD')

    def test_home_page_loads(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)

    def test_login_page_defaults_to_staff_template(self):
        r = self.client.get(reverse('login'))
        self.assertEqual(r.status_code, 200)

    def test_nurse_login_routes_to_nurse_dashboard(self):
        r = self.client.post(reverse('login'), {'username': 'nurse@test.com', 'password': 'Test1234!'}, follow=True)
        self.assertRedirects(r, reverse('nurse_dashboard'), fetch_redirect_response=False)

    def test_cssd_login_routes_to_cssd_dashboard(self):
        self.client.login(email='cssd@test.com', password='Test1234!')
        r = self.client.get(reverse('dashboard_router'), follow=True)
        self.assertRedirects(r, reverse('cssd_dashboard'), fetch_redirect_response=False)

    def test_wrong_password_shows_error(self):
        r = self.client.post(reverse('login'), {'username': 'nurse@test.com', 'password': 'wrong'}, follow=True)
        msgs = [str(m) for m in r.context['messages']] if r.context and 'messages' in r.context else []
        # Error shown either via messages or form errors
        form = r.context.get('form')
        has_error = bool(msgs) or (form and form.errors)
        self.assertTrue(has_error, "Wrong password should produce an error")

    def test_unauthenticated_dashboard_redirects_to_login(self):
        r = self.client.get(reverse('cssd_dashboard'))
        self.assertIn(r.status_code, [301, 302])

    def test_nurse_cannot_access_cssd_dashboard(self):
        self.client.login(email='nurse@test.com', password='Test1234!')
        r = self.client.get(reverse('cssd_dashboard'))
        self.assertEqual(r.status_code, 403)

    def test_logout_clears_session(self):
        self.client.login(email='cssd@test.com', password='Test1234!')
        self.client.get(reverse('logout'))
        r = self.client.get(reverse('cssd_dashboard'))
        self.assertIn(r.status_code, [301, 302])


# ---------------------------------------------------------------------------
# 2. Nurse creates request (PROJ-6)
# ---------------------------------------------------------------------------

class NurseCreateRequestTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.nurse, self.pwd = make_user('nurse@test.com', 'Department Nurse', 'ICU')
        self.i1, self.i2, self.i3 = make_inventory()
        self.client.login(email='nurse@test.com', password=self.pwd)

    def test_create_request_success(self):
        r = self.client.post(reverse('nurse_create_request'), {
            'priority': 'Normal',
            'notes': 'Urgent surgery',
            f'quantity_{self.i1.id}': '3',
        }, follow=True)
        self.assertTrue(InstrumentRequest.objects.filter(requester=self.nurse).exists())

    def test_stock_deducted_after_request(self):
        self.client.post(reverse('nurse_create_request'), {
            'priority': 'Normal',
            f'quantity_{self.i1.id}': '5',
        })
        self.i1.refresh_from_db()
        self.assertEqual(self.i1.current_stock, 15)

    def test_insufficient_stock_blocked(self):
        r = self.client.post(reverse('nurse_create_request'), {
            'priority': 'Normal',
            f'quantity_{self.i2.id}': '10',  # only 2 in stock
        }, follow=True)
        msgs = [str(m) for m in r.context['messages']]
        self.assertTrue(any('Insufficient' in m for m in msgs))
        self.assertEqual(InstrumentRequest.objects.count(), 0)

    def test_empty_selection_blocked(self):
        r = self.client.post(reverse('nurse_create_request'), {
            'priority': 'Normal',
        }, follow=True)
        msgs = [str(m) for m in r.context['messages']]
        self.assertTrue(any('at least one' in m.lower() for m in msgs))

    def test_urgent_request_priority_saved(self):
        self.client.post(reverse('nurse_create_request'), {
            'priority': 'Urgent',
            f'quantity_{self.i1.id}': '1',
        })
        req = InstrumentRequest.objects.get(requester=self.nurse)
        self.assertEqual(req.priority, 'Urgent')

    def test_request_appears_in_nurse_dashboard(self):
        self.client.post(reverse('nurse_create_request'), {
            'priority': 'Normal',
            f'quantity_{self.i1.id}': '1',
        })
        r = self.client.get(reverse('nurse_dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'REQ-')


# ---------------------------------------------------------------------------
# 3. Full state machine pipeline (PROJ-17 → 21, Proj-17/18/19/21/20)
# ---------------------------------------------------------------------------

class FullPipelineTest(TestCase):
    """
    End-to-end: Requested → Collected → Cleaned → Sterilized → Packed → Delivered
    """

    def setUp(self):
        self.nurse_client = Client()
        self.cssd_client  = Client()

        self.nurse, _ = make_user('nurse@test.com', 'Department Nurse', 'ICU')
        self.cssd,  _ = make_user('cssd@test.com',  'CSSD Technician',  'CSSD')

        self.i1, _, _ = make_inventory()

        self.nurse_client.login(email='nurse@test.com', password='Test1234!')
        self.cssd_client.login(email='cssd@test.com',  password='Test1234!')

        # Nurse creates a request
        self.nurse_client.post(reverse('nurse_create_request'), {
            'priority': 'Normal',
            f'quantity_{self.i1.id}': '2',
        })
        self.req = InstrumentRequest.objects.get(requester=self.nurse)

    def _update(self, status):
        return self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': status}),
            follow=True,
        )

    def test_initial_status_is_requested(self):
        self.assertEqual(self.req.status, 'Requested')

    # --- US-17: Collected ---
    def test_collected_transition(self):
        self._update('Collected')
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Collected')

    def test_collected_sets_timestamp(self):
        self._update('Collected')
        self.req.refresh_from_db()
        self.assertIsNotNone(self.req.collected_at)

    def test_collected_notifies_nurse(self):
        self._update('Collected')
        self.assertTrue(
            Notification.objects.filter(recipient=self.nurse, request=self.req).exists()
        )

    # --- US-18: Cleaned ---
    def test_cleaned_transition(self):
        self._update('Collected')
        self._update('Cleaned')
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Cleaned')

    def test_cannot_skip_to_cleaned_from_requested(self):
        self._update('Cleaned')   # skip Collected
        self.req.refresh_from_db()
        self.assertNotEqual(self.req.status, 'Cleaned')

    # --- US-19: Sterilized (needs batch) ---
    def _make_batch(self):
        return SterilizationBatch.objects.create(
            operator=self.cssd, temperature=134.0, cycle_duration=18, status='In Progress'
        )

    def test_sterilized_transition_with_batch(self):
        self._update('Collected')
        self._update('Cleaned')
        batch = self._make_batch()
        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Sterilized'}),
            {'batch_id': batch.id},
            follow=True,
        )
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Sterilized')

    # --- US-21: Packed ---
    def test_packed_transition(self):
        self._update('Collected')
        self._update('Cleaned')
        batch = self._make_batch()
        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Sterilized'}),
            {'batch_id': batch.id},
        )
        self._update('Packed')
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Packed')

    # --- US-20: Delivered (nurse side) ---
    def test_delivered_transition(self):
        self._update('Collected')
        self._update('Cleaned')
        batch = self._make_batch()
        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Sterilized'}),
            {'batch_id': batch.id},
        )
        self._update('Packed')
        # Nurse marks as delivered
        deliver_url = reverse('nurse_request_detail', kwargs={'pk': self.req.pk})
        self.nurse_client.post(deliver_url, {'action': 'deliver'}, follow=True)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Delivered')

    def test_operator_recorded_on_each_transition(self):
        self._update('Collected')
        self.req.refresh_from_db()
        self.assertEqual(self.req.last_operator, self.cssd)


# ---------------------------------------------------------------------------
# 4. Batch management (Proj-24)
# ---------------------------------------------------------------------------

class BatchManagementTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cssd, _ = make_user('cssd@test.com', 'CSSD Technician', 'CSSD')
        self.client.login(email='cssd@test.com', password='Test1234!')

    def test_batch_list_loads(self):
        r = self.client.get(reverse('cssd_batch_list'))
        self.assertEqual(r.status_code, 200)

    def test_create_batch_valid(self):
        r = self.client.post(reverse('cssd_batch_create'), {
            'temperature': '134',
            'cycle_duration': '18',
        }, follow=True)
        self.assertTrue(SterilizationBatch.objects.exists())
        batch = SterilizationBatch.objects.first()
        self.assertEqual(batch.operator, self.cssd)

    def test_create_batch_temp_below_121_rejected(self):
        r = self.client.post(reverse('cssd_batch_create'), {
            'temperature': '100',
            'cycle_duration': '18',
        }, follow=True)
        self.assertFalse(SterilizationBatch.objects.exists())

    def test_batch_detail_loads(self):
        batch = SterilizationBatch.objects.create(
            operator=self.cssd, temperature=134, cycle_duration=18
        )
        r = self.client.get(reverse('cssd_batch_detail', kwargs={'pk': batch.pk}))
        self.assertEqual(r.status_code, 200)

    def test_nurse_cannot_access_batch_create(self):
        nurse, _ = make_user('nurse@test.com', 'Department Nurse', 'ICU')
        self.client.logout()
        self.client.login(email='nurse@test.com', password='Test1234!')
        r = self.client.get(reverse('cssd_batch_create'))
        self.assertEqual(r.status_code, 403)


# ---------------------------------------------------------------------------
# 5. Inventory Shortage Alerts (Proj-27)
# ---------------------------------------------------------------------------

class InventoryAlertsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cssd, _ = make_user('cssd@test.com', 'CSSD Technician', 'CSSD')
        make_inventory()  # Forceps(2<5) and Clamp(0<3) are below threshold
        self.client.login(email='cssd@test.com', password='Test1234!')

    def test_alerts_page_loads(self):
        r = self.client.get(reverse('cssd_inventory_alerts'))
        self.assertEqual(r.status_code, 200)

    def test_low_stock_items_appear(self):
        r = self.client.get(reverse('cssd_inventory_alerts'))
        # Forceps (2 < threshold 5) and Clamp Set (0 < threshold 3) should be listed
        self.assertContains(r, 'Forceps')
        self.assertContains(r, 'Clamp Set')

    def test_adequate_stock_item_not_in_alerts(self):
        r = self.client.get(reverse('cssd_inventory_alerts'))
        # Scalpel Set (20 >= threshold 5) should NOT appear
        self.assertNotContains(r, 'Scalpel Set')

    def test_cssd_dashboard_shows_alert_count(self):
        r = self.client.get(reverse('cssd_dashboard'))
        self.assertEqual(r.status_code, 200)
        # stats.alerts should be 2 (Forceps + Clamp Set)
        self.assertEqual(r.context['stats']['alerts'], 2)


# ---------------------------------------------------------------------------
# 6. Notification flow
# ---------------------------------------------------------------------------

class NotificationFlowTest(TestCase):

    def setUp(self):
        self.nurse_client = Client()
        self.cssd_client  = Client()
        self.nurse, _ = make_user('nurse@test.com', 'Department Nurse', 'ICU')
        self.cssd,  _ = make_user('cssd@test.com',  'CSSD Technician',  'CSSD')
        i1, _, _ = make_inventory()
        self.nurse_client.login(email='nurse@test.com', password='Test1234!')
        self.cssd_client.login(email='cssd@test.com',  password='Test1234!')
        self.nurse_client.post(reverse('nurse_create_request'), {
            'priority': 'Normal',
            f'quantity_{i1.id}': '1',
        })
        self.req = InstrumentRequest.objects.get(requester=self.nurse)

    def test_notification_created_after_collection(self):
        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Collected'})
        )
        self.assertEqual(Notification.objects.filter(recipient=self.nurse).count(), 1)

    def test_nurse_dashboard_shows_notification_count(self):
        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Collected'})
        )
        r = self.nurse_client.get(reverse('nurse_dashboard'))
        self.assertGreater(r.context['notif_count'], 0)

    def test_mark_notifications_read_clears_count(self):
        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Collected'})
        )
        self.nurse_client.post(reverse('nurse_mark_notifications_read'))
        r = self.nurse_client.get(reverse('nurse_dashboard'))
        self.assertEqual(r.context['notif_count'], 0)
