# AtomQuest — Goal Setting & Tracking Portal

A full-stack performance management system for organisations to set, track, and review employee goals across quarterly cycles.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 · Django REST Framework · Token Auth |
| Database | SQLite (dev) · NeonDB PostgreSQL (production) |
| Task Queue | Celery + Redis (configured, not required for dev) |
| Frontend | React 18 · Vite · TanStack Query v5 |
| Styling | Tailwind CSS v3 · Custom design tokens |
| Deployment | Vercel (monorepo — `experimentalServices`) |

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_reference_data           # ThrustAreas, UoM types, Departments
python manage.py seed_test_users               # 3 test accounts (see below)
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The Vite dev server proxies `/api` and `/api-token-auth` to `http://localhost:8000`.

### Environment Variables

Copy `backend/.env.example` to `backend/.env`:

```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Test Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin_user` | `Admin@123` |
| Manager | `manager_user` | `Manager@123` |
| Employee | `emp_user` | `Employee@123` |

`emp_user` reports to `manager_user`. Re-running `seed_test_users` resets passwords without touching existing data.

---

## Project Structure

```
AtomQuest/
├── backend/
│   ├── atomquest/          # Django project config (settings, urls, celery)
│   └── portal/
│       ├── models.py       # All data models
│       ├── views.py        # DRF ViewSets
│       ├── serializers.py  # Request/response serialization
│       ├── permissions.py  # RBAC permission classes
│       ├── validators.py   # Business rule validators
│       ├── utils.py        # Scoring engine, audit logger, notifications
│       └── urls.py         # API routing
└── frontend/
    └── src/
        ├── api/            # Axios API layer (goals, checkins, cycles, users)
        ├── context/        # AuthContext, ToastContext
        ├── components/
        │   ├── admin/      # RegisterUserModal
        │   ├── layout/     # AppLayout, Sidebar, TopBar
        │   └── ui/         # Badge, Modal, ProgressBar, Spinner, Toast
        ├── pages/
        │   ├── admin/      # Users, Cycles
        │   ├── goals/      # GoalCard, GoalForm
        │   ├── approvals/  # ApprovalCard, ApprovalModals, EditGoalModal
        │   └── ...         # Dashboard, CheckIns, Reports, Login
        └── styles/
            └── theme.css   # All design tokens (colours, spacing, radii)
```

---

## Redis / Celery

Redis is configured but **not required** to run the app. All notifications are sent synchronously. No Celery tasks are dispatched at runtime.

To spin up a local Redis container:

```bash
docker compose -f backend/docker-compose.redis.yml up -d
```

---

## Deployment

Deployed on **Vercel** using the `experimentalServices` monorepo architecture. The backend runs as a serverless Python service; the frontend is a static Vite build. Database is **NeonDB** (serverless PostgreSQL).

See **[ARCHITECTURE.md § 8](./ARCHITECTURE.md#8-configuration--deployment)** for the full deployment guide.

---

For full architecture details, role permissions, and API reference see **[ARCHITECTURE.md](./ARCHITECTURE.md)**.
