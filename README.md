# CSSD Management System

A comprehensive hospital management system for Central Sterile Supply Departments (CSSD). This application handles instrument tracking, sterilization batch processing, and department requests with role-based access control.

##  Quick Start

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CSSD_Management_System
   ```

2. **Install dependencies:**
   ```bash
   pip install django djangorestframework
   ```

3. **Navigate to the project directory:**
   ```bash
   cd CSSD_Management_System
   ```

4. **Initialize the database:**
   ```bash
   python manage.py migrate
   ```

5. **Populate mock data (Recommended):**
   This script creates initial inventory items and sets up standard users for testing.
   ```bash
   python populate_mock_data.py
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`.

---

## Mock Credentials

All mock users use the password: `password123`

| Role | Email | Purpose |
| :--- | :--- | :--- |
| **System Administrator** | `admin@test.com` | Full system control and user management. |
| **Department Nurse** | `nurse@test.com` | Create requests for sterile instruments. |
| **CSSD Technician** | `tech@test.com`| Process sterilization batches and fulfill requests. |
| **Hospital Administrator**| `hospital@test.com`| Access reports and audit logs. |

---

##  Project Structure

- `CSSD_Management_System/`: Main Django project folder.
  - `CSSD_Management_System/`: App logic, models, and settings.
  - `static/`: Global CSS and JS assets.
  - `templates/`: HTML templates for different dashboards.
- `frontend/`: Static HTML prototypes and design assets.

---

##  Tech Stack
- **Backend:** Django 5.x
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Database:** SQLite (default for development)
- **API:** Django Rest Framework (optional)

---

##  Key Features
- **Role-Based Routing:** Automated redirection to appropriate dashboards upon login.
- **Inventory Management:** Tracking of sterile and non-sterile items with threshold alerts.
- **Sterilization Tracking:** Full lifecycle management (Requested → Collected → Cleaned → Sterilized → Packed → Delivered).
- **Notifications:** Real-time status updates for department nurses.
