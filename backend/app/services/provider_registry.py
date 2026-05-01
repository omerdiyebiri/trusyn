"""
Static registry of abuse channels for major registrars and hosting providers.
Sourced from docs/abuse-research/templates.md.

Each entry returns a tuple of (display_name, abuse_email_or_None, web_form_url_or_None,
prefer_form: bool). When prefer_form is True the operator should also use the web
form to escalate; the email becomes a backstop / audit-trail copy.

Lookup keys are lowercased substrings of the WHOIS 'registrar' field or hosting
provider organization name. Matching is substring-based for robustness against
WHOIS formatting differences (e.g. "GoDaddy.com, LLC" vs "GoDaddy Operating Company, LLC").
"""

from typing import Optional, Tuple, Dict

ProviderEntry = Tuple[str, Optional[str], Optional[str], bool]


REGISTRARS: Dict[str, ProviderEntry] = {
    "godaddy": ("GoDaddy", None, "https://supportcenter.godaddy.com/abusereport/phishing", True),
    "godaddy corporate": ("GoDaddy Corporate Domains", "abuse@gcd.com", "https://gcd.com/abuse-policy/", False),
    "namecheap": ("Namecheap", "abuse@namecheap.com", None, False),
    "tucows": ("Tucows", "domainabuse@tucows.com", "https://tucowsdomains.com/abuse-form/phishing/", False),
    "opensrs": ("OpenSRS", "domainabuse@tucows.com", "https://tucowsdomains.com/abuse-form/phishing/", False),
    "enom": ("Enom", "abuse@enom.com", None, False),
    "namesilo": ("NameSilo", "hosting-abuse@namesilo.com", "https://new.namesilo.com/phishing_report.php", True),
    "ionos": ("IONOS", "abuse@ionos.com", None, False),
    "1&1": ("1&1 IONOS", "abuse@ionos.com", None, False),
    "squarespace": ("Squarespace Domains", "abuse-network@squarespace.com",
                    "https://support.squarespace.com/hc/en-us/requests/new?ticket_form_id=23532118441357", True),
    "google domains": ("Squarespace Domains", "abuse-network@squarespace.com",
                       "https://support.squarespace.com/hc/en-us/requests/new?ticket_form_id=23532118441357", True),
    "network solutions": ("Network Solutions", "abuse@web.com", "https://newfold.com/abuse", False),
    "web.com": ("Web.com (Newfold)", "abuse@web.com", "https://newfold.com/abuse", False),
    "newfold": ("Newfold Digital", "abuse@web.com", "https://newfold.com/abuse", False),
    "dynadot": ("Dynadot", None, "https://www.dynadot.com/report_abuse.html", True),
    "porkbun": ("Porkbun", None, "https://porkbun.com/abuse", True),
    "hostinger": ("Hostinger", "abuse@hostinger.com", None, False),
    "gandi": ("Gandi", "abuse@gandi.net", None, False),
    "ovh": ("OVH", None, "https://www.ovh.com/abuse", True),
    "cloudflare": ("Cloudflare Registrar", "abuse@cloudflare.com",
                   "https://abuse.cloudflare.com/phishing", True),
}


HOSTING_PROVIDERS: Dict[str, ProviderEntry] = {
    "hetzner": ("Hetzner", "abuse@hetzner.com", "https://abuse.hetzner.com/issues/new?lang=en", False),
    "ovh": ("OVH", None, "https://www.ovh.com/abuse", True),
    "digitalocean": ("DigitalOcean", "abuse@digitalocean.com",
                     "https://www.digitalocean.com/company/contact/abuse", False),
    "amazon": ("AWS", "trustandsafety@support.aws.com", None, False),
    "aws": ("AWS", "trustandsafety@support.aws.com", None, False),
    "amazon technologies": ("AWS", "trustandsafety@support.aws.com", None, False),
    "google llc": ("Google Cloud", "google-cloud-compliance@google.com",
                   "https://support.google.com/code/contact/cloud_platform_report", False),
    "google cloud": ("Google Cloud", "google-cloud-compliance@google.com",
                     "https://support.google.com/code/contact/cloud_platform_report", False),
    "microsoft": ("Microsoft Azure", None, "https://msrc.microsoft.com/report/abuse", True),
    "azure": ("Microsoft Azure", None, "https://msrc.microsoft.com/report/abuse", True),
    "linode": ("Linode (Akamai)", "abuse@linode.com", "https://www.linode.com/legal-abuse/", False),
    "akamai": ("Akamai", "abuse@linode.com", "https://www.linode.com/legal-abuse/", False),
    "vultr": ("Vultr", "abuse@constant.com", "https://www.vultr.com/company/contact/", False),
    "constant": ("Vultr / Constant Co", "abuse@constant.com", "https://www.vultr.com/company/contact/", False),
    "choopa": ("Vultr / Constant Co", "abuse@constant.com", "https://www.vultr.com/company/contact/", False),
    "hostinger": ("Hostinger", "abuse@hostinger.com", None, False),
    "bluehost": ("Bluehost (Newfold)", None, "https://newfold.com/abuse", True),
    "newfold": ("Newfold Digital", None, "https://newfold.com/abuse", True),
    "contabo": ("Contabo", "abuse@contabo.com", None, False),
    "leaseweb": ("Leaseweb", "abuse@leaseweb.com", None, False),
    "cloudflare": ("Cloudflare", "abuse@cloudflare.com", "https://abuse.cloudflare.com/phishing", True),
}


def lookup_registrar(registrar_field: Optional[str]) -> Optional[ProviderEntry]:
    if not registrar_field:
        return None
    key = registrar_field.lower()
    for needle, entry in REGISTRARS.items():
        if needle in key:
            return entry
    return None


def lookup_hosting(org_or_asn_field: Optional[str]) -> Optional[ProviderEntry]:
    if not org_or_asn_field:
        return None
    key = org_or_asn_field.lower()
    for needle, entry in HOSTING_PROVIDERS.items():
        if needle in key:
            return entry
    return None


def fallback_abuse_email(domain_or_org: str) -> str:
    """RFC 2142 fallback: abuse@<root-domain> for unknown providers."""
    parts = domain_or_org.lower().strip().split(".")
    if len(parts) >= 2:
        return f"abuse@{'.'.join(parts[-2:])}"
    return f"abuse@{domain_or_org.lower().strip()}"
