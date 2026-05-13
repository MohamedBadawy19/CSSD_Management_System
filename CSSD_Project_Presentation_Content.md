# CSSD Management System - Presentation Content

Sources used:
- `C:\Users\rowid\Downloads\swe\CSSD_Release_Plan_Final.docx`
- `C:\Users\rowid\Downloads\swe\Testing_doc_team5.pdf`

---

## Slide 1: Title

**CSSD Management System**  
Central Sterile Services Department Workflow Management Platform

**Subtitle:**  
A role-based hospital workflow system for managing surgical instrument requests, sterilization stages, inventory alerts, reports, and audit history.

**Presenter/team:** Team 5  
**Course:** Software Engineering

**Screenshot to add:** Home page or login selection page.

---

## Slide 2: Idea & Problem Statement

Hospitals need a reliable way to track surgical instruments from request to delivery.

**Problem:**
- Instrument requests are often difficult to track manually.
- Nurses need visibility into request status.
- CSSD staff need a structured workflow for processing instruments.
- Hospital administrators need reports and audit visibility.
- Manual communication can cause delays, missing updates, and unclear responsibility.

**Project idea:**  
Build a digital CSSD workflow system that connects nurses, CSSD technicians, and hospital administrators in one platform.

---

## Slide 3: Project Objectives

The project aims to:
- Digitize the full instrument lifecycle.
- Support separate dashboards for each user role.
- Enforce role-based access control.
- Track every request through defined processing stages.
- Provide inventory shortage alerts.
- Notify nurses when request status changes.
- Give hospital administrators reporting and audit tools.
- Deliver a stable academic prototype by the end of the semester.

**Screenshot to add:** Dashboard overview.

---

## Slide 4: Main Requirements

**Functional requirements:**
- Nurse login and CSSD staff login.
- Nurse can submit instrument requests.
- CSSD technician can process requests through lifecycle stages.
- System tracks statuses: Requested, Collected, Cleaned, Sterilized, Packed, Delivered.
- CSSD staff can create sterilization batches and assign operators.
- Inventory items show available, limited, or out-of-stock status.
- Nurses receive in-app notifications.
- Hospital admin can view daily reports and audit history.

**Non-functional requirements:**
- Secure role separation.
- Reliable database updates.
- Clear UI for hospital workflow.
- No HTTP 500 errors during expected use.
- Testable and maintainable Django codebase.

---

## Slide 5: Users & Roles

**Department Nurse:**
- Creates instrument requests.
- Tracks request status.
- Views notifications.
- Confirms delivery.

**CSSD Technician:**
- Views pending and active requests.
- Updates sterilization stages.
- Creates sterilization batches.
- Handles inventory shortage alerts.

**Hospital Administrator:**
- Views daily sterilization reports.
- Searches audit history.
- Reviews request lifecycle records.

**System Administrator:**
- Has system-level access and admin control.

**Screenshot to add:** Nurse login, staff login, or role-based dashboard.

---

## Slide 6: Design & Architecture

**Architecture:**
- Backend: Django web framework.
- Database: SQLite for development and academic prototype.
- Frontend: Django templates, HTML, CSS, JavaScript.
- Authentication: Custom user model using email login.
- Access control: Role-based decorators and dashboard routing.

**Main modules:**
- Authentication and role routing.
- Instrument request management.
- CSSD workflow status transitions.
- Sterilization batch management.
- Inventory tracking and alerts.
- Notifications.
- Hospital reports and audit history.

**Suggested visual:**  
User -> Django Views -> Models -> SQLite Database -> Templates/Dashboards

---

## Slide 7: Core Workflow

The system follows a controlled lifecycle:

1. Nurse submits request.
2. CSSD staff collects instruments.
3. Instruments are cleaned.
4. Instruments are sterilized and linked to a batch.
5. Instruments are packed.
6. Nurse receives or marks final delivery.
7. Hospital admin can audit the full history.

**Important design decision:**  
Each stage stores timestamps and operator information, which supports traceability and accountability.

**Screenshot to add:** CSSD request detail page or lifecycle timeline.

