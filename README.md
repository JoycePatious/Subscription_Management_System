# Brightloop Subscription Management System — Starter

A starter backbone covering the supplied problem statement. It includes a Django REST API structure, React/Vite frontend, core data models, role-aware permissions, CRUD endpoints, dashboard summaries, and a billing-generation service scaffold.

## Stack
- Backend: Python, Django, Django REST Framework, SQLite for local development
- Frontend: React + Vite
- Authentication: JWT (djangorestframework-simplejwt)
- Database: SQLite by default; PostgreSQL can be configured later

## Important
This is a **starter scaffold**, not a production-ready billing platform. Payment gateway integration, real email delivery, robust scheduled jobs, audit logging, concurrency-safe billing, and comprehensive tests still need implementation and verification.

## Run locally

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py test accounts
```
API: http://127.0.0.1:8000/api/

### Frontend
In another terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend: http://localhost:5173

The frontend currently shows a dashboard shell and module navigation. Connect the forms and tables to the API as you implement each module.

## Suggested build order
1. Create users and assign `ADMIN`, `STAFF`, or `CUSTOMER` roles.
2. Finish customer profile and product/variant/plan CRUD.
3. Implement quotation templates and quotation acceptance.
4. Implement subscription lifecycle transitions.
5. Finish tax/discount calculation and invoice line snapshots.
6. Make invoice generation scheduled and idempotent.
7. Record and allocate payments; calculate outstanding balances.
8. Add reports, pagination, database indexes, and performance tests.

## API outline
- `/api/auth/register/` — customer registration
- `/api/auth/login/` — JWT login (email + password)
- `/api/auth/token/refresh/` — refresh access token
- `/api/auth/me/` — current user
- `/api/auth/staff/` — admin-only staff creation
- `/api/auth/password-reset/` — request a time-limited reset token (console email in development)
- `/api/auth/password-reset/confirm/` — set a new password with email + token
- `/api/customers/`
- `/api/products/`, `/api/variants/`, `/api/plans/`
- `/api/quotations/`, `/api/subscriptions/`
- `/api/taxes/`, `/api/discounts/`
- `/api/invoices/`, `/api/payments/`
- `/api/dashboard/summary/`

See `docs/REQUIREMENTS_MAP.md` and `docs/DATABASE_NOTES.md`.
