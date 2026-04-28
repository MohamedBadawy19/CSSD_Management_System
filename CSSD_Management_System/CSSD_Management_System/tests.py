from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from .models import CustomUser, InventoryItem, InstrumentRequest, RequestItem, Notification, SterilizationBatch
from .decorators import cssd_staff_required
from django.http import HttpResponse

class StoryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create users
        self.cssd_tech = CustomUser.objects.create_user(
            email='cssd@example.com',
            password='password123',
            role='CSSD Technician'
        )
        self.nurse = CustomUser.objects.create_user(
            email='nurse@example.com',
            password='password123',
            role='Department Nurse',
            department='ER'
        )
        self.sys_admin = CustomUser.objects.create_user(
            email='admin@example.com',
            password='password123',
            role='System Administrator'
        )
        
        # Create inventory items
        self.inventory_item = InventoryItem.objects.create(
            name='Scalpel',
            category='Surgical',
            current_stock=10,
            min_threshold=5
        )
        self.inventory_item_low = InventoryItem.objects.create(
            name='Forceps',
            category='Surgical',
            current_stock=2,
            min_threshold=5
        )
        
        # Create requests
        self.request1 = InstrumentRequest.objects.create(
            requester=self.nurse,
            priority='Normal',
            department='ER',
            status='Requested'
        )
        RequestItem.objects.create(
            request=self.request1,
            inventory_item=self.inventory_item,
            quantity=1
        )

        self.request_collected = InstrumentRequest.objects.create(
            requester=self.nurse,
            priority='Urgent',
            department='ER',
            status='Collected'
        )
        self.request_cleaned = InstrumentRequest.objects.create(
            requester=self.nurse,
            status='Cleaned'
        )
        self.request_sterilized = InstrumentRequest.objects.create(
            requester=self.nurse,
            status='Sterilized'
        )
        self.request_packed = InstrumentRequest.objects.create(
            requester=self.nurse,
            status='Packed'
        )

    # US-01 — CSSD Staff Login
    def test_cssd_staff_login(self):
        # Valid login
        response = self.client.post(reverse('login'), {'username': 'cssd@example.com', 'password': 'password123'})
        self.assertRedirects(response, reverse('dashboard_router'))
        
        self.client.logout()
        # Invalid login
        response = self.client.post(reverse('login'), {'username': 'cssd@example.com', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    # US-02 — Department Nurse Login
    def test_nurse_login_routing(self):
        self.client.login(email='nurse@example.com', password='password123')
        response = self.client.get(reverse('dashboard_router'))
        self.assertRedirects(response, reverse('nurse_dashboard'))

    # US-03 — Restrict Nurse Access to CSSD Endpoints
    def test_restrict_nurse_access_decorator(self):
        @cssd_staff_required
        def dummy_view(request):
            return HttpResponse("Success")
        
        request = self.factory.get('/dummy/')
        request.user = self.nurse
        response = dummy_view(request)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Denied", response.content)
        
        request.user = self.cssd_tech
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)

    # US-05 — Submit an Instrument Request
    def test_submit_instrument_request(self):
        self.client.login(email='nurse@example.com', password='password123')
        response = self.client.post(reverse('save_instrument_request'), {
            'instruments': ['Scalpel'],
            'quantity_Scalpel': 2,
            'priority': 'Urgent',
            'notes': 'Need ASAP'
        })
        self.assertRedirects(response, reverse('nurse_create_request'))
        
        new_req = InstrumentRequest.objects.last()
        self.assertEqual(new_req.priority, 'Urgent')
        self.assertEqual(new_req.requester, self.nurse)
        
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.current_stock, 8)

    # US-06 — View Available Sterile Stock
    def test_view_sterile_stock(self):
        self.client.login(email='nurse@example.com', password='password123')
        response = self.client.get(reverse('nurse_sterile_stock'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('packed_requests', response.context)
        
        packed_ids = [r.id for r in response.context['packed_requests']]
        self.assertIn(self.request_packed.id, packed_ids)
        self.assertNotIn(self.request1.id, packed_ids)

    # US-07 — Mark Instrument as Collected
    def test_mark_collected(self):
        self.client.login(email='cssd@example.com', password='password123')
        response = self.client.post(reverse('mark_collected', args=[self.request1.id]))
        self.assertRedirects(response, reverse('cssd_request_details', args=[self.request1.id]))
        
        self.request1.refresh_from_db()
        self.assertEqual(self.request1.status, 'Collected')
        self.assertIsNotNone(self.request1.collected_at)
        
        notif = Notification.objects.filter(request=self.request1).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.recipient, self.nurse)

    # US-08 — Mark Instrument as Cleaned
    def test_mark_cleaned(self):
        self.client.login(email='cssd@example.com', password='password123')
        response = self.client.post(reverse('mark_cleaned', args=[self.request_collected.id]))
        self.assertRedirects(response, reverse('cssd_request_details', args=[self.request_collected.id]))
        
        self.request_collected.refresh_from_db()
        self.assertEqual(self.request_collected.status, 'Cleaned')
        self.assertIsNotNone(self.request_collected.cleaned_at)
        
        response = self.client.post(reverse('mark_cleaned', args=[self.request1.id]))
        self.assertEqual(response.status_code, 200) 
        self.request1.refresh_from_db()
        self.assertEqual(self.request1.status, 'Requested')

    # US-09 — Mark Instrument as Sterilized
    def test_mark_sterilized(self):
        self.client.login(email='cssd@example.com', password='password123')
        response = self.client.post(reverse('mark_sterilized', args=[self.request_cleaned.id]))
        self.assertRedirects(response, reverse('cssd_request_details', args=[self.request_cleaned.id]))
        
        self.request_cleaned.refresh_from_db()
        self.assertEqual(self.request_cleaned.status, 'Sterilized')
        self.assertIsNotNone(self.request_cleaned.sterilized_at)

    # US-10 — Mark Instrument as Packed
    def test_mark_packed(self):
        self.client.login(email='cssd@example.com', password='password123')
        response = self.client.post(reverse('mark_packed', args=[self.request_sterilized.id]))
        self.assertRedirects(response, reverse('cssd_request_details', args=[self.request_sterilized.id]))
        
        self.request_sterilized.refresh_from_db()
        self.assertEqual(self.request_sterilized.status, 'Packed')
        self.assertIsNotNone(self.request_sterilized.packed_at)

    # US-15 & US-16 — Dashboard Counters (Pending & Alerts)
    def test_cssd_dashboard_counters(self):
        self.client.login(email='cssd@example.com', password='password123')
        response = self.client.get(reverse('dashboard_router'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stat_pending'], 1)
        self.assertEqual(response.context['stat_alerts'], 1)

    def test_cssd_inventory_alerts_page(self):
        self.client.login(email='cssd@example.com', password='password123')
        response = self.client.get(reverse('cssd_inventory_alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('alert_items', response.context)

        alert_names = [item.name for item in response.context['alert_items']]
        self.assertIn(self.inventory_item_low.name, alert_names)
        self.assertNotIn(self.inventory_item.name, alert_names)

    # US-17 — View Active Requests (Nurse Dashboard)
    def test_nurse_dashboard_active_requests(self):
        self.client.login(email='nurse@example.com', password='password123')
        response = self.client.get(reverse('nurse_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 5)
        self.assertEqual(response.context['in_progress'], 4)
        self.assertEqual(response.context['urgent'], 1)

    # US-18 — View Estimated Completion Time
    def test_estimated_completion_time(self):
        eta = self.request1.get_eta()
        self.assertIn("Ready by ~", eta)


class BugRegressionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.nurse = CustomUser.objects.create_user(
            email='bug-nurse@example.com',
            password='password123',
            role='Department Nurse',
            department='ER'
        )
        self.scalpel = InventoryItem.objects.create(
            name='Bug Scalpel',
            category='Surgical',
            current_stock=5,
            min_threshold=2
        )
        self.forceps = InventoryItem.objects.create(
            name='Bug Forceps',
            category='Surgical',
            current_stock=1,
            min_threshold=2
        )

    def test_save_instrument_request_requires_authenticated_user(self):
        response = self.client.post(reverse('save_instrument_request'), {
            'instruments': ['Bug Scalpel'],
            'quantity_Bug Scalpel': 1,
            'priority': 'Normal',
            'notes': 'anonymous request should not succeed'
        })

        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(InstrumentRequest.objects.count(), 0)
        self.scalpel.refresh_from_db()
        self.assertEqual(self.scalpel.current_stock, 5)

    def test_insufficient_stock_does_not_create_request(self):
        self.client.login(email='bug-nurse@example.com', password='password123')

        response = self.client.post(reverse('save_instrument_request'), {
            'instruments': ['Bug Forceps'],
            'quantity_Bug Forceps': 3,
            'priority': 'Urgent',
            'notes': 'quantity exceeds stock'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(InstrumentRequest.objects.count(), 0)
        self.assertEqual(RequestItem.objects.count(), 0)
        self.forceps.refresh_from_db()
        self.assertEqual(self.forceps.current_stock, 1)

    def test_multi_item_request_rolls_back_when_any_item_is_unavailable(self):
        self.client.login(email='bug-nurse@example.com', password='password123')

        response = self.client.post(reverse('save_instrument_request'), {
            'instruments': ['Bug Scalpel', 'Bug Forceps'],
            'quantity_Bug Scalpel': 2,
            'quantity_Bug Forceps': 3,
            'priority': 'Urgent',
            'notes': 'request should be atomic'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(InstrumentRequest.objects.count(), 0)
        self.assertEqual(RequestItem.objects.count(), 0)

        self.scalpel.refresh_from_db()
        self.forceps.refresh_from_db()
        self.assertEqual(self.scalpel.current_stock, 5)
        self.assertEqual(self.forceps.current_stock, 1)
