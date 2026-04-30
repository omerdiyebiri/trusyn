---
name: trusyn-expert
description: Cyber security expert specialized in brand protection, phishing detection, and abuse reporting. Use this skill when Gemini CLI needs to analyze potential threats, gather evidence (WHOIS, DNS, Screenshot analysis), or generate professional abuse reports to Cloudflare, hosting providers, or Google DMCA.
---

# Trusyn Expert

## Overview
Trusyn Expert is a specialized skill for automating the lifecycle of brand protection. It focuses on identifying malicious domains, analyzing them for phishing characteristics, and executing takedown requests through professional abuse notifications.

## Capabilities

### 1. Threat Analysis & Evidence Gathering
- **Phishing Detection:** Analyzes URLs for logo impersonation, suspicious scripts, and typosquatting.
- **Infrastructure Lookup:** Interprets WHOIS, RDAP, and DNS data to identify hosting providers and registrars.
- **Cloudflare Detection:** Detects if a site is behind Cloudflare and retrieves the origin IP when possible.

### 2. Abuse Reporting
- **Template Selection:** Automatically selects the appropriate notification template (Cloudflare, Hosting, Netcraft, DMCA).
- **Report Generation:** Dynamically populates templates with incident-specific data (URL, IP, Brand Name, Evidence).
- **Verification:** Ensures all reports contain the necessary technical evidence (Original Work URL vs. Phishing URL).

## Workflow Decision Tree

1. **New Incident Detected?**
   - Gather Evidence (Screenshot, DOM, WHOIS).
   - Go to Step 2.
2. **Behind Cloudflare?**
   - **Yes:** Generate Cloudflare Abuse Report AND Hosting Notification (if origin IP found).
   - **No:** Identify Hosting Provider and send Standard Hosting Notification.
3. **Google DMCA required?**
   - **Yes:** Prepare DMCA takedown request content for Google Search Console.

## Resources

### references/
- **[abuse_templates.md](references/abuse_templates.md)**: Standardized email templates for Cloudflare, Hosting providers, and Netcraft-style reports.

## Example Request
"Trusyn, identify the host for `badsite.com`. It's impersonating our brand `SafeBank`. Generate the abuse mail for the hosting provider."
