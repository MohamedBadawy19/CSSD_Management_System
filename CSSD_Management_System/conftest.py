"""
conftest.py — Shared pytest fixtures for the CSSD Management System.

Fixtures defined here are automatically available to every test file
under this directory tree without any explicit import.

Naming convention
-----------------
- ``db_*``   → database-level helpers (transactions, migrations)
- ``*_user`` → pre-built users with a specific role
- ``*_client`` → Django test clients already logged in as that user
- ``sample_*`` → domain objects (instruments, batches, etc.)
"""

import pytest
from django.test import Client
from CSSD_Management_System.models import (
    CustomUser,
    InstrumentSet,
    SterilizationBatch,
    InventoryItem,
    InstrumentRequest,
    RequestItem,
)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  1. DATABASE FIXTURES                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


@pytest.fixture
def db_access(db):
    """
    Grants test-level access to the real (test) database.

    WHY: pytest-django blocks all DB access by default to keep unit tests
    fast and side-effect-free.  Any test that needs to create / query
    models must request this fixture (or use ``@pytest.mark.django_db``).
    This fixture wraps Django's built-in ``db`` fixture so we can extend
    it later (e.g. seed reference data) without touching every test.
    """
    pass  # The ``db`` dependency is all we need; the body is intentionally empty.


@pytest.fixture
def transactional_db_access(transactional_db):
    """
    Like ``db_access`` but each test runs in its own *transaction* that is
    rolled back at the end.

    WHY: Some tests (e.g. concurrent request handling, signals that
    commit) need real transaction semantics rather than the default
    ``SAVEPOINT`` wrapper.  This fixture pays a small speed penalty but
    avoids false-positive passes that hide transaction-related bugs.
    """
    pass


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  2. USER / AUTHENTICATION FIXTURES                                          ║
# ║                                                                              ║
# ║  One fixture per role defined in CustomUser.ROLE_CHOICES:                    ║
# ║    • System Administrator  →  admin_user                                     ║
# ║    • CSSD Technician       →  cssd_technician_user                           ║
# ║    • Department Nurse      →  nurse_user                                     ║
# ║    • Hospital Administrator →  hospital_admin_user                           ║
# ║                                                                              ║
# ║  Each user fixture also has a matching ``*_client`` fixture that             ║
# ║  returns a Django test ``Client`` already logged-in as that user.            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── Shared password for all test users ──────────────────────────────────────
TEST_PASSWORD = "TestPass123!"


@pytest.fixture
def admin_user(db):
    """
    Creates a **System Administrator** user.

    WHY: The admin can manage users, view all dashboards, and access the
    Django admin panel.  Tests for user-management endpoints and
    role-gating need an admin user to verify that privileged actions are
    allowed.
    """
    return CustomUser.objects.create_user(
        email="admin@cssd.hospital",
        password=TEST_PASSWORD,
        first_name="Admin",
        last_name="User",
        role="System Administrator",
        department="IT",
        is_staff=True,
    )


@pytest.fixture
def admin_client(admin_user):
    """
    Returns a Django test ``Client`` already authenticated as the admin.

    WHY: Saves repeating ``client.login(…)`` boilerplate in every admin
    test.  Just inject ``admin_client`` and start making requests.
    """
    client = Client()
    client.login(email=admin_user.email, password=TEST_PASSWORD)
    return client


@pytest.fixture
def cssd_technician_user(db):
    """
    Creates a **CSSD Technician** user.

    WHY: Technicians perform the core workflow — collecting, cleaning,
    sterilising, and packing instrument sets.  Most state-transition
    tests and batch-processing tests need this role.
    """
    return CustomUser.objects.create_user(
        email="tech@cssd.hospital",
        password=TEST_PASSWORD,
        first_name="CSSD",
        last_name="Technician",
        role="CSSD Technician",
        department="CSSD",
    )


@pytest.fixture
def cssd_client(cssd_technician_user):
    """
    Returns a Django test ``Client`` already authenticated as a CSSD
    Technician.
    """
    client = Client()
    client.login(email=cssd_technician_user.email, password=TEST_PASSWORD)
    return client


@pytest.fixture
def nurse_user(db):
    """
    Creates a **Department Nurse** user.

    WHY: Nurses submit instrument requests and track their status.
    Tests for the request-submission form, the nurse dashboard, and
    notification delivery all require a nurse user.
    """
    return CustomUser.objects.create_user(
        email="nurse@cssd.hospital",
        password=TEST_PASSWORD,
        first_name="Jane",
        last_name="Nurse",
        role="Department Nurse",
        department="Emergency",
    )


@pytest.fixture
def nurse_client(nurse_user):
    """
    Returns a Django test ``Client`` already authenticated as a nurse.
    """
    client = Client()
    client.login(email=nurse_user.email, password=TEST_PASSWORD)
    return client


@pytest.fixture
def hospital_admin_user(db):
    """
    Creates a **Hospital Administrator** user.

    WHY: Hospital admins view reports and analytics dashboards but
    cannot perform CSSD operations.  Access-control tests need this role
    to verify they see the correct dashboard and *cannot* trigger
    technician-only actions.
    """
    return CustomUser.objects.create_user(
        email="hadmin@cssd.hospital",
        password=TEST_PASSWORD,
        first_name="Hospital",
        last_name="Admin",
        role="Hospital Administrator",
        department="Administration",
    )


