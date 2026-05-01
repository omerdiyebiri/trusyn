# Trusyn Project Progress Log

## Status Overview
- **Production URL:** https://trusyn.io
- **Backend API:** https://api.trusyn.io
- **Local Dev:** http://localhost:3000 (Frontend) / http://localhost:8000 (Backend)

## Completed Milestones

### 1. Stabilization & Bug Fixes
- **Bcrypt Compatibility:** Downgraded `bcrypt` to `3.2.2` to fix `passlib` compatibility issues that were causing crashes.
- **SQLite Support:** Configured the system to run with SQLite locally for faster development without Docker.
- **UUID Compatibility:** Updated SQLAlchemy models to use a generic `UUID` type compatible with both SQLite and Postgres.
- **CORS Configuration:** Added middleware to FastAPI to allow frontend-backend communication.

### 2. Feature Implementation
- **Admin API:** Added `POST /admin/tenants` and `GET /admin/tenants` protected by `SUPER_ADMIN` role.
- **Typosquatting Detection:** Created `typosquat_service` using Levenshtein distance to calculate similarity scores between official domains and suspect URLs.
- **Automated Scanner Integration:** Integrated similarity scoring and auto-classification into the async analysis pipeline.

## Current Phase: Evidence Gathering
- [ ] Modernize Playwright screenshot service.
- [ ] Capture DOM snapshots for analysis.
- [ ] Fetch DNS records (A, MX, NS) as evidence.

## Next Steps
1. Abuse Email Engine (Template generation based on gathered evidence).
2. Frontend Dashboard updates to display similarity scores and evidence.
