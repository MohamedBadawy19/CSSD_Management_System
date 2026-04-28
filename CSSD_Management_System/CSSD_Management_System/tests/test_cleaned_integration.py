"""
Integration Tests - US-18 Cleaned transition

These tests exercise the cleaned workflow through real Django views:
  1. A collected request can be cleaned by CSSD staff.
  2. Cleaning records the acting operator and nurse notification.
  3. Cleaning can be observed by a nurse through persisted request data.
  4. Invalid direct clean attempts from Requested are blocked.
"""

from django.test import Client, TestCase
from django.urls import reverse

from CSSD_Management_System.models import CustomUser, InstrumentRequest, InventoryItem, Notification, RequestItem


def make_user(email, role, department, password='Test1234!'):
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        role=role,
        department=department,
        first_name='Test',
    )
    return user, password


def make_collected_request(nurse):
    item = InventoryItem.objects.create(
        name='Forceps Set',
        category='Surgical',
        current_stock=6,
        min_threshold=1,
    )
    request_obj = InstrumentRequest.objects.create(
        requester=nurse,
        department=nurse.department,
        priority='Urgent',
        status='Collected',
    )
    RequestItem.objects.create(request=request_obj, inventory_item=item, quantity=1)
    return request_obj


class CleanedWorkflowIntegrationTest(TestCase):
    def setUp(self):
        self.nurse_client = Client()
        self.cssd_client = Client()
        self.nurse, self.nurse_password = make_user('nurse-int@test.com', 'Department Nurse', 'ICU')
        self.cssd, self.cssd_password = make_user('cssd-int@test.com', 'CSSD Technician', 'CSSD')

        self.nurse_client.login(email=self.nurse.email, password=self.nurse_password)
        self.cssd_client.login(email=self.cssd.email, password=self.cssd_password)

        self.req = make_collected_request(self.nurse)

    def test_cssd_can_clean_and_nurse_sees_updated_status(self):
        response = self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Cleaned'})
        )
        self.assertEqual(response.status_code, 302)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Cleaned')
        nurse_view = InstrumentRequest.objects.get(pk=self.req.pk, requester=self.nurse)
        self.assertEqual(nurse_view.status, 'Cleaned')

    def test_cleaning_creates_notification_and_records_operator(self):
        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': self.req.pk, 'status': 'Cleaned'})
        )

        notification = Notification.objects.filter(recipient=self.nurse, request=self.req).first()
        self.assertIsNotNone(notification)
        self.req.refresh_from_db()
        self.assertEqual(self.req.last_operator, self.cssd)
        self.assertIsNotNone(self.req.cleaned_at)

    def test_requested_cannot_be_cleaned_directly(self):
        blocked_request = make_collected_request(self.nurse)
        blocked_request.status = 'Requested'
        blocked_request.save(update_fields=['status'])

        self.cssd_client.post(
            reverse('cssd_update_request_status', kwargs={'pk': blocked_request.pk, 'status': 'Cleaned'})
        )
        blocked_request.refresh_from_db()
        self.assertEqual(blocked_request.status, 'Requested')
