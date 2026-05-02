import { PageShell } from "@/components/landing/SiteChrome";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Advisories — Trusyn",
  description:
    "Recent phishing trends, kit teardowns, and brand-impersonation patterns observed by the Trusyn detection pipeline.",
};

type Advisory = {
  id: string;
  date: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  title: string;
  summary: string;
  body: string[];
};

const ADVISORIES: Advisory[] = [
  {
    id: "TRY-2026-04",
    date: "2026-04-22",
    severity: "HIGH",
    title: "Mobile-only Turkish banking kits gating on geo + UA",
    summary:
      "A wave of credential-harvesting pages impersonating Turkish retail banks now serves the live phishing UI only to mobile Chrome User-Agents resolving from Turkish IPs; everyone else gets a Cloudflare challenge or an empty page.",
    body: [
      "Kits are deploying multi-stage gating to defeat reputation scanners. The first hop is a Cloudflare-fronted domain that returns a managed challenge to anything that does not match `Mozilla/5.0 (Linux; Android …) Chrome` with `Accept-Language: tr-TR` and a Turkish residential ASN.",
      "Trusyn's scanner emulates the geo and UA profile and clears the JavaScript challenge in most cases. Sites that additionally enforce ASN-level fences (only TR residential IPs) require a downstream proxy.",
      "Operators should expect that desktop-based abuse-desk reviewers may load the URL and see a clean page or a 1015 block — full-page screenshots are now a mandatory part of the evidence bundle, not an optional extra.",
    ],
  },
  {
    id: "TRY-2026-04-02",
    date: "2026-04-09",
    severity: "MEDIUM",
    title: "Typosquat campaigns favoring `.online` and `.live` TLDs",
    summary:
      "Bulk-registered typosquats for major fintech brands have shifted from `.com`/`.net` to cheaper `.online` and `.live` TLDs where WHOIS proxy services are aggressive and registrars are slower to enforce DNS-abuse policy.",
    body: [
      "Across Trusyn's CertStream feed in March-April 2026, 41% of new typosquat detections involve `.online`, `.live`, `.shop`, or `.top`. Most come from a small number of registrars; abuse contact discovery via python-whois often returns empty, requiring an RDAP fallback (which we apply).",
      "We are observing that registrars in this category respond materially faster when the abuse mail explicitly cites ICANN RAA §3.18 (5 April 2024) by name and attaches a power of attorney. Trusyn templates do both.",
    ],
  },
  {
    id: "TRY-2026-03",
    date: "2026-03-28",
    severity: "HIGH",
    title: "OAuth consent-phishing kits impersonating Microsoft 365",
    summary:
      "OAuth consent phishing has resurged, with kits hosted on `*.workers.dev` and `*.pages.dev` subdomains harvesting tokens via legitimate-looking app consent prompts.",
    body: [
      "Because the credential exchange happens at the genuine Microsoft endpoint, traditional URL reputation systems often miss these flows. The actionable signal is the malicious app's redirect URI, not the visible domain.",
      "Trusyn flags any newly-issued certificate matching a customer brand on Cloudflare developer-platform domains as HIGH-confidence regardless of visual similarity, because the deployment pattern itself is anomalous.",
      "Cloudflare's abuse form is the highest-leverage channel here; the registrar path is irrelevant for Workers/Pages subdomains.",
    ],
  },
  {
    id: "TRY-2026-03-02",
    date: "2026-03-14",
    severity: "MEDIUM",
    title: "Abuse-desk inbox discipline: Message-IDs as receipts",
    summary:
      "Multiple registrars and hosting providers now silently drop abuse messages that fail RFC 5322 hygiene checks. Missing or duplicate Message-IDs are the most common culprit.",
    body: [
      "Operators self-rolling abuse mailers should ensure every message generates a unique RFC 2822 Message-ID, sets `Auto-Submitted: auto-generated`, and uses `Precedence: bulk`. Without these, large providers fast-path the mail into spam triage rather than the abuse queue.",
      "Trusyn includes all of the above plus `X-Trusyn-Incident-ID` headers so reply matching and IMAP-side classification work without natural-language parsing.",
    ],
  },
  {
    id: "TRY-2026-02",
    date: "2026-02-19",
    severity: "LOW",
    title: "Smishing via shortened branded URLs in SMS PDU",
    summary:
      "Carrier SMS abuse tooling continues to ignore links delivered through URL shorteners that appear to belong to the targeted brand (e.g. `bit.ly/<brand>-acc`).",
    body: [
      "These are not phishing in the strict sense — the shortener is genuine — but the destination is a credential-harvesting page hosted under a typosquat. Operators should treat the destination URL as the IOC, not the shortener.",
      "Trusyn submits the destination to URLScan.io and ThreatFox at detection time so that downstream feeds (browser blockers, secure-email-gateway products) can act on the pattern even before the registrar processes our notice.",
    ],
  },
];

const SEV_BADGE: Record<Advisory["severity"], string> = {
  HIGH: "bg-red-500/10 text-red-300 border-red-500/40",
  MEDIUM: "bg-yellow-500/10 text-yellow-300 border-yellow-500/40",
  LOW: "bg-blue-500/10 text-blue-300 border-blue-500/40",
};

export default function AdvisoriesPage() {
  return (
    <PageShell
      eyebrow="Trusyn Threat Lab"
      title="Phishing advisories &amp; trend writeups."
      intro="Field notes from the detection pipeline. Patterns we are seeing across customer brands, dispatched in plain English so operations and legal can act on them."
    >
      <div className="space-y-6">
        {ADVISORIES.map((a) => (
          <article
            key={a.id}
            className="bg-gray-900 border border-gray-800 rounded-lg p-6 hover:border-gray-600 transition-colors"
          >
            <div className="flex flex-wrap items-center gap-3 mb-3 text-xs">
              <span className={`uppercase font-bold border px-2 py-0.5 rounded ${SEV_BADGE[a.severity]}`}>
                {a.severity}
              </span>
              <span className="font-mono text-gray-500">{a.id}</span>
              <span className="text-gray-500">{a.date}</span>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">{a.title}</h2>
            <p className="text-gray-400 italic mb-4">{a.summary}</p>
            <div className="space-y-3 text-sm text-gray-300 leading-relaxed">
              {a.body.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="mt-12 p-6 border border-dashed border-gray-700 rounded-lg text-sm text-gray-400">
        Want advisories tailored to your brand&apos;s exposure?
        Customers see all detections in their dashboard with confidence
        bands and dispatched-report status.{" "}
        <a href="mailto:takedowns@trusyn.io" className="text-blue-400 hover:underline">
          Get in touch
        </a>{" "}
        to start onboarding.
      </div>
    </PageShell>
  );
}
