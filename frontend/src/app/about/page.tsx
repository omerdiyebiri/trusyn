import { PageShell } from "@/components/landing/SiteChrome";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — Trusyn",
  description:
    "Trusyn is an automated brand-protection platform: we detect phishing kits and typosquats targeting our customers, gather evidence, and dispatch RFC-compliant abuse reports.",
};

export default function AboutPage() {
  return (
    <PageShell
      eyebrow="About Trusyn"
      title="A takedown engine, not another dashboard."
      intro="Trusyn was built around a single observation: brand-protection vendors are good at finding phishing pages, but bad at actually shutting them down. We invert that priority."
    >
      <div className="space-y-12 text-gray-300 leading-relaxed">
        <section>
          <h2 className="text-xl font-bold text-white mb-3">The problem</h2>
          <p>
            Phishing kits live for hours, not weeks. By the time a SOC team
            triages a Slack alert, copies the URL into a registrar form,
            attaches a screenshot, and chases a reply, the kit has already
            harvested credentials from thousands of victims and rotated to a
            new domain. Most &ldquo;brand protection&rdquo; products stop at
            detection — leaving the slow, manual, deadline-sensitive part to
            their customers.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-3">Our approach</h2>
          <p>
            Trusyn collapses the loop. The moment a certificate is issued for
            a hostname that pattern-matches a customer brand, our pipeline
            opens it from a Turkish-locale mobile profile, captures
            full-page screenshot + DOM, resolves the origin IP through any
            Cloudflare proxy, runs RDAP against the registrar, and parallel-
            dispatches templated abuse mails to hosting + registrar +
            Cloudflare alongside submissions to URLScan.io, abuse.ch
            ThreatFox, Microsoft Defender SmartScreen, and Google Safe
            Browsing.
          </p>
          <p className="mt-3">
            Every mail cites the relevant compliance vehicle — ICANN RAA
            §3.18 for registrars, AUP language for hosts — and ships with
            attached evidence. A linked public incident page lets the abuse
            desk verify our submission without a Trusyn login. A signed
            power-of-attorney from the brand owner is required and gated
            before any mail leaves the queue.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-3">Operating posture</h2>
          <ul className="space-y-2 text-gray-400">
            <li className="flex gap-2"><span className="text-blue-400">›</span><span>Operated from Türkiye, with localized detection profiles for region-fenced phishing kits.</span></li>
            <li className="flex gap-2"><span className="text-blue-400">›</span><span>SMTP fronted by Google Workspace with full DKIM + SPF + DMARC alignment so abuse mail lands in the inbox, not the spam folder.</span></li>
            <li className="flex gap-2"><span className="text-blue-400">›</span><span>Multi-tenant by design — brand, incident, and report data never crosses customer boundaries.</span></li>
            <li className="flex gap-2"><span className="text-blue-400">›</span><span>Public incident pages mirror the Netcraft pattern: sanitized, auth-free, URL-shareable evidence for recipients.</span></li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-3">Who we work with</h2>
          <p>
            Banks, fintechs, betting platforms, and any consumer brand whose
            customers are routinely funneled into credential-harvesting kits
            via SMS, paid ads, or messenger spam. If your fraud loss line
            item is correlated with a typosquat domain, talk to us.
          </p>
          <div className="mt-6">
            <a
              href="mailto:takedowns@trusyn.io?subject=Trusyn%20onboarding"
              className="inline-flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white font-bold px-6 py-3 rounded-lg transition-colors"
            >
              takedowns@trusyn.io
            </a>
          </div>
        </section>
      </div>
    </PageShell>
  );
}
