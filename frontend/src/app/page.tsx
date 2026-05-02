import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Nav />
      <Hero />
      <Stats />
      <Pipeline />
      <Channels />
      <Compliance />
      <CTA />
      <Footer />
    </div>
  );
}

function Nav() {
  return (
    <nav className="sticky top-0 z-40 backdrop-blur bg-gray-950/80 border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.8)]" />
          <span className="font-bold tracking-tight">Trusyn</span>
          <span className="text-gray-500 text-xs uppercase tracking-widest hidden sm:inline">
            Brand Protection
          </span>
        </Link>
        <div className="flex items-center gap-3 text-sm">
          <a
            href="#how-it-works"
            className="text-gray-400 hover:text-white transition-colors hidden sm:inline"
          >
            How it works
          </a>
          <a
            href="#channels"
            className="text-gray-400 hover:text-white transition-colors hidden sm:inline"
          >
            Channels
          </a>
          <Link
            href="/login"
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-1.5 rounded-md transition-colors"
          >
            Sign in
          </Link>
        </div>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="absolute inset-0 -z-10 opacity-[0.18] [background:radial-gradient(60%_80%_at_50%_0%,rgba(59,130,246,0.6),transparent_60%)]"
      />
      <div className="max-w-6xl mx-auto px-6 pt-24 pb-20 sm:pt-32 sm:pb-28">
        <div className="inline-flex items-center gap-2 text-xs uppercase tracking-widest text-blue-400 border border-blue-500/30 bg-blue-500/5 px-3 py-1 rounded-full mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          Live phishing intel — CertStream + RDAP + URLScan
        </div>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight leading-[1.05] max-w-4xl">
          Brand protection that{" "}
          <span className="text-blue-400">actually moves</span> takedowns.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-gray-400 leading-relaxed">
          Trusyn detects phishing kits and typosquats targeting your brand the
          moment a certificate is issued, gathers court-grade evidence, and
          dispatches RFC-compliant abuse reports to the registrar, hosting
          provider, and reputation systems — automatically.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row gap-3">
          <Link
            href="/login"
            className="inline-flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white font-bold px-6 py-3 rounded-lg transition-colors"
          >
            Sign in to dashboard
          </Link>
          <a
            href="mailto:takedowns@trusyn.io?subject=Trusyn%20demo%20request"
            className="inline-flex items-center justify-center border border-gray-700 hover:border-gray-500 hover:bg-gray-900 text-white font-bold px-6 py-3 rounded-lg transition-colors"
          >
            Request a demo
          </a>
        </div>
        <p className="mt-6 text-xs text-gray-600 font-mono">
          takedowns@trusyn.io · DKIM + SPF + DMARC aligned · Cloudflare-fronted
        </p>
      </div>
    </section>
  );
}

