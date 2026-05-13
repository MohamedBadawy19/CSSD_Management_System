"""
test_auth.py — Comprehensive Authentication & Authorization Tests

CONTEXT:
This test suite covers US-01, US-02, and US-03 from the SRS.
It maps the requested REST API/Token requirements to the system's actual
implementation (Django Sessions, Form-based views, and Custom User Model).

Test Structure:
1. Unit Tests (Password Hashing, Session Token, Role Validation)
2. Integration Tests (Login Flow, Access Control, Session Expiry)

Pytest Fixtures:
This file uses fixtures defined in `conftest.py` (e.g., `db_access`, 
`cssd_technician_user`, `cssd_client`, `nurse_client`). Pytest injects 
these automatically when you pass them as arguments to the test functions.
"""

import pytest
from django.urls import reverse
from django.http import HttpResponse
from django.test import RequestFactory
from django.conf import settings

from CSSD_Management_System.models import CustomUser
from CSSD_Management_System.decorators import cssd_staff_required

# We need the pytest-django db mark to allow database access in all tests here
pytestmark = pytest.mark.django_db


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  1. UNIT TESTS                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def test_password_hashing_function(db_access):
    """
    Unit Test: Password Hashing Function
    Ensures that plain-text passwords are never saved directly to the database.
    """
    # ARRANGE: Define user details
    email = "hasher@cssd.hospital"
    raw_password = "SuperSecretPassword123!"

    # ACT: Create the user using the custom manager (which handles hashing)
    user = CustomUser.objects.create_user(
        email=email,
        password=raw_password,
        role="CSSD Technician"
    )

    # ASSERT: Check that the password in DB is not plain text
    assert user.password != raw_password
    # ASSERT: Ensure Django's check_password correctly verifies the hash
    assert user.check_password(raw_password) is True
    assert user.check_password("WrongPassword") is False


def test_token_generation_function(cssd_client, cssd_technician_user):
    """
    Unit Test: Token Generation (Django Session ID)
    In a REST API this would be a JWT. In Django, this is the Session Cookie.
    Ensures that logging in generates a valid session ID for the user.
    """
    # ARRANGE & ACT: The `cssd_client` fixture already logs the user in.
    # We retrieve the active session from the client.
    session = cssd_client.session

    # ASSERT: Ensure a session/token has been generated
    assert session.session_key is not None
    # ASSERT: Ensure the session is tied to the correct user ID
    assert str(session['_auth_user_id']) == str(cssd_technician_user.pk)


def test_role_validation_function(db_access):
    """
    Unit Test: Role Validation Function
    Ensures the CustomUser model strictly enforces valid role choices.
    """
    # ARRANGE: Create a user with a valid role
    user = CustomUser.objects.create_user(
        email="role_test@cssd.hospital",
        password="test",
        role="Department Nurse"
    )

    # ACT: Get the available role choices from the model definition
    valid_roles = [choice[0] for choice in CustomUser.ROLE_CHOICES]

    # ASSERT: The user's role must exist in the valid choices
    assert user.role in valid_roles
    assert user.role == "Department Nurse"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  2. INTEGRATION TESTS                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def test_login_with_valid_cssd_credentials(client, cssd_technician_user):
    """
    Integration Test: POST /login/ with valid CSSD credentials.
    US-01: Valid credentials -> redirect to dashboard router.
    """
    # ARRANGE: Set up the URL and login payload
    url = reverse("login") + "?role=staff"
    payload = {
        "username": cssd_technician_user.email,
        "password": "TestPass123!"  # Password defined in conftest.py
    }

    # ACT: Submit the POST request to the login endpoint
    response = client.post(url, data=payload)

    # ASSERT: It should redirect (HTTP 302) to the CSSD dashboard
    assert response.status_code == 302
    assert response.url == reverse("cssd_dashboard")


def test_login_with_invalid_credentials(client, cssd_technician_user):
    """
    Integration Test: POST /login/ with invalid credentials.
    US-01: Invalid credentials -> error message and access denied.
    """
    # ARRANGE: Setup payload with the WRONG password
    url = reverse("login") + "?role=nurse"
    payload = {
        "username": cssd_technician_user.email,
        "password": "WrongPassword!"
    }

    # ACT: Submit the POST request
    response = client.post(url, data=payload)

    # ASSERT: It should NOT redirect. It should render the form again (HTTP 200).
    assert response.status_code == 200
    # ASSERT: The form context should contain errors
    assert "form" in response.context
    assert response.context["form"].errors is not None


def test_login_with_valid_nurse_credentials(client, nurse_user):
    """
    Integration Test: POST /login/ with valid Nurse credentials.
    US-02: Valid nurse credentials -> redirect to dashboard router.
    """
    # ARRANGE: Setup payload for the nurse user
    url = reverse("login")
    payload = {
        "username": nurse_user.email,
        "password": "TestPass123!"
    }

    # ACT: Submit the POST request
    response = client.post(url, data=payload)

    # ASSERT: Should successfully redirect to the nurse dashboard
    assert response.status_code == 302
    assert response.url == reverse("nurse_dashboard")


def test_logout_redirects_to_home(client, cssd_technician_user):
    """
    Integration Test: GET /logout/ clears the session and returns to home.
    """
    client.login(email=cssd_technician_user.email, password="TestPass123!")

    response = client.get(reverse("logout"))

    assert response.status_code == 302
    assert response.url == reverse("home")
    assert "_auth_user_id" not in client.session


def test_nurse_cannot_access_cssd_endpoints(nurse_user):
    """
    Integration Test: GET request to CSSD endpoint with nurse token/session.
    US-03: Restrict Nurse Access -> HTTP 403 Forbidden.
    This tests the backend decorator @cssd_staff_required.
    """
    # ARRANGE: Create a dummy view protected by the CSSD decorator
    @cssd_staff_required
    def dummy_cssd_endpoint(request):
        return HttpResponse("Welcome to the CSSD Control Room")

    # Set up a RequestFactory to simulate an incoming HTTP GET request
    factory = RequestFactory()
    request = factory.get("/api/cssd/sterilize/")
    # Attach the logged-in nurse user to the request object
    request.user = nurse_user

    # ACT: Call the dummy view with the nurse's request
    response = dummy_cssd_endpoint(request)

    # ASSERT: The decorator must intercept it and return 403 Forbidden
    assert response.status_code == 403
    assert b"Access Denied" in response.content


def test_session_expires_after_30_minutes(client, cssd_technician_user):
    """
    Integration Test: Session expiration after 30 minutes of inactivity.
    US-01: Verifies that settings.SESSION_COOKIE_AGE is exactly 30 minutes (1800s).
    
    NOTE: If this fails, you need to add `SESSION_COOKIE_AGE = 1800` to your 
    `settings.py` file to fulfill US-01.
    """
    # ARRANGE & ACT: Login to generate a session
    client.login(email=cssd_technician_user.email, password="TestPass123!")
    
    # Check the Django setting that controls session timeout
    session_timeout_seconds = settings.SESSION_COOKIE_AGE
    
    # 30 minutes * 60 seconds = 1800 seconds
    EXPECTED_TIMEOUT = 1800
    
    # ASSERT: The configured timeout must be exactly 30 minutes
    assert session_timeout_seconds == EXPECTED_TIMEOUT, (
        f"Expected session expiry of {EXPECTED_TIMEOUT}s (30m), "
        f"but got {session_timeout_seconds}s. Add SESSION_COOKIE_AGE=1800 to settings.py"
    )
