# Evidence of Testing

Date: 2026-04-26
Project: CSSD Management System
Tester: Codex

## Test Type

Automated backend testing using Django's built-in test runner.

## Command Used

```powershell
cd CSSD_Management_System
python manage.py test
```

## Test Log Evidence

```text
Found 17 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................
----------------------------------------------------------------------
Ran 17 tests in 29.601s

OK
Destroying test database for alias 'default'...
```

## Interpretation

- `Found 17 test(s)` means Django discovered 17 automated tests.
- `System check identified no issues` means there were no Django configuration or model warnings at test time.
- The 17 dots mean all 17 tests passed.
- `OK` confirms there were no failures or errors.

## Covered Areas

- login flow
- dashboard routing
- role restriction decorator
- instrument request submission
- sterile stock view
- CSSD state transitions
- dashboard counters
- ETA display
- bug regression cases for request validation and stock handling

## How Bugs Were Caught

The sample bugs in [BUG_REPORT.md](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/BUG_REPORT.md) were identified using a mix of source-code review, route inspection, and live behavior checks.

### Method Used

1. Read the Django views, models, templates, and URL configuration to understand the expected flow.
2. Compare links in templates against actual routes in `urls.py`.
3. Review authorization checks in views to see whether role restrictions were enforced.
4. Inspect form-handling logic for missing validation and unsafe stock updates.
5. Run `python manage.py test` and use failing/passing tests to confirm behavior.
6. Reproduce visible issues through the browser where possible, such as missing pages and portal-routing behavior.

### Bug Discovery Notes

- `BUG-001` was caught by inspecting the CSSD transition views and noticing they use `@login_required` without checking that the user is CSSD staff.
- `BUG-002` was caught by inspecting `cssd_request_details` and seeing that any logged-in user can open the page without an ownership or role check.
- `BUG-003` was caught by reviewing `mark_delivered` and noticing it checks department only, not whether the user is actually a nurse.
- `BUG-004` was caught by reviewing request submission validation and seeing that negative quantities are never blocked before stock is updated.
- `BUG-005` was caught by inspecting the `InventoryItem` model and seeing that a `status` field and a `status` property use the same name.
- `BUG-006` was caught by manually testing login behavior and observing that a nurse account can authenticate through the CSSD staff login page and still enter the system.

### Manual Reproduction Evidence

- The shortage-alert 404 bug was reproduced by clicking the `Shortage Alerts` card in the CSSD dashboard and observing that `/cssd_inventory_alerts/` had no matching route.
- The portal mismatch bug was reproduced by entering nurse credentials into the CSSD login page and observing that the user was authenticated and redirected to the nurse dashboard.
- Request IDs for testing were obtained by creating a nurse request through `/nurse_create_request/` and then reading the numeric ID from the request detail URL.

## Related Files

- [tests.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/CSSD_Management_System/tests.py)
- [state_machine/tests.py](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/CSSD_Management_System/state_machine/tests.py)
- [BUG_REPORT.md](c:/Users/SPEED/Documents/GitHub/CSSD_Management_System/BUG_REPORT.md)

## Optional Screenshot Evidence

If your instructor wants screenshots, capture:

1. the terminal before running `python manage.py test`
2. the terminal showing the final `OK`
3. the project files showing the test files and bug report