function Stats() {
  const items = [
    { k: "<60s", v: "From CertStream issuance to first scan" },
    { k: "5+", v: "Parallel abuse channels per incident" },
    { k: "RFC 5322", v: "Mail headers · Message-ID · auto-submitted" },
    { k: "RAA §3.18", v: "Registrar DNS-abuse compliance baked in" },
  ];
  return (
    <section className="border-y border-gray-800 bg-gray-900/40">
      <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-2 sm:grid-cols-4 gap-6">
        {items.map((i) => (
          <div key={i.k}>
            <div className="text-2xl sm:text-3xl font-bold text-white">
              {i.k}
            </div>
            <div className="text-xs text-gray-500 mt-1 leading-relaxed">
              {i.v}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Pipeline() {
  const steps = [
    {
      n: "01",
      t: "Detect",
      d: "We watch CertStream and DNS feeds for newly-issued certificates whose hostnames look like your brand — typosquats, homoglyphs, brand keywords.",
    },
    {
      n: "02",
      t: "Validate",
      d: "Headless Chromium opens the page from a Turkish-locale mobile profile, captures a full-page screenshot + DOM, resolves origin IP through Cloudflare, runs RDAP against the registrar.",
    },
    {
      n: "03",
      t: "Score",
      d: "Visual similarity, brand-asset hits, login-form heuristics and Levenshtein distance combine into a HIGH / MEDIUM / LOW confidence band.",
    },
    {
      n: "04",
      t: "Dispatch",
      d: "Templated RFC-compliant abuse mails go to hosting + registrar + Cloudflare; intel platforms (URLScan, ThreatFox, SmartScreen, Safe Browsing) get parallel submissions.",
    },
    {
      n: "05",
      t: "Track",
      d: "An IMAP poller classifies replies (ACTIONED / DECLINED / BOUNCE) by token. Status surfaces in the dashboard and the public incident page.",
    },
  ];
  return (
    <section id="how-it-works" className="max-w-6xl mx-auto px-6 py-24">
      <div className="text-xs uppercase tracking-widest text-blue-400 mb-3">
        Pipeline
      </div>
      <h2 className="text-3xl sm:text-4xl font-bold tracking-tight max-w-2xl">
        From certificate issuance to registrar suspension — autonomously.
      </h2>
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {steps.map((s) => (
          <div
            key={s.n}
            className="bg-gray-900 border border-gray-800 rounded-lg p-5 hover:border-blue-500/40 transition-colors"
          >
            <div className="text-xs font-mono text-blue-400 mb-3">{s.n}</div>
            <div className="font-bold text-white text-lg mb-2">{s.t}</div>
            <p className="text-sm text-gray-400 leading-relaxed">{s.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Channels() {
  const groups = [
    {
      title: "Hosting & DNS",
      items: [
        "Cloudflare Trust & Safety",
        "Registrar abuse desks (RAA §3.18)",
        "Hosting provider abuse contacts via IP RDAP",
      ],
    },
    {
      title: "Reputation systems",
      items: [
        "Google Safe Browsing",
        "Microsoft Defender SmartScreen",
        "URLScan.io public verification",
        "abuse.ch ThreatFox IOC feed",
      ],
    },
    {
      title: "Evidence shipped",
      items: [
        "Full-page screenshot (PNG)",
        "DOM snapshot at detection",
        "WHOIS / RDAP record",
        "Public, auth-free incident page",
      ],
    },
  ];
  return (
    <section
      id="channels"
      className="border-t border-gray-800 bg-gray-900/40"
    >
      <div className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-xs uppercase tracking-widest text-blue-400 mb-3">
          Coverage
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight max-w-2xl mb-12">
          One detection — five+ parallel pressure points.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {groups.map((g) => (
            <div
              key={g.title}
              className="bg-gray-950 border border-gray-800 rounded-lg p-6"
            >
              <div className="font-bold text-white mb-4">{g.title}</div>
              <ul className="space-y-2 text-sm text-gray-400">
                {g.items.map((it) => (
                  <li key={it} className="flex gap-2">
                    <span className="text-blue-400 mt-0.5">›</span>
                    <span>{it}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Compliance() {
  const items = [
    {
      t: "ICANN RAA §3.18",
      d: "Registrar abuse mails cite the 5 April 2024 DNS-abuse amendment by name.",
    },
    {
      t: "Power of attorney gating",
      d: "No abuse mail leaves the queue until a signed PoA is approved, and recipients can fetch it from the message body.",
    },
    {
      t: "RFC 5322 hygiene",
      d: "Message-ID, Precedence: bulk, Auto-Submitted, X-Trusyn-* tracking. DKIM-signed via Google Workspace.",
    },
    {
      t: "Multi-tenant isolation",
      d: "Brands, incidents, and reports never cross a tenant boundary. Public pages expose only the fields already in the abuse mail.",
    },
  ];
  return (
    <section className="max-w-6xl mx-auto px-6 py-24">
      <div className="text-xs uppercase tracking-widest text-blue-400 mb-3">
        Compliance
      </div>
      <h2 className="text-3xl sm:text-4xl font-bold tracking-tight max-w-2xl mb-12">
        Built so abuse desks don&apos;t reject the mail on first read.
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {items.map((i) => (
          <div
            key={i.t}
            className="bg-gray-900 border border-gray-800 rounded-lg p-5"
          >
            <div className="font-bold text-white mb-1">{i.t}</div>
            <p className="text-sm text-gray-400 leading-relaxed">{i.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="border-t border-gray-800">
      <div className="max-w-4xl mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Ready to stop chasing phishing kits by hand?
        </h2>
        <p className="mt-4 text-gray-400 max-w-xl mx-auto">
          Onboarding is one signed power-of-attorney away. Reach out and
          we&apos;ll wire your brand into the detection pipeline within a day.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <a
            href="mailto:takedowns@trusyn.io?subject=Trusyn%20onboarding"
            className="inline-flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white font-bold px-6 py-3 rounded-lg transition-colors"
          >
            takedowns@trusyn.io
          </a>
          <Link
            href="/login"
            className="inline-flex items-center justify-center border border-gray-700 hover:border-gray-500 hover:bg-gray-900 text-white font-bold px-6 py-3 rounded-lg transition-colors"
          >
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-gray-800 bg-gray-950">
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row gap-4 justify-between text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
          <span className="font-bold text-gray-300">Trusyn</span>
          <span>· Brand Protection · trusyn.io</span>
        </div>
        <div className="flex gap-4">
          <a
            href="mailto:takedowns@trusyn.io"
            className="hover:text-gray-300"
          >
            takedowns@trusyn.io
          </a>
          <Link href="/login" className="hover:text-gray-300">
            Sign in
          </Link>
        </div>
      </div>
    </footer>
  );
}
