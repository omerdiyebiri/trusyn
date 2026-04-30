# Abuse Notification Templates

These templates are based on industry standards and specific formats used by Cloudflare and Netcraft.

## 1. Cloudflare Abuse Report (Automated Flow)
**Recipient:** Cloudflare Abuse Team / Dashboard
**Subject:** [Report ID]: Phishing report received regarding [TARGET_DOMAIN]

**Content:**
Hello,
Cloudflare received a Phishing report regarding: [TARGET_DOMAIN].
Reported URLs: [REPORTED_URLS]
Logs or other evidence of abuse: [EVIDENCE_URL_OR_TEXT]

---

## 2. Hosting Provider Notification (Standard)
**Recipient:** abuse@[HOSTING_PROVIDER_DOMAIN]
**Subject:** Urgent: Phishing Activity Detected on [TARGET_DOMAIN] - [IP_ADDRESS]

**Content:**
Hello,

Phishing activity has been detected regarding [TARGET_DOMAIN] hosted on your network at [IP_ADDRESS].

Cloudflare offers network service solutions but does not host this content. The actual host for [TARGET_DOMAIN] is [IP_ADDRESS].

Reporter: Trusyn Brand Protection
Reported URLs: [REPORTED_URLS]
Logs or Evidence of Abuse: [EVIDENCE_DETAILS]

Please address this issue with your customer and remove the fraudulent content immediately.

Regards,
Trusyn Trust & Safety Team

---

## 3. Netcraft / Professional Takedown Request
**Recipient:** [PROVIDER_OR_CLEANUP_SERVICE]
**Subject:** Phishing Attack Notification - [TARGET_DOMAIN] - Issue [ISSUE_NUMBER]

**Content:**
Dear Sir or Madam,

You are currently hosting a phishing attack on your network:
[TARGET_URL]

This attack targets our customer, [BRAND_NAME], website URL [OFFICIAL_URL].

Please remove this fraudulent content, and any other associated fraudulent content, as soon as possible.

It is possible that this attack is being restricted so it is only visible from certain countries. Before deciding that the attack has been resolved please confirm it cannot be viewed from the following countries: [TARGET_COUNTRIES]

Additionally, please keep the fraudulent content safe so that our customer and law enforcement agencies can investigate this incident further once the site is offline.

Regards,
Trusyn Brand Protection Team