---

## Slide 8: Development Process

Development followed an incremental feature-branch approach.

**Major feature areas:**
- PROJ-4: Authentication and role routing.
- PROJ-6: Department nurse requests.
- PROJ-8: Nurse and CSSD dashboards.
- PROJ-17 to PROJ-21: Status lifecycle transitions.
- PROJ-24: Assign operator to batch.
- PROJ-27: Inventory shortage alerts.
- PROJ-29: Estimated completion time.
- PROJ-31: Audit history search and hospital reports.

**Process:**
- Build one feature at a time.
- Add tests for each feature.
- Merge completed branches into dev.
- Fix integration conflicts and regressions before release.

---

## Slide 9: Testing Strategy

Testing was done at three levels:

**Unit testing:**
- Model methods.
- Form validation.
- User roles.
- Inventory status logic.
- ETA calculations.

**Integration testing:**
- Login and redirects.
- View/model/database interaction.
- Request creation.
- Status transitions.
- Batch creation.
- Access control.

**System testing:**
- Full workflow from nurse request to delivery.
- Browser testing on localhost.
- Role-based access verification.
- Stability checks for invalid inputs and repeated actions.

**Latest verification:**
- Full test suite: 281 tests passed.
- Coverage: 87.27%.

**Screenshot to add:** pytest output or coverage output.

---

## Slide 10: Bugs Found & Quality Improvements

Important bugs discovered during testing:
- Any logged-in user could trigger CSSD status changes.
- Users could access CSSD request details without proper authorization.
- Non-nurse users could confirm delivery.
- Negative quantities could incorrectly increase stock.
- Nurse accounts could log in through the staff portal.

**Fixes and improvements:**
- Added stricter role checks.
- Improved request ownership validation.
- Added quantity validation.
- Protected CSSD-only endpoints.
- Added tests to prevent regressions.

**Key testing lesson:**  
Security and access control must be tested from the perspective of the wrong user, not only the correct user.

---

## Slide 11: Release Plan

**Version 1.0 goal:**  
Deliver a stable, demonstrable prototype covering the complete CSSD and nurse workflow.

**Release milestones:**
- Phase 1: Requirements and database design.
- Phase 2: Authentication and roles.
- Phase 3: Nurse request and CSSD modules.
- Phase 4: Sterilization workflow stages.
- Phase 5: Dashboards and monitoring.
- Phase 6: Integration testing and bug fixing.
- Phase 7: Final validation, documentation, and submission.

**Planned or extended features:**
- Estimated completion time.
- Inventory shortage alerts.
- Daily sterilization reports.
- Audit history search.
- Enhanced notifications.
- Additional management roles.

---

## Slide 12: Challenges Faced

**Challenges:**
- Managing many feature branches and merge conflicts.
- Keeping role permissions consistent across pages.
- Connecting frontend templates with real Django data.
- Handling state transitions without allowing invalid skips.
- Maintaining test coverage while adding new features.
- Balancing project scope with semester deadlines.

**Specific challenge:**  
The lifecycle workflow required careful validation because each status depends on the previous status.

---

## Slide 13: Lessons Learned

**Technical lessons:**
- Role-based access must be designed early, not added at the end.
- State machines need clear rules and tests.
- Integration tests catch issues that unit tests miss.
- Test data and seed accounts make demos much easier.
- Small feature branches are easier to review and merge.

**Team/process lessons:**
- Scope control matters.
- Documentation helps during handoff and debugging.
- Testing should start before the final phase.
- A working core system is more valuable than many unfinished features.

---

## Slide 14: Final Outcome

The final system provides:
- A working nurse request portal.
- A CSSD technician workflow dashboard.
- Full sterilization lifecycle tracking.
- Inventory alerts.
- Batch operator assignment.
- Notifications.
- Hospital admin reports.
- Searchable audit history.
- Verified test coverage and stable release readiness.

**Closing statement:**  
The CSSD Management System demonstrates how software engineering practices can transform a manual hospital workflow into a traceable, role-based, and testable digital system.

