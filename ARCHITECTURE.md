# AtomQuest — Architecture & Feature Reference

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Data Models](#3-data-models)
4. [Role-Based Access Control](#4-role-based-access-control)
5. [Feature Reference](#5-feature-reference)
   - [Goal Lifecycle](#51-goal-lifecycle)
   - [Check-in & Progress Scoring](#52-check-in--progress-scoring)
   - [Shared Goals (KPI Distribution)](#53-shared-goals-kpi-distribution)
   - [Cycle Management](#54-cycle-management)
   - [User Management](#55-user-management)
   - [Reports & Analytics](#56-reports--analytics)
   - [Notifications](#57-notifications)
   - [Audit Trail](#58-audit-trail)
6. [API Reference](#6-api-reference)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Configuration & Deployment](#8-configuration--deployment)

---

## 1. System Overview

AtomQuest is a performance management portal built for organisations running annual goal cycles (typically aligned to the Indian financial year, April–March). The core workflow is:

1. Admin creates a **Cycle** and activates it.
2. Employees set **Goals** (draft → submit for approval).
3. Managers **approve or reject** goals with comments.
4. Employees submit quarterly **Check-ins** with progress values.
5. Managers **approve or reject** check-ins.
6. The system calculates weighted achievement scores for **Reports**.

Every action is recorded in an immutable **Audit Trail**. In-app **Notifications** keep users informed of state changes.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│                                                             │
│   React 18 + Vite                                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │ AuthCtx  │  │ TanStack │  │  Pages   │  │Components│  │
│   │ (token)  │  │  Query   │  │ (routes) │  │(UI/layout│  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                      │                                      │
│              Axios (api/ layer)                             │
│              /api proxy → :8000                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP + Token Auth
┌──────────────────────▼──────────────────────────────────────┐
│                   Django 4.2 + DRF                          │
│                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │  Views   │  │Serializers│ │Permissions│ │Validators│  │
│   │(ViewSets)│  │          │  │  (RBAC)  │  │(business │  │
│   └──────────┘  └──────────┘  └──────────┘  │  rules)  │  │
│                                              └──────────┘  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│   │  Models  │  │  Utils   │  │ AuditLog │               │
│   │          │  │(scoring, │  │(immutable│               │
│   │          │  │ notifs)  │  │  trail)  │               │
│   └──────────┘  └──────────┘  └──────────┘               │
└──────────────────────┬──────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  SQLite / PgSQL │
              └─────────────────┘
```

### Request Flow

```
Browser → Axios (Authorization: Token <token>)
       → Django URL router → DRF ViewSet
       → Permission check (role-based)
       → Serializer validation + business rule validators
       → Model save + AuditLog write + Notification dispatch
       → Serialized JSON response
```

### Authentication

Token-based authentication via DRF `TokenAuthentication`. The frontend stores the token in `localStorage` and attaches it to every request via an Axios request interceptor. On 401, the interceptor clears the token and redirects to `/login`.

---

## 3. Data Models

```
User (Django built-in)
 └── UserProfile          role, department FK, manager FK (self-ref to User)

Department               name, is_active
ThrustArea               name, is_active (goal category)
UoMType                  name (numeric/percentage/timeline/zero_based)

Cycle                    name, status (planning/active/closed), start/end dates,
                         4 quarterly check-in dates (auto-calculated on create)

Goal                     user FK, cycle FK, title, description,
                         thrust_area FK, uom_type FK,
                         target_value, weightage (10–100),
                         status (draft/submitted/approved/rejected/locked),
                         is_shared, shared_by FK,
                         approved_by FK, approved_at, approval_comments,
                         rejection_reason

SharedGoal               goal OneToOne, department FK, created_by FK

CheckIn                  goal FK, user FK, cycle FK,
                         progress_value, progress_percentage (auto-calculated),
                         comments, status (submitted/approved/rejected),
                         approved_by FK, rejection_comments
                         UNIQUE: (goal, cycle)

AuditLog                 entity_type, entity_id, action, user FK,
                         old_values JSON, new_values JSON,
                         ip_address, user_agent, created_at (immutable)

Notification             user FK, title, message, notification_type,
                         goal FK (optional), checkin FK (optional), is_read
```

### Key Constraints

- A user can have at most **8 goals** per cycle.
- Individual goal weightage: **10–100%**.
- Total weightage across all goals in a cycle must equal **exactly 100%** before submission.
- Only **one check-in** per goal per cycle (`unique_together`).
- Goals can only be created/edited during **Active** cycles.
- Approved goals are **locked** — only admins can edit them.

---

## 4. Role-Based Access Control

### Roles

| Role | Description |
|---|---|
| **Admin** | Full system access. Manages users, cycles, reference data. Can edit any goal regardless of status. |
| **Manager** | Manages their direct reports. Approves/rejects goals and check-ins for their team. Can inline-edit submitted goals during review. |
| **Employee** | Creates and submits their own goals. Submits check-ins for approved goals. Views own reports. |
| **Viewer** | Read-only access to all goals, check-ins, and reports. Cannot create or modify anything. |

---

### Permission Matrix

#### Users & Profiles

| Action | Admin | Manager | Employee | Viewer |
|---|---|---|---|---|
| Create new user | ✅ | ❌ | ❌ | ❌ |
| View all users | ✅ | ❌ | ❌ | ❌ |
| View own team | ✅ | ✅ (direct reports only) | ❌ | ❌ |
| View own profile | ✅ | ✅ | ✅ | ✅ |
| Update user role / department / manager | ✅ | ❌ | ❌ | ❌ |
| Deactivate / reactivate user | ✅ | ❌ | ❌ | ❌ |

#### Cycles

| Action | Admin | Manager | Employee | Viewer |
|---|---|---|---|---|
| Create cycle | ✅ | ❌ | ❌ | ❌ |
| Activate cycle (Planning → Active) | ✅ | ❌ | ❌ | ❌ |
| Close cycle (Active → Closed) | ✅ | ❌ | ❌ | ❌ |
| View cycles | ✅ | ✅ | ✅ | ✅ |

#### Goals

| Action | Admin | Manager | Employee | Viewer |
|---|---|---|---|---|
| Create goal | ✅ | ✅ | ✅ | ❌ |
| View own goals | ✅ | ✅ | ✅ | — |
| View team goals | ✅ | ✅ (direct reports) | ❌ | — |
| View all goals | ✅ | ❌ | ❌ | ✅ (read-only) |
| Edit draft goal | ✅ | ✅ (own) | ✅ (own) | ❌ |
| Edit submitted goal (inline review) | ✅ | ✅ (team's) | ❌ | ❌ |
| Edit approved/locked goal | ✅ | ❌ | ❌ | ❌ |
| Submit goal for approval | ✅ | ✅ (own) | ✅ (own) | ❌ |
| Approve goal | ✅ | ✅ (direct reports' goals) | ❌ | ❌ |
| Reject goal | ✅ | ✅ (direct reports' goals) | ❌ | ❌ |
| Push shared goal to department | ✅ | ✅ | ❌ | ❌ |

#### Check-ins

| Action | Admin | Manager | Employee | Viewer |
|---|---|---|---|---|
| Submit check-in | ✅ | ✅ (own) | ✅ (own) | ❌ |
| View own check-ins | ✅ | ✅ | ✅ | — |
| View team check-ins | ✅ | ✅ (direct reports) | ❌ | — |
| View all check-ins | ✅ | ❌ | ❌ | ✅ (read-only) |
| Approve check-in | ✅ | ✅ (direct reports') | ❌ | ❌ |
| Reject check-in | ✅ | ✅ (direct reports') | ❌ | ❌ |

#### Reference Data (ThrustAreas, UoM Types, Departments)

| Action | Admin | Manager | Employee | Viewer |
|---|---|---|---|---|
| Create / update / delete | ✅ | ❌ | ❌ | ❌ |
| View | ✅ | ✅ | ✅ | ✅ |

#### Audit Trail & Reports

| Action | Admin | Manager | Employee | Viewer |
|---|---|---|---|---|
| View audit trail | ✅ | ✅ (own + team) | ✅ (own) | ✅ (all, read-only) |
| View reports | ✅ | ✅ (own + team) | ✅ (own) | ✅ (all, read-only) |

---

### How Permissions Are Enforced

**Backend (authoritative):**
- Every ViewSet uses `permission_classes` to enforce role checks at the view level.
- Object-level permissions (`IsGoalOwnerOrManager`, `CanApproveGoal`, etc.) enforce ownership and hierarchy checks per object.
- `get_filtered_queryset()` in `permissions.py` scopes list queries by role — admins see all, managers see own + team, employees see own only.

**Frontend (UX layer):**
- `AuthContext` exposes `user` and `role` to all components.
- `ProtectedRoute` wraps routes with a `roles` prop — non-matching roles are redirected to `/dashboard`.
- Navigation items in `Sidebar.jsx` are rendered per-role from the `NAV` map.
- Action buttons (Approve, Reject, Add User, etc.) are conditionally rendered based on role.

The frontend guards are UX conveniences only. The backend is the security boundary.

---

## 5. Feature Reference

### 5.1 Goal Lifecycle

```
Draft ──► Submitted ──► Approved ──► Locked
                   └──► Rejected ──► (edit & resubmit as Draft)
```

| State | Who can edit | Notes |
|---|---|---|
| Draft | Owner, Admin | Freely editable |
| Submitted | Manager (inline), Admin | Manager can edit during review |
| Approved | Admin only | Locked for all others |
| Rejected | Owner, Admin | Employee edits and resubmits |
| Locked | Admin only | Explicitly locked by admin |

**Submission rules:**
- Total weightage of all goals in the cycle must equal exactly **100%**.
- Cycle must be in **Active** status.
- Max **8 goals** per user per cycle.

---

### 5.2 Check-in & Progress Scoring

Check-ins are submitted by employees for each **approved** goal during an **active** cycle. One check-in per goal per cycle.

**Progress percentage calculation** (in `utils.py`):

| UoM Type | Formula |
|---|---|
| **Numeric** | `min((progress_value / target_value) × 100, 100)` |
| **Percentage** | `progress_value` directly (clamped 0–100) |
| **Timeline** | `(today − cycle_start) / (cycle_end − cycle_start) × 100` |
| **Zero-based** | `0%` if `progress_value == 0`, else `100%` |

**Weighted achievement score** (for reports):
```
score = Σ (goal.progress_percentage × goal.weightage) / 100
```

**Quarterly check-in windows** (auto-set on cycle creation):

| Quarter | Date | Period |
|---|---|---|
| Q1 | July 15 | Apr–Jun |
| Q2 | October 15 | Jul–Sep |
| Q3 | January 15 | Oct–Dec |
| Q4 | April 15 | Jan–Mar |

---

### 5.3 Shared Goals (KPI Distribution)

Admins and managers can push a goal from the KPI library to an entire department. Each employee in the department receives a copy of the goal with:
- `title` and `target_value` locked as **read-only**
- `weightage` editable by the employee (to fit their 100% total)

The `SharedGoal` model links the goal to the department and records who pushed it.

---

### 5.4 Cycle Management

Cycles follow a strict state machine: `Planning → Active → Closed`.

- **Planning**: Cycle exists but goal creation is not yet open.
- **Active**: Goal creation, editing, and check-in submission are open.
- **Closed**: No new goals or check-ins. All data is read-only.

On creation, four quarterly check-in dates are auto-calculated from the cycle's `start_date`. Only one cycle should be active at a time (enforced by convention, not a DB constraint).

---

### 5.5 User Management

Only **admins** can create, update, deactivate, or reactivate users.

**Creating a user** (`POST /api/user-management/`):
- Sets `username`, `email`, `password`, `first_name`, `last_name`
- Assigns `role` (employee / manager / admin / viewer)
- Optionally assigns `department_id` and `manager_id` (reporting manager)
- Creates both a Django `User` and a `UserProfile` atomically
- Logs to `AuditLog`

**Updating a user** (`PUT /api/user-management/{id}/`):
- Can change `role`, `manager_id`, `department_id`

**Deactivating** sets `UserProfile.is_active = False`. The user can no longer log in (enforced by checking `is_active` in the auth flow). Reactivation reverses this.

The `RegisterUserModal` in the frontend provides the admin UI for user creation with department and manager dropdowns.

---

### 5.6 Reports & Analytics

Available to all roles (scoped by data access rules):

- **Weighted Achievement Score**: `Σ (progress% × weightage) / 100` per user per cycle
- **Goal Progress Chart**: Bar chart showing progress per approved goal
- **Status Distribution**: Count breakdown of goal statuses
- **Cycle filter**: Switch between cycles
- **CSV Export**: Download report data

---

### 5.7 Notifications

In-app notifications are generated synchronously on state changes:

| Event | Recipient |
|---|---|
| Goal submitted | Manager |
| Goal approved | Employee |
| Goal rejected | Employee |
| Check-in period open | Employee |
| Check-in pending review | Manager |
| Check-in approved | Employee |
| Check-in rejected | Employee |
| Shared goal assigned | Employee |

Notifications are stored in the `Notification` model and fetched via `GET /api/notifications/`. The TopBar bell icon shows an unread count badge. "Mark all read" is available in the notification panel.

---

### 5.8 Audit Trail

Every mutating action writes an immutable `AuditLog` record:

| Field | Description |
|---|---|
| `entity_type` | goal / checkin / user / cycle |
| `entity_id` | PK of the affected record |
| `action` | create / update / approve / reject / submit / lock / delete |
| `user` | Who performed the action |
| `old_values` | JSON snapshot before change |
| `new_values` | JSON snapshot after change |
| `ip_address` | Client IP |
| `user_agent` | Browser/client string |
| `created_at` | Timestamp (auto, immutable) |

Audit logs are never updated or deleted. Access is scoped by role (see Permission Matrix).

---

## 6. API Reference

All endpoints require `Authorization: Token <token>` unless noted.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api-token-auth/` | Login — returns `{ token }` |

### Goals

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/goals/` | All roles | List goals (scoped by role) |
| POST | `/api/goals/` | Employee, Manager, Admin | Create goal |
| GET | `/api/goals/{id}/` | Owner, Manager, Admin, Viewer | Get goal detail |
| PUT/PATCH | `/api/goals/{id}/` | Owner (draft), Manager (submitted), Admin | Update goal |
| POST | `/api/goals/{id}/submit/` | Owner, Admin | Submit for approval |
| POST | `/api/goals/{id}/approve/` | Manager (team), Admin | Approve goal |
| POST | `/api/goals/{id}/reject/` | Manager (team), Admin | Reject with reason |
| POST | `/api/goals/{id}/edit_during_review/` | Manager (team), Admin | Inline edit submitted goal |
| GET | `/api/goals/pending/` | Manager, Admin | Goals awaiting approval |
| POST | `/api/goals/{id}/push_to_department/` | Manager, Admin | Push as shared goal |

### Check-ins

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/checkins/` | All roles | List check-ins (scoped by role) |
| POST | `/api/checkins/` | Employee, Manager, Admin | Submit check-in |
| GET | `/api/checkins/{id}/` | Owner, Manager, Admin, Viewer | Get check-in detail |
| POST | `/api/checkins/{id}/approve/` | Manager (team), Admin | Approve check-in |
| POST | `/api/checkins/{id}/reject/` | Manager (team), Admin | Reject check-in |
| GET | `/api/checkins/pending/` | Manager, Admin | Check-ins awaiting review |
| GET | `/api/checkins/approved_goals/` | Employee, Manager, Admin | Goals eligible for check-in |

### Cycles

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/cycles/` | All roles | List cycles |
| POST | `/api/cycles/` | Admin | Create cycle |
| PUT/PATCH | `/api/cycles/{id}/` | Admin | Update cycle |
| POST | `/api/cycles/{id}/activate/` | Admin | Planning → Active |
| POST | `/api/cycles/{id}/close/` | Admin | Active → Closed |

### User Management

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/user-management/` | Admin | List all users |
| POST | `/api/user-management/` | Admin | Create user with role/dept/manager |
| GET | `/api/user-management/{id}/` | Admin | Get user detail |
| PUT | `/api/user-management/{id}/` | Admin | Update role/dept/manager |
| POST | `/api/user-management/{id}/deactivate/` | Admin | Deactivate user |
| POST | `/api/user-management/{id}/reactivate/` | Admin | Reactivate user |
| GET | `/api/users/me/` | All roles | Current user profile |
| GET | `/api/users/team/` | Manager, Admin | Team members |

### Reference Data

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/thrust-areas/` | All roles | List thrust areas |
| POST/PUT/DELETE | `/api/thrust-areas/` | Admin | Manage thrust areas |
| GET | `/api/uom-types/` | All roles | List UoM types |
| GET | `/api/departments/` | All roles | List departments |
| POST/PUT/DELETE | `/api/departments/` | Admin | Manage departments |

### Notifications

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/api/notifications/` | All roles | User's notifications |
| POST | `/api/notifications/mark_all_read/` | All roles | Mark all as read |

---

## 7. Frontend Architecture

### State Management

- **Server state**: TanStack Query (`useQuery`, `useMutation`). Each resource has a query key (e.g., `['goals']`, `['cycles']`). Mutations invalidate relevant queries on success.
- **Auth state**: `AuthContext` — holds `user`, `role`, `token`, `login()`, `logout()`. Persisted to `localStorage`.
- **UI state**: Local `useState` in components (modal open/close, form state via `react-hook-form`).

### Routing

React Router v6. All authenticated routes are wrapped in `AppLayout` (Sidebar + TopBar). `ProtectedRoute` checks `role` from `AuthContext` and redirects unauthorized users to `/dashboard`.

```
/login                    — public
/dashboard                — all roles
/goals                    — employee, manager, admin
/approvals                — manager, admin
/checkins                 — employee, manager, admin
/reports                  — all roles
/admin/users              — admin only
/admin/cycles             — admin only
```

### Component Structure

```
AppLayout
├── Sidebar
│   ├── Nav links (role-filtered)
│   └── Footer: AvatarBadge (username + role) + Logout
└── TopBar
    ├── Page title
    ├── Notification bell + panel
    ├── RoleBadge (color-coded role chip)
    └── User avatar
```

### Design System

All visual tokens live in `frontend/src/styles/theme.css` as CSS custom properties:
- `--color-primary-*` — blue accent scale
- `--color-slate-*` — neutral dark scale
- `--radius-*`, `--shadow-*`, `--transition-*`

Utility classes like `glass-card`, `btn-primary`, `input-field`, `label`, `field-error`, `data-table`, `page-header` are defined in `index.css` on top of Tailwind.

---

## 8. Configuration & Deployment

### Environment Variables (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | insecure default | Django secret key — **change in production** |
| `DEBUG` | `True` | Set to `False` in production |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | SQLite or `postgres://...` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis URL for Celery |

### Production Checklist

- Set `DEBUG=False`
- Set a strong `SECRET_KEY`
- Switch `DATABASE_URL` to PostgreSQL
- Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to your domain
- Run `python manage.py collectstatic`
- Use a production WSGI server (gunicorn, uvicorn)
- Enable HTTPS — `SECURE_SSL_REDIRECT=True` is auto-applied when `DEBUG=False`

### Docker

A `Dockerfile` and `docker-compose.yml` are provided in `backend/` for containerised deployment. A separate `docker-compose.redis.yml` spins up a Redis container for local development.
