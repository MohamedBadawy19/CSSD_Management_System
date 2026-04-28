# CSSD Management System — Frontend Branch

> **Role:** Frontend only (HTML / CSS / JavaScript)  
> **Branch name:** `feature/frontend`

---

## Project Structure

```
cssd-frontend/
├── index.html                    ← Home / Role selector
├── css/
│   ├── styles.css                ← Main stylesheet
│   └── extended_styles.css       ← Dashboard & detail styles
├── js/
│   ├── mock-data.js              ← All mock data (replace with real API calls)
│   └── app.js                    ← Shared JS (icons, login, search)
└── pages/
    ├── staff-login.html          ← PROJ-11: CSSD Staff Login
    ├── nurse-login.html          ← PROJ-12: Nurse Login
    ├── cssd-dashboard.html       ← PROJ-26 + 27 + 28 + 29: Dashboard
    ├── cssd-inventory-alerts.html← PROJ-27: Inventory Shortage Alerts
    ├── cssd-request-details.html ← Request details + status update
    ├── cssd-batch-list.html      ← Sterilization batches list
    ├── cssd-batch-detail.html    ← Single batch detail
    ├── cssd-batch-create.html    ← Create new batch
    ├── nurse-dashboard.html      ← Nurse home (stats + requests)
    ├── nurse-create-request.html ← Submit new instrument request
    ├── nurse-request-details.html← Track request + vertical timeline
    └── nurse-sterile-stock.html  ← View packed & ready instruments
```

---

## Tickets Covered

| Ticket   | Feature                          | File                          |
|----------|----------------------------------|-------------------------------|
| PROJ-11  | CSSD Staff Login                 | `pages/staff-login.html`      |
| PROJ-12  | Nurse Login                      | `pages/nurse-login.html`      |
| PROJ-26  | View Pending Requests Count      | `pages/cssd-dashboard.html`   |
| PROJ-27  | View Inventory Shortage Alerts   | `pages/cssd-inventory-alerts.html` |
| PROJ-28  | View Active Requests             | `pages/cssd-dashboard.html`   |
| PROJ-29  | View Estimated Completion Time   | `pages/cssd-dashboard.html`   |

---

## How to Run

Just open `index.html` in any browser — no server needed.

```bash
# Mac / Linux
open index.html

# Windows
start index.html
```

---

## Mock Data

All data lives in `js/mock-data.js`. When the backend is ready, replace the
`MOCK.*` calls in each page's `<script>` block with `fetch()` calls to the
Django API endpoints.

| Mock object        | Django equivalent                     |
|--------------------|---------------------------------------|
| `MOCK.requests`    | `GET /dashboard/cssd/`                |
| `MOCK.inventory`   | `GET /dashboard/cssd/alerts/`         |
| `MOCK.batches`     | `GET /dashboard/cssd/batches/`        |
| `MOCK.notifications` | `GET /dashboard/nurse/notifications/` |

---

## GitHub Branch Setup

```bash
# 1. Clone the repo (or navigate into it)
git clone https://github.com/your-org/cssd-project.git
cd cssd-project

# 2. Create the branches
git checkout -b feature/frontend    # Your branch (frontend only)
git checkout -b feature/backend     # Backend team's branch
git checkout -b feature/auth        # Auth / login pages (PROJ-11 & 12)

# 3. Add frontend files to feature/frontend
git checkout feature/frontend
cp -r /path/to/cssd-frontend/* .
git add .
git commit -m "feat(frontend): add all HTML pages with mock data"
git push origin feature/frontend
```

---

## Notes for Backend Integration

- All `<form>` submissions in the frontend currently run mock JS logic.
  When integrating, point `action=""` to the correct Django URL and add `{% csrf_token %}`.
- Login pages redirect to dashboard via JS — replace with Django's `login()` + `redirect()`.
- Status update buttons in `cssd-request-details.html` mutate `MOCK.requests` in memory —
  replace with `fetch('/dashboard/cssd/request/<id>/update/<status>/')`.
