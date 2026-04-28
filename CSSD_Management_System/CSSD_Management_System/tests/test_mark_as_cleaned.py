"""
Unit Tests - US-18: Mark Instrument Request as Cleaned

Coverage:
  1. Happy path: Collected -> Cleaned
  2. Invalid transition: non-Collected statuses blocked
  3. Invalid status slug: only 'Cleaned' accepted in this branch
  4. Unauthenticated access: redirect to login
  5. Nurse access: 403 Forbidden
  6. Notification created on success
  7. Timestamps and operator recorded on success
  8. Non-existent request: 404
"""

from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser,
    InstrumentRequest,
    InventoryItem,
    Notification,
    RequestItem,
)


def make_cssd(email='cssd-clean@test.com', password='Test1234!'):
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        role='CSSD Technician',
        department='CSSD',
        first_name='Ali',
    )
    return user, password


def make_nurse(email='nurse-clean@test.com', password='Test1234!'):
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        role='Department Nurse',
        department='ICU',
        first_name='Sara',
    )
    return user, password


def make_request(nurse, status='Collected'):
    item = InventoryItem.objects.create(
        name='Scalpel Set',
        category='Surgical',
        current_stock=10,
        min_threshold=2,
    )
    request_obj = InstrumentRequest.objects.create(
        requester=nurse,
        department=nurse.department,
        priority='Normal',
        status=status,
    )
    RequestItem.objects.create(request=request_obj, inventory_item=item, quantity=2)
    return request_obj


def clean_url(pk, slug='Cleaned'):
    return reverse('cssd_update_request_status', kwargs={'pk': pk, 'status': slug})


class MarkAsCleanedHappyPathTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cssd_user, self.password = make_cssd()
        self.nurse, _ = make_nurse()
        self.req = make_request(self.nurse, status='Collected')
        self.client.login(email=self.cssd_user.email, password=self.password)

    def test_status_changes_to_cleaned(self):
        self.client.post(clean_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Cleaned')

    def test_cleaned_at_timestamp_set(self):
        before = timezone.now()
        self.client.post(clean_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertIsNotNone(self.req.cleaned_at)
        self.assertGreaterEqual(self.req.cleaned_at, before)

    def test_last_operator_recorded(self):
        self.client.post(clean_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.last_operator, self.cssd_user)

    def test_redirects_to_request_detail(self):
        response = self.client.post(clean_url(self.req.pk))
        self.assertRedirects(
            response,
            reverse('cssd_request_detail', kwargs={'pk': self.req.pk}),
            fetch_redirect_response=False,
        )

    def test_success_message_displayed(self):
        response = self.client.post(clean_url(self.req.pk))
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('Cleaned' in message for message in messages))

    def test_notification_created_for_nurse(self):
        self.client.post(clean_url(self.req.pk))
        notification = Notification.objects.filter(recipient=self.nurse, request=self.req).first()
        self.assertIsNotNone(notification)
        self.assertIn('clean', notification.message.lower())

    def test_notification_is_unread_by_default(self):
        self.client.post(clean_url(self.req.pk))
        notification = Notification.objects.get(recipient=self.nurse, request=self.req)
        self.assertFalse(notification.is_read)


class MarkAsCleanedInvalidTransitionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cssd_user, self.password = make_cssd()
        self.nurse, _ = make_nurse()
        self.client.login(email=self.cssd_user.email, password=self.password)

    def _assert_blocked(self, initial_status):
        request_obj = make_request(self.nurse, status=initial_status)
        response = self.client.post(clean_url(request_obj.pk))
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, initial_status)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('only' in message.lower() or 'current status' in message.lower() for message in messages))

    def test_cannot_clean_requested(self):
        self._assert_blocked('Requested')

    def test_cannot_clean_already_cleaned(self):
        self._assert_blocked('Cleaned')

    def test_cannot_clean_sterilized(self):
        self._assert_blocked('Sterilized')

    def test_cannot_clean_packed(self):
        self._assert_blocked('Packed')

    def test_cannot_clean_delivered(self):
        self._assert_blocked('Delivered')


class MarkAsCleanedInvalidStatusSlugTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cssd_user, self.password = make_cssd()
        self.nurse, _ = make_nurse()
        self.req = make_request(self.nurse, status='Collected')
        self.client.login(email=self.cssd_user.email, password=self.password)

    def test_collected_slug_rejected(self):
        response = self.client.post(clean_url(self.req.pk, slug='Collected'))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Collected')
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('Cleaned' in message for message in messages))

    def test_sterilized_slug_rejected(self):
        self.client.post(clean_url(self.req.pk, slug='Sterilized'))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Collected')

    def test_packed_slug_rejected(self):
        self.client.post(clean_url(self.req.pk, slug='Packed'))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Collected')


class MarkAsCleanedAccessControlTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cssd_user, self.cssd_password = make_cssd()
        self.nurse, self.nurse_password = make_nurse()
        self.req = make_request(self.nurse, status='Collected')

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.post(clean_url(self.req.pk))
        self.assertIn(response.status_code, [301, 302])
        self.assertIn(reverse('login'), response['Location'])

    def test_nurse_gets_403(self):
        self.client.login(email=self.nurse.email, password=self.nurse_password)
        response = self.client.post(clean_url(self.req.pk))
        self.assertEqual(response.status_code, 403)

    def test_nurse_cannot_change_status(self):
        self.client.login(email=self.nurse.email, password=self.nurse_password)
        self.client.post(clean_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Collected')

    def test_cssd_technician_allowed(self):
        self.client.login(email=self.cssd_user.email, password=self.cssd_password)
        self.client.post(clean_url(self.req.pk))
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Cleaned')


class MarkAsCleanedEdgeCasesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cssd_user, self.password = make_cssd()
        self.nurse, _ = make_nurse()
        self.client.login(email=self.cssd_user.email, password=self.password)

    def test_nonexistent_request_returns_404(self):
        response = self.client.post(clean_url(99999))
        self.assertEqual(response.status_code, 404)

    def test_get_request_does_not_mutate_status(self):
        request_obj = make_request(self.nurse, status='Collected')
        response = self.client.get(clean_url(request_obj.pk))
        self.assertEqual(response.status_code, 405)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'Collected')

    def test_double_clean_blocked(self):
        request_obj = make_request(self.nurse, status='Collected')
        self.client.post(clean_url(request_obj.pk))
        self.client.post(clean_url(request_obj.pk))
        notification_count = Notification.objects.filter(recipient=self.nurse, request=request_obj).count()
        self.assertEqual(notification_count, 1)
