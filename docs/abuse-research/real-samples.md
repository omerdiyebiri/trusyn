# Real-World Abuse Notification Samples

Source: Reports actually received in production by Trusyn customers (sanitized).

## 1. Cloudflare → Site Owner (Phishing Report Acknowledgement)

**Subject:** `[3afb16b95222e212]: Phishing report received regarding your site`
**To:** site contact (info2@ibizagsmr.com)
**From:** Cloudflare Trust & Safety automated system

Key elements:
- Report ID in subject (bracketed)
- Direct link to dashboard mitigation page
- Numbered steps to "Request review"
- Reply path: `abusereply@cloudflare.com`
- URLs defanged with `hxxp://` and `[.]`
- Body labels CF actions: "We have restricted access" + "We have forwarded this complaint to your hosting provider"

```
Hello,

Cloudflare received an Phishing report regarding: ibizagsmr[.]com.

We have restricted access to the reported URL(s).
We have forwarded this complaint to your hosting provider.

To respond to this complaint through the Cloudflare dashboard, you can click this link:
https://dash.cloudflare.com/<account_id>/abuse-reports/report/<report_id>/blocked-content
and select Request review...

Report ID: 3afb16b95222e212
Logs or other evidence of abuse:  http://ibizagsmr.com/
Reported URLs: hxxp://ibizagsmr[.]com/
```

## 2. Cloudflare → Hosting Provider (Forwarded Phishing Report)

Cloudflare automatically forwards phishing reports to the hosting provider behind their CDN/proxy.

Key elements:
- "Cloudflare is generally not a website hosting provider" disclaimer
- Origin IP disclosed: `46.28.234.137`
- `curl -v -H "Host: ..." <ip>/` verification command included
- Original reporter info: "Anonymous" (when CF report form is used anonymously)
- Reply path: `abusereply@cloudflare.com`

```
Hello,

Cloudflare received a Phishing report regarding ibizagsmr[.]com

Please be aware Cloudflare offers network service solutions including pass-through
security services, a content distribution network (CDN) and registrar services.

The actual host for ibizagsmr[.]com are the following IP addresses. 46.28.234.137.
Using the following command, you can confirm the site in question is hosted at that IP:
curl -v -H "Host: ibizagsmr[.]com" 46.28.234.137/

Reporter: Anonymous
Reported URLs: hxxps://ibizagsmr[.]com/
Logs or Evidence of Abuse: https://ibizagsmr.com/

Please address this issue with your customer.

Regards,
Cloudflare Trust & Safety
```

## 3. Netcraft → Hosting Provider (Brand Protection Phishing Report)

Netcraft is the gold-standard reference for our system — they handle takedowns for
banks and brands and have very high success rates.

**Subject (typical):** `Netcraft Phishing Notification: <domain> - Issue #<num>`

Key elements:
- "On behalf of <customer>" framing — tells hosting provider whose brand is being abused
- Original brand URL: `https://klot.com/`
- Country-restriction warning: "this attack is being restricted so it is only visible
  from certain countries. Before deciding that the attack has been resolved please confirm
  it cannot be viewed from the following countries: Turkey"
- Evidence preservation request: "please keep the fraudulent content safe so that our
  customer and law enforcement agencies can investigate this incident further once the
  site is offline"
- Public incident URL: `https://incident.netcraft.com/reports/<id>`
- Real contact info: phone, fax, issue number
- API support reference: `https://incident.netcraft.com/about`

```
Dear Sir or Madam,

You are currently hosting a phishing attack on your network:
https://klotyeni.com/

This attack targets our customer, klot, website URL https://klot.com/.

Please remove this fraudulent content, and any other associated fraudulent content,
as soon as possible.

It is possible that this attack is being restricted so it is only visible from
certain countries. Before deciding that the attack has been resolved please confirm
it cannot be viewed from the following countries: Turkey

Additionally, please keep the fraudulent content safe so that our customer and law
enforcement agencies can investigate this incident further once the site is offline.

More information about the detected issue is provided at
https://incident.netcraft.com/reports/<id>

Regards,
Netcraft
Phone: +44(0)1225 447500
Fax: +44(0)1225 448600
Netcraft Issue Number: 79470566
```

## Patterns to Replicate in Trusyn

| Pattern | Source | Why it works |
|---|---|---|
| Bracketed Report ID in subject | CF | Easy threading + reply parsing |
| Defanged URLs (`hxxp://`, `[.]`) | CF | Doesn't trigger spam URL scanners on receiving end |
| Origin IP disclosure + curl verify command | CF→hosting | Eliminates "we can't find it" excuse |
| "On behalf of <customer>" framing | Netcraft | Establishes legitimacy and brand standing |
| Country-restriction warning | Netcraft | Pro signal — shows attacker tactics are known |
| Evidence preservation clause | Netcraft | Forensic-friendly, signals law enforcement coordination |
| Public incident URL on own domain | Netcraft | Receiver can verify the report exists, raises credibility |
| Real contact info (phone, issue num) | Netcraft | Differentiates from random spam reports |
| Plain-text body, no HTML images | both | Maximum deliverability across all corporate mail filters |
