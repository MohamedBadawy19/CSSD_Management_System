"""
PROJ-14 / US-04 — Register New Instrument Set
==============================================
Unit tests  : InstrumentSetForm validation (duplicate check, field validation)
Integration : View behaviour for both ACs end-to-end via Django test client

Acceptance Criteria:
  AC-1  System Admin fills name + type + quantity → saved with state 'Unassigned'
  AC-2  Duplicate name → rejected with clear error message
"""

import pytest
from django.urls import reverse

from CSSD_Management_System.models import CustomUser, InstrumentSet, InventoryItem
from CSSD_Management_System.forms import InstrumentSetForm


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_user(
        email='admin@test.com',
        password='AdminPass1!',
        role='System Administrator',
        department='CSSD',
    )


@pytest.fixture
def cssd_user(db):
    return CustomUser.objects.create_user(
        email='cssd@test.com',
        password='CssdPass1!',
        role='CSSD Technician',
        department='CSSD',
    )


@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email='nurse@test.com',
        password='NursePass1!',
        role='Department Nurse',
        department='ICU',
    )


@pytest.fixture
def existing_set(db):
    """An instrument set already in the DB — used for duplicate tests."""
    return InstrumentSet.objects.create(
        name='Major Surgical Set',
        type='General',
        quantity=5,
        state='Unassigned',
    )


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests — InstrumentSetForm
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestInstrumentSetForm:

    def test_valid_form_saves_with_unassigned_state(self):
        """AC-1: Valid data produces a valid form and the saved object has state='Unassigned'."""
        form = InstrumentSetForm(data={
            'name': 'Ortho Drill Set',
            'type': 'Orthopedic',
            'quantity': 3,
        })
        assert form.is_valid(), form.errors
        instrument_set = form.save()
        assert instrument_set.pk is not None
        assert instrument_set.state == 'Unassigned'

    def test_name_field_required(self):
        """Form is invalid when name is missing."""
        form = InstrumentSetForm(data={'name': '', 'type': 'General', 'quantity': 2})
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_type_field_required(self):
        """Form is invalid when type is blank/unselected."""
        form = InstrumentSetForm(data={'name': 'Eye Kit', 'type': '', 'quantity': 2})
        assert not form.is_valid()
        assert 'type' in form.errors

    def test_quantity_field_required(self):
        """Form is invalid when quantity is missing."""
        form = InstrumentSetForm(data={'name': 'Forceps Set', 'type': 'General', 'quantity': ''})
        assert not form.is_valid()
        assert 'quantity' in form.errors

    def test_quantity_must_be_at_least_one(self):
        """Form rejects quantity = 0."""
        form = InstrumentSetForm(data={'name': 'Clamp Set', 'type': 'General', 'quantity': 0})
        assert not form.is_valid()
        assert 'quantity' in form.errors

    def test_duplicate_name_exact_match_rejected(self, existing_set):
        """AC-2: Exact duplicate name raises ValidationError."""
        form = InstrumentSetForm(data={
            'name': 'Major Surgical Set',   # same as existing_set
            'type': 'General',
            'quantity': 2,
        })
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'already exists' in form.errors['name'][0]

    def test_duplicate_name_case_insensitive_rejected(self, existing_set):
        """AC-2: Case-insensitive duplicate (different case) is also rejected."""
        form = InstrumentSetForm(data={
            'name': 'MAJOR SURGICAL SET',   # different case, same name
            'type': 'General',
            'quantity': 2,
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_unique_name_passes(self, existing_set):
        """A genuinely different name should pass validation."""
        form = InstrumentSetForm(data={
            'name': 'Minor Surgical Set',
            'type': 'General',
            'quantity': 2,
        })
        assert form.is_valid(), form.errors

    def test_all_type_choices_are_valid(self):
        """Every type listed in the form's choices should be accepted."""
        valid_types = ['General', 'Orthopedic', 'Cardiac', 'Neurology',
                       'ENT', 'Ophthalmic', 'Gynaecology', 'Other']
        for i, type_val in enumerate(valid_types):
            form = InstrumentSetForm(data={
                'name': f'Test Set {i}',
                'type': type_val,
                'quantity': 1,
            })
            assert form.is_valid(), f"Type '{type_val}' should be valid. Errors: {form.errors}"


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests — View (end-to-end via test client)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAdminRegisterInstrumentSetView:

    REGISTER_URL = '/admin/instrument-sets/register/'
    LIST_URL     = '/admin/instrument-sets/'

    # ── Access control ────────────────────────────────────────────────────────

    def test_unauthenticated_redirected_to_login(self, client):
        response = client.get(self.REGISTER_URL)
        assert response.status_code in (302, 301)
        assert 'login' in response.url.lower() or response.status_code == 302

    def test_nurse_forbidden(self, client, nurse_user):
        client.login(email='nurse@test.com', password='NursePass1!')
        response = client.get(self.REGISTER_URL)
        assert response.status_code == 403

    def test_cssd_tech_forbidden(self, client, cssd_user):
        """Only System Administrator can register instrument sets."""
        client.login(email='cssd@test.com', password='CssdPass1!')
        response = client.get(self.REGISTER_URL)
        assert response.status_code == 403

    def test_admin_can_access_register_form(self, client, admin_user):
        client.login(email='admin@test.com', password='AdminPass1!')
        response = client.get(self.REGISTER_URL)
        assert response.status_code == 200

    def test_admin_can_access_list_page(self, client, admin_user):
        client.login(email='admin@test.com', password='AdminPass1!')
        response = client.get(self.LIST_URL)
        assert response.status_code == 200

    def test_admin_dashboard_shows_instrument_sets_button(self, client, admin_user):
        """Admin dashboard exposes an entry point to the PROJ-14 flow."""
        client.login(email='admin@test.com', password='AdminPass1!')
        response = client.get(reverse('dashboard_router'))
        content = response.content.decode()
        assert response.status_code == 200
        assert 'Instrument Sets' in content
        assert self.LIST_URL in content

    def test_cssd_tech_dashboard_does_not_show_instrument_sets_button(self, client, cssd_user):
        """Only System Administrators should see the admin instrument-set button."""
        client.login(email='cssd@test.com', password='CssdPass1!')
        response = client.get(reverse('dashboard_router'))
        content = response.content.decode()
        assert response.status_code == 200
        assert 'Instrument Sets' not in content

    # ── AC-1: Successful registration ────────────────────────────────────────

    def test_ac1_valid_submission_creates_set(self, client, admin_user):
        """AC-1: POST with valid data → InstrumentSet saved in DB."""
        client.login(email='admin@test.com', password='AdminPass1!')
        response = client.post(self.REGISTER_URL, {
            'name': 'Cardiac Bypass Set',
            'type': 'Cardiac',
            'quantity': 4,
        })
        assert InstrumentSet.objects.filter(name='Cardiac Bypass Set').exists()

    def test_ac1_new_set_state_is_unassigned(self, client, admin_user):
        """AC-1: Newly registered set always has state='Unassigned'."""
        client.login(email='admin@test.com', password='AdminPass1!')
        client.post(self.REGISTER_URL, {
            'name': 'ENT Micro Set',
            'type': 'ENT',
            'quantity': 2,
        })
        iset = InstrumentSet.objects.get(name='ENT Micro Set')
        assert iset.state == 'Unassigned'

    def test_ac1_saved_quantity_matches_input(self, client, admin_user):
        """AC-1: Quantity submitted is exactly what gets saved."""
        client.login(email='admin@test.com', password='AdminPass1!')
        client.post(self.REGISTER_URL, {
            'name': 'Neuro Retractor Set',
            'type': 'Neurology',
            'quantity': 7,
        })
        iset = InstrumentSet.objects.get(name='Neuro Retractor Set')
        assert iset.quantity == 7

    def test_ac1_successful_post_redirects_to_list(self, client, admin_user):
        """AC-1: After saving, admin is redirected to the instrument set list."""
        client.login(email='admin@test.com', password='AdminPass1!')
        response = client.post(self.REGISTER_URL, {
            'name': 'Ophthalmic Phaco Set',
            'type': 'Ophthalmic',
            'quantity': 3,
        })
        assert response.status_code == 302
        assert response.url == self.LIST_URL

    def test_ac1_set_visible_on_list_page(self, client, admin_user):
        """AC-1: Newly registered set appears in the list page."""
        client.login(email='admin@test.com', password='AdminPass1!')
        client.post(self.REGISTER_URL, {
            'name': 'Gynaecology Set A',
            'type': 'Gynaecology',
            'quantity': 6,
        })
        response = client.get(self.LIST_URL)
        assert 'Gynaecology Set A' in response.content.decode()

    def test_ac1_registered_set_creates_inventory_stock(self, client, admin_user):
        """Registered sets feed the inventory stock used by downstream workflows."""
        client.login(email='admin@test.com', password='AdminPass1!')
        client.post(self.REGISTER_URL, {
            'name': 'Trauma Response Set',
            'type': 'General',
            'quantity': 5,
        })

        inventory_item = InventoryItem.objects.get(name='Trauma Response Set')
        assert inventory_item.category == 'General'
        assert inventory_item.current_stock == 5
        assert inventory_item.min_threshold == 3

    def test_ac1_registered_set_appears_on_nurse_request_page(self, client, admin_user, nurse_user):
        """A set registered by admin is selectable by nurses for US-05 requests."""
        client.login(email='admin@test.com', password='AdminPass1!')
        client.post(self.REGISTER_URL, {
            'name': 'Neonatal Surgery Set',
            'type': 'General',
            'quantity': 4,
        })
        client.logout()

        client.login(email='nurse@test.com', password='NursePass1!')
        response = client.get(reverse('nurse_create_request'))
        content = response.content.decode()

        assert response.status_code == 200
        assert 'Neonatal Surgery Set' in content
        assert 'Available (4)' in content

    # ── AC-2: Duplicate name rejection ───────────────────────────────────────

    def test_ac2_duplicate_name_rejected(self, client, admin_user, existing_set):
        """AC-2: Submitting an existing name returns 200 (form shown again) — not saved."""
        client.login(email='admin@test.com', password='AdminPass1!')
        count_before = InstrumentSet.objects.count()
        response = client.post(self.REGISTER_URL, {
            'name': 'Major Surgical Set',  # duplicate
            'type': 'General',
            'quantity': 2,
        })
        assert response.status_code == 200   # re-renders form with error
        assert InstrumentSet.objects.count() == count_before  # no new record

    def test_ac2_error_message_shown_in_response(self, client, admin_user, existing_set):
        """AC-2: The duplicate error message is visible in the returned HTML."""
        client.login(email='admin@test.com', password='AdminPass1!')
        response = client.post(self.REGISTER_URL, {
            'name': 'Major Surgical Set',
            'type': 'General',
            'quantity': 2,
        })
        content = response.content.decode()
        assert 'already exists' in content

    def test_ac2_case_insensitive_duplicate_rejected(self, client, admin_user, existing_set):
        """AC-2: Same name in different case is also rejected (case-insensitive)."""
        client.login(email='admin@test.com', password='AdminPass1!')
        count_before = InstrumentSet.objects.count()
        client.post(self.REGISTER_URL, {
            'name': 'major surgical set',  # lower-case duplicate
            'type': 'General',
            'quantity': 1,
        })
        assert InstrumentSet.objects.count() == count_before

    def test_ac2_different_name_after_duplicate_succeeds(self, client, admin_user, existing_set):
        """After a duplicate rejection, submitting a unique name works."""
        client.login(email='admin@test.com', password='AdminPass1!')
        client.post(self.REGISTER_URL, {
            'name': 'Major Surgical Set',  # duplicate — rejected
            'type': 'General',
            'quantity': 2,
        })
        # Now submit a unique name
        response = client.post(self.REGISTER_URL, {
            'name': 'Minor Surgical Set',
            'type': 'General',
            'quantity': 2,
        })
        assert response.status_code == 302  # redirect = success
        assert InstrumentSet.objects.filter(name='Minor Surgical Set').exists()
