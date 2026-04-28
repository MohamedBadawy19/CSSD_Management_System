# Bug Report

Date: 2026-04-26
Project: CSSD Management System
Reviewer: Codex

## Summary

This report lists sample bugs found by code inspection in the current Django app. They are ordered by severity and include file references, reproduction steps, expected behavior, and actual behavior.

## BUG-001

Title: Any logged-in user can change CSSD processing states

Severity: Critical

Priority: High

Location: [views_us07_10.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views_us07_10.py:57), [views_us07_10.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views_us07_10.py:101), [views_us07_10.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views_us07_10.py:139), [views_us07_10.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views_us07_10.py:181)

Preconditions: A user is authenticated. A request exists in a state that allows transition.

Steps to Reproduce:
1. Log in as a `Department Nurse`.
2. Send a POST request to `mark_collected`, `mark_cleaned`, `mark_sterilized`, or `mark_packed`.
3. Use a request ID that matches the required previous state.

Expected Result:
Only CSSD staff should be able to perform processing transitions.

Actual Result:
The endpoints only use `@login_required`, so any authenticated user can trigger the transitions.

Impact:
Nurses can move requests through internal CSSD workflow stages without authorization, which breaks role-based access control and audit trust.

## BUG-002

Title: Any logged-in user can view CSSD request detail page for any request

Severity: High

Priority: High

Location: [views_us07_10.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views_us07_10.py:218)

Preconditions: A user is authenticated. Another user's request ID is known or guessed.

Steps to Reproduce:
1. Log in as a nurse.
2. Open `/cssd_request_details/<request_id>/` for a request you do not own.

Expected Result:
Only authorized CSSD staff, or possibly the owning user if intended, should be able to open the request detail page.

Actual Result:
The view fetches the request and renders it for any logged-in user without checking role or ownership.

Impact:
Unauthorized users can inspect other departments' request data.

## BUG-003

Title: Delivered status can be confirmed by non-nurse users

Severity: High

Priority: Medium

Location: [views.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views.py:209)

Preconditions: A packed request exists. A non-nurse authenticated user has a matching department value or blank department compatible with the request.

Steps to Reproduce:
1. Log in as a non-nurse user.
2. POST to `/requests/<request_id>/deliver/`.
3. Use a request whose department matches the user's department value.

Expected Result:
Only the receiving department nurse should be allowed to confirm delivery.

Actual Result:
The code checks only `request.user.department`, not the user's role.

Impact:
Delivery confirmation can be forged by the wrong class of user, which corrupts request lifecycle accuracy.

## BUG-004

Title: Negative quantity request increases stock instead of consuming stock

Severity: Critical

Priority: High

Location: [views.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views.py:162), [views.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views.py:189)

Preconditions: A nurse is logged in and an inventory item exists.

Steps to Reproduce:
1. Log in as a nurse.
2. Submit `save_instrument_request` with a negative quantity such as `-3`.
3. Inspect the request item and inventory stock afterward.

Expected Result:
The system should reject zero or negative quantities as invalid input.

Actual Result:
The only validation is `quantity > current_stock`. A negative quantity passes validation, creates a request item, and then `current_stock -= quantity` increases stock.

Impact:
Inventory can be artificially inflated and request records can contain impossible negative quantities.

## BUG-005

Title: InventoryItem status field is overwritten by a property with the same name

Severity: Medium

Priority: Medium

Location: [models.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/models.py:86), [models.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/models.py:92)

Preconditions: Any code path that reads or writes `InventoryItem.status`.

Steps to Reproduce:
1. Inspect the `InventoryItem` model.
2. Note that a `status` database field is declared.
3. Note that a `@property def status(...)` is declared with the same name.

Expected Result:
The model should have either a stored field named `status` or a computed property with a different name.

Actual Result:
The property shadows the model field at the Python level.

Impact:
Persisted status values are effectively hidden, assignments become confusing or broken, and future admin/forms/filter behavior may not match database state.

## BUG-006

Title: Nurse account can log in through the CSSD staff login page

Severity: Medium

Priority: Medium

Location: [views.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views.py:16), [views.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views.py:24), [views.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/views.py:48)

Preconditions: A valid nurse account exists with working credentials.

Steps to Reproduce:
1. Open the CSSD staff login page.
2. Enter a valid nurse email and password.
3. Submit the form.

Expected Result:
The staff login page should reject non-staff users or show a message that the portal is only for CSSD staff and admins.

Actual Result:
The nurse is authenticated successfully and then redirected into the nurse dashboard based on role.

Impact:
The login portal does not enforce role separation. Users can authenticate through the wrong portal, which is confusing and weakens access-control expectations.

## Notes

- These bugs were identified from the current source code and project behavior patterns.
- The automated test suite currently passes, but these cases are not fully covered by tests yet.
- The most important next additions would be regression tests for authorization on the state-transition and delivery-confirmation endpoints, plus validation tests for non-positive quantities.
