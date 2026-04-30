# Trusyn Project Guidelines

Trusyn is a high-security automated brand protection platform. These guidelines ensure consistency, security, and reliability across the codebase.

## 1. Engineering Standards
- **Language:** Python 3.10+ for Backend (FastAPI), TypeScript for Frontend (Next.js).
- **Code Style:** 
  - Backend: Follow PEP 8. Use explicit type hints for all function signatures.
  - Frontend: Use Tailwind CSS for styling. Prefer functional components and hooks.
- **Asynchronous Operations:** All network-bound tasks (Whois lookups, web scraping, email sending) MUST be asynchronous using `asyncio` and `Celery/Redis`.

## 2. Security Protocols
- **Credential Management:** NEVER hardcode API keys, database URLs, or mail credentials. Use `.env` files and validated environment variables.
- **Multi-tenancy:** Data isolation is critical. Every query must be scoped to the `tenant_id`.
- **Validation:** Every automated abuse report must undergo a validation step. High-confidence detections can be auto-approved, while ambiguous cases must be flagged for manual review.

## 3. Automation Rules
- **Scanning:** Implement rate-limiting to avoid IP bans during domain scanning.
- **Evidence Gathering:** Always capture:
  - Full DOM snapshot.
  - High-resolution screenshot (Playwright).
  - WHOIS/RDAP raw data.
  - DNS records (A, MX, NS).
- **Reporting:** Abuse emails must follow the professional templates defined in `TRUSYN_SPECS.md`.

## 4. Documentation
- All API endpoints must be documented using FastAPI's built-in OpenAPI (Swagger) support.
- Major architectural changes must be reflected in `TRUSYN_SPECS.md`.