@pytest.fixture
def hospital_admin_client(hospital_admin_user):
    """
    Returns a Django test ``Client`` authenticated as a Hospital
    Administrator.
    """
    client = Client()
    client.login(email=hospital_admin_user.email, password=TEST_PASSWORD)
    return client


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  3. INSTRUMENT SET FIXTURES                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


@pytest.fixture
def sample_instrument_set(db):
    """
    Creates a single InstrumentSet in the default ``Unassigned`` state.

    WHY: The most common starting point for state-machine tests.  A
    freshly created set should be unassigned and ready to be included in
    a new request.
    """
    return InstrumentSet.objects.create(
        name="General Surgery Kit",
        type="Surgical",
        quantity=15,
    )


@pytest.fixture
def sample_instrument_sets(db):
    """
    Creates a *collection* of instrument sets in various states.

    WHY: Dashboard and filtering tests need multiple sets across
    different lifecycle stages so we can verify correct grouping,
    counts, and badge colours.

    Returns a dict keyed by state for easy assertion:
        sets = sample_instrument_sets
        assert sets["Sterilized"].state == "Sterilized"
    """
    sets = {}
    data = [
        ("Cardiac Surgery Kit", "Surgical", 12, "Unassigned"),
        ("Ortho Drill Set", "Orthopaedic", 8, "Requested"),
        ("Endoscopy Kit", "Endoscopy", 5, "Collected"),
        ("Neuro Micro Set", "Neurosurgery", 20, "Cleaned"),
        ("Laparoscopy Kit", "Surgical", 10, "Sterilized"),
        ("Dental Extraction Kit", "Dental", 6, "Packed"),
        ("Eye Surgery Kit", "Ophthalmic", 9, "Delivered"),
    ]
    for name, type_, qty, state in data:
        sets[state] = InstrumentSet.objects.create(
            name=name,
            type=type_,
            quantity=qty,
            state=state,
        )
    return sets


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  4. STERILIZATION BATCH FIXTURES                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


@pytest.fixture
def sample_batch(db, cssd_technician_user):
    """
    Creates a single SterilizationBatch in ``In Progress`` status,
    operated by the CSSD technician.

    WHY: Batch tests (adding instruments, completing a cycle, verifying
    temperature/duration) need at least one batch to work with.  Tying
    it to ``cssd_technician_user`` mirrors the real workflow where only
    technicians operate autoclaves.
    """
    return SterilizationBatch.objects.create(
        operator=cssd_technician_user,
        temperature=134.0,
        cycle_duration=18.0,
        status="In Progress",
    )


@pytest.fixture
def completed_batch(db, cssd_technician_user):
    """
    Creates a SterilizationBatch that has already been marked
    ``Completed``.

    WHY: Tests that verify post-sterilisation logic (packing, delivery,
    audit trail) need a batch whose cycle is finished.
    """
    return SterilizationBatch.objects.create(
        operator=cssd_technician_user,
        temperature=134.0,
        cycle_duration=18.0,
        status="Completed",
    )


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  5. INVENTORY & REQUEST FIXTURES                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


@pytest.fixture
def sample_inventory_items(db):
    """
    Creates a set of InventoryItems with varying stock levels.

    WHY: Inventory-status tests need items that trigger every branch of
    the ``InventoryItem.status`` property — 'Available', 'Limited', and
    'Out of Stock'.
    """
    return {
        "available": InventoryItem.objects.create(
            name="Surgical Scalpel",
            category="Cutting",
            current_stock=50,
            min_threshold=10,
        ),
        "limited": InventoryItem.objects.create(
            name="Forceps",
            category="Grasping",
            current_stock=5,
            min_threshold=10,
        ),
        "out_of_stock": InventoryItem.objects.create(
            name="Suture Needle",
            category="Suturing",
            current_stock=0,
            min_threshold=10,
        ),
    }


@pytest.fixture
def sample_request(db, nurse_user, sample_inventory_items):
    """
    Creates an InstrumentRequest submitted by the nurse, with two line
    items from the sample inventory.

    WHY: End-to-end workflow tests need a fully formed request (header +
    line items) to drive through Collected → Cleaned → … → Delivered.
    """
    req = InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Requested",
        department=nurse_user.department,
        notes="Needed for morning OR schedule",
    )
    # Attach two line items
    RequestItem.objects.create(
        request=req,
        inventory_item=sample_inventory_items["available"],
        quantity=2,
    )
    RequestItem.objects.create(
        request=req,
        inventory_item=sample_inventory_items["limited"],
        quantity=1,
    )
    return req


@pytest.fixture
def urgent_request(db, nurse_user, sample_inventory_items):
    """
    Creates an *urgent* InstrumentRequest.

    WHY: Priority-handling tests need both Normal and Urgent requests to
    verify that urgent ones surface first in the CSSD queue.
    """
    req = InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Urgent",
        status="Requested",
        department=nurse_user.department,
        notes="STAT — trauma case incoming",
    )
    RequestItem.objects.create(
        request=req,
        inventory_item=sample_inventory_items["available"],
        quantity=5,
    )
    return req
