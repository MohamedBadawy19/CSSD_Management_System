"""
PROJ-22 / US-12 — Create Sterilization Batch
=============================================
Unit tests  : SterilizationBatchForm validation
Integration : View behaviour for both ACs end-to-end

Acceptance Criteria:
  AC-1  CSSD Tech creates batch + adds multiple instrument sets → saved with unique batch ID
  AC-2  When viewing the batch record → status shows "In Progress"
"""

import pytest
from django.urls import reverse

from CSSD_Management_System.models import CustomUser, InstrumentSet, SterilizationBatch
from CSSD_Management_System.forms import SterilizationBatchForm


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def cssd_user(db):
    return CustomUser.objects.create_user(
        email='tech@test.com', password='TechPass1!',
        role='CSSD Technician', department='CSSD',
    )

@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_user(
        email='admin@test.com', password='AdminPass1!',
        role='System Administrator', department='CSSD',
    )

@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email='nurse@test.com', password='NursePass1!',
        role='Department Nurse', department='ICU',
    )

@pytest.fixture
def set_a(db):
    return InstrumentSet.objects.create(name='Set A', type='General', quantity=3)

@pytest.fixture
def set_b(db):
    return InstrumentSet.objects.create(name='Set B', type='Cardiac', quantity=2)


# ── Unit Tests — SterilizationBatchForm ──────────────────────────────────────

@pytest.mark.django_db
class TestSterilizationBatchForm:

    def test_valid_form_no_sets(self, cssd_user):
        form = SterilizationBatchForm(data={
            'temperature': 134, 'cycle_duration': 30, 'instrument_sets': [],
        })
        assert form.is_valid(), form.errors

    def test_valid_form_with_multiple_sets(self, cssd_user, set_a, set_b):
        form = SterilizationBatchForm(data={
            'temperature': 134,
            'cycle_duration': 30,
            'instrument_sets': [set_a.pk, set_b.pk],
        })
        assert form.is_valid(), form.errors

    def test_temperature_below_121_rejected(self):
        form = SterilizationBatchForm(data={
            'temperature': 100, 'cycle_duration': 30, 'instrument_sets': [],
        })
        assert not form.is_valid()
        assert 'temperature' in form.errors

    def test_temperature_exactly_121_accepted(self):
        form = SterilizationBatchForm(data={
            'temperature': 121, 'cycle_duration': 30, 'instrument_sets': [],
        })
        assert form.is_valid(), form.errors

    def test_zero_duration_rejected(self):
        form = SterilizationBatchForm(data={
            'temperature': 134, 'cycle_duration': 0, 'instrument_sets': [],
        })
        assert not form.is_valid()
        assert 'cycle_duration' in form.errors

    def test_missing_temperature_rejected(self):
        form = SterilizationBatchForm(data={
            'temperature': '', 'cycle_duration': 30, 'instrument_sets': [],
        })
        assert not form.is_valid()
        assert 'temperature' in form.errors


# ── Integration Tests — Views ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestSterilizationBatchCreateView:

    CREATE_URL = '/dashboard/cssd/batches/create/'

    # Access control
    def test_unauthenticated_redirected(self, client):
        r = client.get(self.CREATE_URL)
        assert r.status_code in (302, 301)

    def test_nurse_forbidden(self, client, nurse_user):
        client.login(email='nurse@test.com', password='NursePass1!')
        r = client.get(self.CREATE_URL)
        assert r.status_code == 403

    def test_cssd_tech_can_access(self, client, cssd_user):
        client.login(email='tech@test.com', password='TechPass1!')
        r = client.get(self.CREATE_URL)
        assert r.status_code == 200

    def test_admin_can_access(self, client, admin_user):
        client.login(email='admin@test.com', password='AdminPass1!')
        r = client.get(self.CREATE_URL)
        assert r.status_code == 200

    # AC-1: batch saved with unique ID + multiple sets
    def test_ac1_batch_created_with_unique_id(self, client, cssd_user, set_a, set_b):
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {
            'temperature': 134,
            'cycle_duration': 30,
            'instrument_sets': [set_a.pk, set_b.pk],
        })
        assert SterilizationBatch.objects.count() == 1
        batch = SterilizationBatch.objects.first()
        assert batch.pk is not None  # unique ID assigned

    def test_ac1_two_batches_have_different_ids(self, client, cssd_user):
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {'temperature': 134, 'cycle_duration': 30, 'instrument_sets': []})
        client.post(self.CREATE_URL, {'temperature': 121, 'cycle_duration': 15, 'instrument_sets': []})
        ids = list(SterilizationBatch.objects.values_list('pk', flat=True))
        assert ids[0] != ids[1]  # unique IDs

    def test_ac1_multiple_instrument_sets_linked(self, client, cssd_user, set_a, set_b):
        """AC-1: Both selected instrument sets are saved in the batch M2M."""
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {
            'temperature': 134,
            'cycle_duration': 30,
            'instrument_sets': [set_a.pk, set_b.pk],
        })
        batch = SterilizationBatch.objects.first()
        linked_ids = set(batch.instrument_sets.values_list('pk', flat=True))
        assert set_a.pk in linked_ids
        assert set_b.pk in linked_ids

    def test_ac1_single_instrument_set_linked(self, client, cssd_user, set_a):
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {
            'temperature': 134, 'cycle_duration': 30,
            'instrument_sets': [set_a.pk],
        })
        batch = SterilizationBatch.objects.first()
        assert batch.instrument_sets.filter(pk=set_a.pk).exists()

    def test_ac1_operator_auto_assigned(self, client, cssd_user):
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {'temperature': 134, 'cycle_duration': 30, 'instrument_sets': []})
        batch = SterilizationBatch.objects.first()
        assert batch.operator == cssd_user

    def test_ac1_redirects_to_batch_detail(self, client, cssd_user):
        client.login(email='tech@test.com', password='TechPass1!')
        r = client.post(self.CREATE_URL, {
            'temperature': 134, 'cycle_duration': 30, 'instrument_sets': [],
        })
        batch = SterilizationBatch.objects.first()
        assert r.status_code == 302
        assert f'/batches/{batch.pk}/' in r.url

    # AC-2: status shows "In Progress"
    def test_ac2_batch_status_is_in_progress(self, client, cssd_user):
        """AC-2: Newly created batch always has status='In Progress'."""
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {'temperature': 134, 'cycle_duration': 30, 'instrument_sets': []})
        batch = SterilizationBatch.objects.first()
        assert batch.status == 'In Progress'

    def test_ac2_status_shown_on_detail_page(self, client, cssd_user):
        """AC-2: The batch detail page contains 'In Progress' text."""
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {'temperature': 134, 'cycle_duration': 30, 'instrument_sets': []})
        batch = SterilizationBatch.objects.first()
        r = client.get(f'/dashboard/cssd/batches/{batch.pk}/')
        assert r.status_code == 200
        assert 'In Progress' in r.content.decode()

    def test_ac2_model_default_is_in_progress(self, db, cssd_user):
        """AC-2: Model-level default — no view needed."""
        batch = SterilizationBatch.objects.create(
            operator=cssd_user, temperature=134, cycle_duration=30,
        )
        assert batch.status == 'In Progress'

    # Validation guard
    def test_invalid_temperature_does_not_create_batch(self, client, cssd_user):
        client.login(email='tech@test.com', password='TechPass1!')
        client.post(self.CREATE_URL, {'temperature': 50, 'cycle_duration': 30, 'instrument_sets': []})
        assert SterilizationBatch.objects.count() == 0
