# Trusyn Technical Specifications

## 1. Database Schema (High-Level)

### Tenants (Multi-tenancy)
- `id`: UUID
- `name`: String
- `subscription_plan`: Enum (Basic, Pro, Enterprise)
- `created_at`: Timestamp

### Users
- `id`: UUID
- `tenant_id`: UUID (FK)
- `email`: String (Unique)
- `role`: Enum (SUPER_ADMIN, TENANT_ADMIN, TENANT_STAFF)
- `password_hash`: String

### Brands
- `id`: UUID
- `tenant_id`: UUID (FK)
- `name`: String
- `official_domains`: List[String]
- `keywords`: List[String]
- `logo_url`: String (For visual comparison)

### Incidents
- `id`: UUID
- `brand_id`: UUID (FK)
- `target_url`: String
- `status`: Enum (DETECTED, ANALYZING, VALIDATED, REPORTED, RESOLVED, FALSE_POSITIVE)
- `threat_type`: Enum (PHISHING, BRAND_IMPERSONATION, TYPOSQUATTING)
- `confidence_score`: Float
- `discovered_at`: Timestamp

### Reports
- `id`: UUID
- `incident_id`: UUID (FK)
- `recipient_type`: Enum (CLOUDFLARE, HOSTING, REGISTRAR, GOOGLE_DMCA)
- `recipient_email`: String
- `sent_at`: Timestamp
- `status`: Enum (SENT, RECEIVED, PENDING_REVIEW)
- `raw_content`: Text

## 2. Core Workflows

### W1: Scanning & Detection
1. Periodic scan of new domain registrations (CT Logs, Whois changes).
2. Keyword matching based on Brand configuration.
3. Typosquatting algorithm (Levenshtein distance).

### W2: Analysis & Evidence Gathering
1. Playwright navigates to `target_url`.
2. Capture screenshot and DOM.
3. Fetch WHOIS/RDAP data.
4. Compare visuals/content with Brand's official data.
5. Assign `confidence_score`.

### W3: Reporting (The "Abuse" Engine)
1. Identify the hosting/registrar via WHOIS lookup.
2. Check if behind Cloudflare.
3. Generate email using templates (from provided examples).
4. Send emails via SMTP or Provider API.
5. Track status via incoming mail parser (IMAP) or webhook.

## 3. API Endpoints (FastAPI)
- `POST /auth/login`
- `GET /incidents` (Filtered by tenant)
- `POST /incidents/{id}/report` (Trigger abuse mail)
- `GET /brands` (Manage brands)
- `POST /admin/tenants` (Super Admin only)
