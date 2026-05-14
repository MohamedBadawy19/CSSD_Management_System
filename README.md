Here is your updated and complete **README.md**, incorporating the setup instructions and mock credentials into the professional project overview.

# CSSD Instrument Tracking System

**Hospital Instrument Lifecycle Management Platform**

A centralized, digital workflow simulation designed to eliminate the manual, error-prone tracking of surgical and non-surgical instruments. This platform connects clinical wards with the Central Sterile Services Department (CSSD) to ensure patient safety, operational efficiency, and regulatory compliance.

---

## <img width="1905" height="786" alt="Screenshot 2026-05-14 230841" src="https://github.com/user-attachments/assets/7473c4ca-9141-489e-b8d6-73332cf4ec25" />
 Quick Start

### Prerequisites

* Python 3.10+
* pip (Python package manager)

### Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/MohamedBadawy19/CSSD_Management_System
cd CSSD_Management_System

```


2. **Install dependencies:**
```bash
pip install django djangorestframework

```


3. **Initialize the database:**
```bash
python manage.py migrate

```


4. **Populate mock data (Recommended):**
This script creates initial inventory items and sets up standard users for testing.
```bash
python populate_mock_data.py

```


5. **Run the development server:**
```bash
python manage.py runserver

```



The application will be available at `http://127.0.0.1:8000/`.

---

##  Key Features

* **Role-Based Routing:** Automated redirection to appropriate dashboards (Nurse vs. CSSD) upon secure login.
  
* **Sterilization State Machine:** A rigid 5-stage workflow (Collected → Cleaned → Sterilized → Packed → Delivered) that prevents "state-skipping" to ensure medical safety.
  
* **Inventory Management:** Live tracking of sterile and non-sterile items with automated threshold alerts for low stock.
  
* **Intelligence & Alerts:** * **Heuristic ETA:** Real-time completion time estimates for clinical planning.
  
* **Status Notifications:** Instant updates for nurses as instruments progress through the CSSD.


* **Compliance & Auditing:** Immutable audit logs for every state transition, including timestamps and operator IDs.

---

##  Tech Stack

* **Backend:** Django 5.x (Python) using Model-View-Template (MVT) architecture.
* **Frontend:** HTML5, CSS3, Vanilla JavaScript.
* **Database:** SQLite (default for development/simulation).
* **API:** Django Rest Framework.

---

##  Project Structure

* `CSSD_Management_System/`: Main Django project directory.
* `CSSD_Management_System/`: App logic, models, and core settings.
* `static/`: Global CSS, JavaScript, and image assets.
* `templates/`: HTML templates for role-specific dashboards.


* `frontend/`: Static HTML prototypes and original design assets.

---

##  Development Process

The system was developed using an **Incremental Feature-Branch Workflow** managed via Jira. Features were isolated in dedicated branches and merged only after passing a multi-tier testing cycle (Unit, Integration, and RBAC validation).


## Future Work (v1.1)

* **HIS/EHR Integration:** Connecting with Hospital Information Systems via HL7/FHIR protocols.
* **Barcode Scanning:** Native mobile support for rapid instrument check-ins.
* **Predictive Analytics:** Transitioning from heuristic ETAs to Machine Learning models.

---
