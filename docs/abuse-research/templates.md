# Trusyn — Abuse Reporting Reference

Operational reference for the Trusyn abuse engine. Every contact and behavior listed here was verified against vendor documentation or Phish.report's curated contacts database (which sources from WHOIS/RDAP and vendor pages). Items that could not be verified are marked `[needs verification]`.

> **Sender identity in production**
> - From: `Trusyn Brand Protection <takedowns@trusyn.io>`
> - Reply-To: `takedowns@trusyn.io`
> - SPF: `v=spf1 include:_spf.google.com ~all` ✅
> - DKIM: `google._domainkey.trusyn.io` (2048-bit, Workspace) ✅
> - DMARC: `v=DMARC1; p=none; rua=mailto:dmarc@trusyn.io; ruf=mailto:dmarc@trusyn.io; fo=1; adkim=r; aspf=r` ✅
> - On-behalf framing: every report signs `On behalf of {{ brand_name }}`.

---

## 1. Top registrars — abuse channels

| Registrar | Primary channel | Email (if any) | Form / API | Notes |
|---|---|---|---|---|
| **GoDaddy** | Web form (mandatory) | — | https://supportcenter.godaddy.com/AbuseReport (general) ; https://supportcenter.godaddy.com/abusereport/phishing (phishing) | Email-only submissions are NOT processed — receiver redirects you to the form. (source: https://www.godaddy.com/help/reporting-abuse-27154) |
| **GoDaddy Corporate Domains (GCD)** | Email | abuse@gcd.com | https://gcd.com/abuse-policy/ | Separate enterprise channel for GCD-managed corporate domain portfolios. |
| **Namecheap (registrar)** | Email | abuse@namecheap.com | — | Phone +1-323-375-2822. Customer suspensions: legalandabuse@namecheap.com. (source: https://www.namecheap.com/support/knowledgebase/article.aspx/9196/) |
| **Namecheap (Trusted Provider API)** | API | abuseescalation@namecheap.com | https://www.namecheap.com/legal/phishing-reports-api/phishing-reports-api-tou/ | **Apply Trusyn for this** — API-based phishing reporting for trusted reporters. (source: namecheap.com/legal/phishing-reports-api) |
| **Tucows / OpenSRS** | Web form preferred, email accepted | domainabuse@tucows.com (general), arin-abuse@tucows.com (network), help@opensrs.com (resellers) | https://tucowsdomains.com/report-abuse/ ; https://tucowsdomains.com/abuse-form/phishing/ | Phone +1-416-531-5584. (source: https://tucowsdomains.com/report-abuse/) |
| **Enom** | Email | abuse@enom.com | — | Public DNS-Abuse track record. (source: https://cp.enom.com//help/abusepolicy.aspx) |
| **NameSilo** | Web form (mandatory) | hosting-abuse@namesilo.com (registrar/hosting) | https://www.namesilo.com/report_abuse.php ; https://new.namesilo.com/phishing_report.php | Form is preferred; email also monitored. (source: https://www.namesilo.com/support/v2/articles/policies/abuse-reporting-procedures) |
| **IONOS (1&1)** | Email | abuse@ionos.com | — | Same email for both registrar and hosting roles. |
| **Squarespace Domains** | Web form | abuse-network@squarespace.com | https://support.squarespace.com/hc/en-us/requests/new?ticket_form_id=23532118441357 | Phone +1-347-758-4644. |
| **Network Solutions / Web.com / Newfold** | Web form preferred | abuse@web.com ; IARPOC@Newfold.com | https://newfold.com/abuse | Newfold is parent (also covers Bluehost, HostGator, Domain.com). Phone +1-904-680-6600. |
| **Dynadot** | Web form | — | https://www.dynadot.com/report_abuse.html | Spam policy: https://www.dynadot.com/spam_policy.html |
| **Porkbun** | Web form (mandatory) | — | https://porkbun.com/abuse | Requires definitive, verifiable proof of abuse. |
| **Hostinger Domains** | Email | abuse@hostinger.com | — | Same email across registrar + hosting. |
| **Gandi** | Email | abuse@gandi.net `[needs verification]` | https://docs.gandi.net/en/gandimail/anti-spam_policy.html | Domain abuse channel not explicitly documented on the same page; RFC 2142 `abuse@gandi.net` is the standard fallback. |
| **OVH** | Web form | — | https://www.ovh.com/abuse | OVH is also a hosting provider; same form. |
| **Cloudflare Registrar** | Web form (mandatory) | — | https://abuse.cloudflare.com/ | CF does not process abuse via email; submissions through the form only. (source: https://developers.cloudflare.com/fundamentals/reference/report-abuse/) |

> Whenever WHOIS/RDAP returns a registrar's `abuse@…` email, prefer that — it's RFC 2142 compliant and contractually required to be monitored under ICANN RAA Section 3.18 (since 5 April 2024).

---

## 2. Top hosting providers — abuse channels

| Provider | Channel | Email | Form / Portal | Notes |
|---|---|---|---|---|
| **Hetzner** | Email + form | abuse@hetzner.com (hosting) ; abuse@hetzner.de (registrar) ; abuse-network@hetzner.com (notifications) | https://abuse.hetzner.com/issues/new?lang=en ; https://docs.hetzner.com/general/security-and-identify/abuse-form/ | Detailed abuse form with structured fields. |
| **OVH** | Web form | — | https://www.ovh.com/abuse | |
| **DigitalOcean** | Email + form | abuse@digitalocean.com | https://www.digitalocean.com/company/contact/abuse | |
| **AWS** | Email + form | trustandsafety@support.aws.com (T&S — current) ; abuse@amazonaws.com (legacy) ; email-abuse@amazon.com (SES) | "Report abusive activity from AWS resources" form (link in https://repost.aws/knowledge-center/report-aws-abuse) | `ec2-abuse@amazon.com` is deprecated. (source: https://repost.aws/knowledge-center/report-aws-abuse) |
| **Google Cloud** | Email + form | google-cloud-compliance@google.com | https://support.google.com/code/contact/cloud_platform_report | Network-level abuse: network-abuse@google.com. |
| **Microsoft Azure** | Web form (mandatory) | — | https://msrc.microsoft.com/report/abuse | |
| **Linode (Akamai)** | Email + form | abuse@linode.com | https://www.linode.com/legal-abuse/ | |
| **Vultr (Constant)** | Email + form | abuse@constant.com | https://www.vultr.com/company/contact/ | Phone +1-973-849-0500. |
| **Hostinger** | Email | abuse@hostinger.com | — | |
| **Bluehost / HostGator (Newfold)** | Web form | — | https://newfold.com/abuse | Same Newfold-wide portal. |
| **Cloudflare Pages/Workers** | Web form | — | https://abuse.cloudflare.com/ | Same form as CDN/Registrar. |
| **Contabo** | Email | abuse@contabo.com ; abuse@contabo.de | — | Phone +49-89-21268372. |
| **Squarespace (sites)** | Web form | abuse-network@squarespace.com | https://support.squarespace.com/hc/en-us/requests/new?ticket_form_id=23532118441357 | |
| **Leaseweb** | Email | abuse@leaseweb.com `[needs verification]` | — | RFC 2142 fallback; phish.report contact page returned 404 at research time. |
| **Choopa / Constant Co** | (same as Vultr) | abuse@constant.com | — | Choopa was acquired by Constant; same channel. |

---

## 3. Cloudflare specifics

- **Single portal**: https://abuse.cloudflare.com/ branches into categories (DMCA / Phishing & Malware / Trademark / Child Exploitation / etc.).
- **Phishing form**: https://abuse.cloudflare.com/phishing.
- **Required for phishing**: domain name + specific URL of the phishing page.
- **What CF does on accept**:
  - Confirms the page exists
  - Displays a CF warning interstitial to visitors
  - Notifies the origin's hosting provider (forwarding the report)
  - Notifies the site owner via the WHOIS/RDAP contact email
- **What CF does NOT do**: remove content from the origin (CF is a pass-through). Hosting/registrar must take that action.
- **Email is NOT a working channel**: email submissions get an automated response directing to the form.
- **CF abuse report ID** (e.g. `3afb16b95222e212`) is the bracketed token in subject of CF's automated reply — use as our incident-correlation ID.

> **Implementation hint for Trusyn**: We cannot post to the CF form directly via simple HTTP (CF protects its own forms with bot detection — we got 403 on `WebFetch`). Two viable paths:
> 1. **Headless browser submission**: a Playwright-based form-poster (we already have Playwright in the stack for screenshots).
> 2. **Email fallback**: send to `abuse@cloudflare.com` knowing it will be auto-redirected, but include a Trusyn-side note that this is a duplicate of an incident also being filed against the hosting provider — this preserves audit trail without expecting CF action via email.

---

## 4. Google Safe Browsing

- **Form**: https://safebrowsing.google.com/safebrowsing/report_phish/
- **Fields**:
  - URL (required)
  - Email Address (optional — Google may follow up)
  - Subject of phishing email (optional)
  - Text of phishing email (optional)
  - Organization being impersonated (optional dropdown — "Other" + specify)
- **Behavior**: Once Google's classifier confirms the URL, Chrome / Firefox / Safari (via Google Safe Browsing API) will display interstitial warnings for that URL globally. Typically takes minutes to hours.
- **Trusyn use**: file Safe Browsing in parallel with hosting/registrar reports. It does not take the site offline, but it dramatically reduces traffic to the phish, which pressures the host.
- **Google Web Risk Submission API** (https://docs.cloud.google.com/web-risk/docs/submission-api): paid GCP API for programmatic submission — deferred decision; manual form is sufficient at current volume.

> **DMCA distinction**: use Safe Browsing for phishing/malware. Use https://www.google.com/webmasters/tools/spamreportform for search-spam. Use a DMCA takedown only for true copyright infringement (e.g. cloned site assets). DMCA via https://www.google.com/dmca and 17 USC §512(c)(3) elements.

---

## 5. Email deliverability — the "don't get spam-foldered" checklist

### 5.1 Authentication (already done for trusyn.io)

| Record | Status | Value |
|---|---|---|
| SPF | ✅ | `v=spf1 include:_spf.google.com ~all` |
| DKIM | ✅ | `google._domainkey` 2048-bit RSA |
| DMARC | ✅ | `p=none; rua=mailto:dmarc@trusyn.io; ruf=mailto:dmarc@trusyn.io; fo=1; adkim=r; aspf=r` |

**Next steps**: leave `p=none` for the first 4 weeks while we bake reputation, then escalate to `p=quarantine` once DMARC reports show ≥ 99% pass rate.

### 5.2 Per-message hygiene (Gmail's 2024 rules apply, applicable to <5000 msg/day senders too)

(source: https://support.google.com/a/answer/81126)

- **RFC 5322 strict**: each single-instance header (`From:`, `To:`, `Subject:`, `Date:`) must appear exactly once. Gmail rejects messages with duplicates.
- **Valid PTR**: outbound IP must have a reverse-DNS record matching the HELO/EHLO. Workspace handles this for us when sending via `smtp.gmail.com`.
- **TLS**: mandatory. aiosmtplib already uses STARTTLS via `use_tls=True`.
- **Spam complaint rate**: Gmail wants ≤ 0.1%, hard cap 0.3%. Abuse reports won't trigger spam-button clicks normally, but stay below.
- **Subject + From/Display name truthfulness**: no impersonation. We always use `Trusyn Brand Protection <takedowns@trusyn.io>`.

### 5.3 Headers we add to every abuse report

```
From: Trusyn Brand Protection <takedowns@trusyn.io>
Reply-To: takedowns@trusyn.io
To: {{ recipient }}
Subject: {{ subject }}
Date: {{ rfc5322_date }}
Message-ID: <{{ uuid }}@trusyn.io>
X-Trusyn-Incident-ID: {{ incident_id }}
X-Trusyn-Brand: {{ brand_name }}
X-Trusyn-Report-Type: phishing|malware|typosquat|trademark
Precedence: bulk
Auto-Submitted: auto-generated
```

- `Message-ID` we generate ourselves, ensures threading on the receiver's side.
- `X-Trusyn-*` headers let us parse our own outbound on IMAP for replies.
- `Precedence: bulk` + `Auto-Submitted: auto-generated` are RFC-compliant (RFC 3834) signals that this is an automated notice — abuse desks expect them.

> **Do NOT** add `List-Unsubscribe` for abuse mail. That header signals marketing/list mail and is wrong here. The unsubscribe model doesn't apply: we're filing a regulatory-style notice, not a newsletter.

### 5.4 Subject-line patterns that survive spam filters

| Recipient | First contact | Follow-up (T+72h, T+168h) |
|---|---|---|
| Hosting provider | `[Trusyn-{{ incident_id8 }}] Phishing on your network: {{ target_domain }}` | `[Trusyn-{{ incident_id8 }}] Follow-up: phishing still live at {{ target_domain }}` |
| Registrar | `[Trusyn-{{ incident_id8 }}] DNS Abuse (phishing) — {{ target_domain }} — RAA §3.18` | `[Trusyn-{{ incident_id8 }}] Reminder: phishing domain {{ target_domain }} pending suspension` |
| CF (email backstop) | `[Trusyn-{{ incident_id8 }}] Phishing report duplicate — {{ target_domain }}` | (no follow-up — file second form submission instead) |
| Trademark / DMCA | `[Trusyn-{{ incident_id8 }}] Trademark abuse / DMCA — {{ target_domain }} — {{ brand_name }}` | `[Trusyn-{{ incident_id8 }}] DMCA follow-up — {{ target_domain }}` |

**Avoid**: ALL CAPS, excessive `!`, the words `URGENT!!!`, `FREE`, `WINNER`. These are the highest-weight spam-classifier triggers per common Bayesian filter rules. Calm, factual subjects pass cleanly.

### 5.5 Rate-limiting

- **Per recipient domain**: minimum 30 seconds between successive sends. (Defends against bulk-flag at the receiver MTA.)
- **Per outbound minute (global)**: cap 30 messages/minute. Workspace's hard cap is 2000 messages/day per user; we're nowhere near it but bursting will trip Gmail's reputation engine.
- **Warmup**: the first 14 days of `takedowns@trusyn.io` should send <100 abuse mails/day, with at least 50% to mailboxes that respond (e.g. send Trusyn-internal cc's). Reputation builds with positive engagement signals.

---

## 6. Email templates (plain-text, RFC 5322 safe)

> **Variable conventions**: all placeholders in `{{ snake_case }}` form. The Trusyn renderer must pre-defang `target_url` → `defanged_url` (`http://` → `hxxp://`, `.` → `[.]`) before substitution. Templates are intentionally short (≤ 280 words) — long bodies hurt deliverability.

### 6.1 `HOSTING_PHISHING.txt` — to hosting abuse desk

```
Subject: [Trusyn-{{ incident_id8 }}] Phishing on your network: {{ target_domain }}

Dear Sir or Madam,

You are currently hosting a phishing attack on your network at {{ origin_ip }}:

  {{ target_url }}

This attack impersonates our customer {{ brand_name }} (legitimate site:
{{ brand_official_url }}). The fraudulent page collects credentials and
financial data from victims who arrive via SMS, email or paid ads.

You can verify the content at the origin with:

  curl -v -H "Host: {{ target_domain }}" {{ origin_ip }}/

Evidence we have collected:
  - Full DOM snapshot
  - High-resolution screenshot: {{ evidence_screenshot_url }}
  - WHOIS / RDAP record
  - DNS A / MX / NS records at time of detection
  - Public Trusyn incident record: {{ incident_public_url }}

It is possible the attack is geo-restricted; please confirm the page
cannot be viewed from these countries before deciding it is resolved:
{{ country_restrictions }}

Please remove this fraudulent content as soon as possible. We ask that
you preserve the content and access logs so that {{ brand_name }} and
law enforcement can investigate further once the page is offline.

We will follow up in 72 hours if the page is still live.

Regards,
Trusyn Brand Protection (on behalf of {{ brand_name }})
{{ reporter_contact }}
Incident ID: {{ incident_id }}
```

### 6.2 `REGISTRAR_PHISHING.txt` — to registrar abuse desk

```
Subject: [Trusyn-{{ incident_id8 }}] DNS Abuse (phishing) — {{ target_domain }} — RAA §3.18

To the Abuse Department of {{ whois_registrar }},

This is a formal notice of well-evidenced DNS Abuse at the following
domain registered through your services:

  Domain:        {{ target_domain }}
  Phishing URL:  {{ target_url }}
  Registered:    {{ whois_created_at }}

The domain is being used to conduct a phishing attack impersonating our
customer {{ brand_name }} ({{ brand_official_url }}). Under the 2024
amendments to the ICANN Registrar Accreditation Agreement (Section 3.18,
effective 5 April 2024), registrars are required to take prompt
mitigation action against well-evidenced DNS Abuse, of which phishing
is an enumerated category.

Evidence (also available at {{ incident_public_url }}):
  - DOM snapshot of the credential-harvesting page
  - High-resolution screenshot: {{ evidence_screenshot_url }}
  - Comparison of the imitated brand assets to our customer's
    legitimate site at {{ brand_official_url }}
  - WHOIS / RDAP record
  - Hosting origin IP: {{ origin_ip }}

Requested action: suspension of {{ target_domain }} (clientHold or
serverHold) and a confirming response to {{ reporter_contact }}.

Please cite incident {{ incident_id }} in any correspondence.

Regards,
Trusyn Brand Protection (on behalf of {{ brand_name }})
{{ reporter_contact }}
```

### 6.3 `CF_PHISHING.txt` — Cloudflare backstop email

> Cloudflare does not action email reports — see §3 above. This template is sent only to create a paper trail in our IMAP, mirroring the form submission we (or the operator) make to https://abuse.cloudflare.com/phishing. Do not expect a CF action from this email; the form submission is what triggers CF's mitigation.

```
Subject: [Trusyn-{{ incident_id8 }}] Phishing report (form duplicate) — {{ target_domain }}

Cloudflare Trust & Safety,

This message duplicates Trusyn incident {{ incident_id }}, also filed
through the Cloudflare abuse form for {{ target_domain }}.

  Reported URL:     {{ defanged_url }}
  Origin host IP:   {{ origin_ip }}
  Brand impersonated: {{ brand_name }} ({{ brand_official_url }})
  Trusyn incident:  {{ incident_public_url }}

Evidence: DOM snapshot, screenshot ({{ evidence_screenshot_url }}),
WHOIS record, DNS records.

Submitted via form for action. This email is logged for audit only.

Regards,
Trusyn Brand Protection (on behalf of {{ brand_name }})
{{ reporter_contact }}
```

### 6.4 `GOOGLE_SAFEBROWSING.txt` — form field map

> Google Safe Browsing is form-only. This template documents the field-to-data mapping rather than an email body.

```
URL                                : {{ target_url }}
Email Address (optional)           : {{ reporter_contact }}
Subject of phishing email (opt.)   : {{ phish_email_subject_if_any }}
Text of phishing email (optional)  : {{ phish_email_body_if_any }}
Organization being impersonated    : {{ brand_name }}    # if listed in dropdown, else "Other" → specify
```

Submission endpoint: https://safebrowsing.google.com/safebrowsing/report_phish/. Programmatic submission (paid) via Google Web Risk Submission API.

### 6.5 `TYPOSQUAT.txt` — non-phishing typosquat / brand impersonation (UDRP-flavor)

> Use when the suspect site does NOT host a phishing page but is a typosquat or pure brand impersonation. Tone is less aggressive — UDRP, not law-enforcement.

```
Subject: [Trusyn-{{ incident_id8 }}] Typosquat / brand impersonation — {{ target_domain }}

To the Abuse Department of {{ whois_registrar }},

Domain {{ target_domain }} (registered {{ whois_created_at }}) appears
to be a typosquat of our customer {{ brand_name }} (legitimate site:
{{ brand_official_url }}).

Levenshtein similarity to {{ brand_name }}'s primary domain:
{{ similarity_score }}.

The domain is currently {{ typosquat_state }} (e.g. parked / displaying
ads / redirecting to an affiliate). While we have not confirmed phishing
activity at this time, the registration is consistent with a typosquat
intended to capture mistyped traffic and is grounds for a UDRP /
trademark complaint by our customer.

We are notifying you in good faith ahead of any UDRP filing so the
registrant has an opportunity to comply voluntarily. Evidence:
{{ incident_public_url }}.

We do not request immediate suspension at this stage. We do request
that the abuse contact for {{ target_domain }} be confirmed accurate
and reachable so that a future UDRP / phishing notice (if the site
escalates) can be acted on within ICANN RAA timelines.

Regards,
Trusyn Brand Protection (on behalf of {{ brand_name }})
{{ reporter_contact }}
```

---

## 7. Receipt-tracking — IMAP closure regex hints

Run these against the body (case-insensitive) of replies to `takedowns@trusyn.io`. Use to update `Report.status` from `SENT` → `RECEIVED` / `ACTIONED` / `DECLINED`.

| Provider | Phrase pattern | Means |
|---|---|---|
| Cloudflare | `restricted access to the reported URL` | CF interstitial enabled |
| Cloudflare | `forwarded this complaint to your hosting provider` | CF acked + forwarded |
| Cloudflare | `Report ID:\s*([0-9a-f]{16})` | Capture CF report ID for cross-ref |
| Generic registrar | `domain has been (suspended\|placed on (server\|client)Hold)` | Domain offline at registry |
| Generic registrar | `forwarded (this\|the) (complaint\|report) to (the )?registrant` | Notice given, action pending |
| Generic hosting | `(content has been\|has been) (removed\|disabled\|taken offline)` | Hosting actioned |
| Generic hosting | `(suspended\|terminated) (the\|our) customer('s)? (account\|service)` | Customer-level action |
| Netcraft | `Netcraft Issue Number:\s*(\d+)` | Cross-ref Netcraft incident |
| GSB | (no email — confirm via Chrome interstitial check) | — |
| Bounce / undeliverable | `^Mail Delivery Subsystem`, `delivery has failed`, SMTP `5\d\d` | Set status FAILED, retry up to 3× |
| Decline | `(unable to verify|insufficient evidence|please use our (web )?form)` | Set status DECLINED, queue for human review |

> **One critical regex**: the bracketed Trusyn incident token (`\[Trusyn-([a-f0-9]{8})\]`) in the reply subject is the cleanest way to thread incoming mail to outbound — much more reliable than `In-Reply-To` because many abuse desks reset threading.

---

## 8. Legal & compliance

- **ICANN RAA Section 3.18 (effective 5 April 2024)**: registrars must take "prompt and reasonable" mitigation against well-evidenced DNS Abuse, defined as malware, botnets, **phishing**, pharming, and spam-as-delivery-mechanism. ICANN Compliance enforcement (first 12 months): 2,528 domain suspensions, 328 phishing sites disabled. (source: https://www.icann.org/en/blogs/details/icanns-enforcement-of-dns-abuse-requirements-a-look-at-the-first-two-months-07-06-2024-en)
- **DMCA structure** — when filing a true copyright takedown (e.g. cloned site assets, copied logo files), include all 6 elements of 17 USC §512(c)(3): (1) physical/electronic signature, (2) identification of copyrighted work, (3) identification of infringing material with URL, (4) reporter contact info, (5) good-faith statement, (6) sworn accuracy statement under penalty of perjury. Without all six, the recipient may refuse to action.
- **Trademark claims** — only assert trademark infringement when the brand has a registered trademark (give the registration number and jurisdiction). For unregistered marks, frame as "common-law trademark" or "passing off" and adjust expectations.
- **GDPR** — when our incident bundle is forwarded by a hosting provider to the registrant (this is normal CF behavior), the reporter contact `takedowns@trusyn.io` may be visible to a third party. This is acceptable because it's an alias, not a personal email. Do NOT include any individual operator's personal email or phone in the report body.
- **Defamation / trade libel risk** — never assert unverified claims of identity ("X individual is the attacker"). Stick to observable evidence: URL, content, behavior. We have a witness model, not an attribution model.

---

## Sources

- GoDaddy reporting: https://www.godaddy.com/help/reporting-abuse-27154 ; https://supportcenter.godaddy.com/abusereport ; https://gcd.com/abuse-policy/
- Namecheap channels: https://www.namecheap.com/support/knowledgebase/article.aspx/9196/ ; https://www.namecheap.com/legal/phishing-reports-api/phishing-reports-api-tou/
- Tucows / OpenSRS: https://tucowsdomains.com/report-abuse/ ; https://support.opensrs.com/support/solutions/articles/201000063050
- Enom: https://cp.enom.com//help/abusepolicy.aspx
- NameSilo: https://www.namesilo.com/support/v2/articles/policies/abuse-reporting-procedures ; https://www.namesilo.com/blog/en/domain-names/abuse-reporting-101-how-to-escalate-phishing-and-impersonation-the-right-way
- IONOS / Squarespace / Network Solutions / Newfold / Dynadot / Porkbun / Hostinger / Gandi / OVH: Phish.report contact pages (https://phish.report/contacts/{Provider})
- Cloudflare abuse docs: https://developers.cloudflare.com/fundamentals/reference/report-abuse/ ; https://developers.cloudflare.com/fundamentals/reference/report-abuse/complaint-types/ ; https://www.cloudflare.com/trust-hub/reporting-abuse/
- AWS Trust & Safety: https://repost.aws/knowledge-center/report-aws-abuse
- Google Cloud abuse: https://support.google.com/code/contact/cloud_platform_report
- Microsoft Azure abuse: https://msrc.microsoft.com/report/abuse
- Hetzner abuse: https://abuse.hetzner.com/issues/new?lang=en ; https://docs.hetzner.com/general/security-and-identify/abuse-form/
- DigitalOcean abuse: https://www.digitalocean.com/company/contact/abuse
- Linode legal/abuse: https://www.linode.com/legal-abuse/
- Vultr contact: https://www.vultr.com/company/contact/
- Google Safe Browsing form: https://safebrowsing.google.com/safebrowsing/report_phish/
- Google Web Risk Submission API: https://docs.cloud.google.com/web-risk/docs/submission-api
- Workspace sender requirements: https://support.google.com/a/answer/81126
- ICANN DNS Abuse / RAA §3.18: https://www.icann.org/dnsabuse ; https://www.icann.org/en/contracted-parties/advisories/documents/advisory-compliance-with-dns-abuse-obligations-in-the-registrar-accreditation-agreement-and-the-registry-agreement-05-02-2024-en ; https://www.icann.org/en/blogs/details/icanns-enforcement-of-dns-abuse-requirements-a-look-at-the-first-two-months-07-06-2024-en
- ICANN Contractual Compliance dashboard: https://compliance-reports.icann.org/dnsabuse/dashboard/trends-list.html
- RFC 8058 (one-click unsubscribe — for ref only, NOT applied to abuse mail): https://www.rfc-editor.org/rfc/rfc8058.html
- RFC 3834 (auto-generated mail headers): https://www.rfc-editor.org/rfc/rfc3834.html
- Netcraft public incident pages: https://incident.netcraft.com/about
