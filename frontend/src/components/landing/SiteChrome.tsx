import Link from "next/link";
import React from "react";

const NAV_LINKS = [
  { href: "/about",      label: "About" },
  { href: "/advisories", label: "Advisories" },
  { href: "/report",     label: "Report phishing" },
  { href: "/contact",    label: "Contact" },
];

export function SiteNav() {
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
        <div className="flex items-center gap-4 text-sm">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-gray-400 hover:text-white transition-colors hidden md:inline"
            >
              {l.label}
            </Link>
          ))}
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

export function SiteFooter() {
  return (
    <footer className="border-t border-gray-800 bg-gray-950 mt-24">
      <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 sm:grid-cols-4 gap-8 text-sm">
        <div className="col-span-2 sm:col-span-1">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            <span className="font-bold text-gray-200">Trusyn</span>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">
            Automated brand protection — detection, evidence, and takedown
            dispatch.
          </p>
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-gray-500 mb-3">
            Product
          </div>
          <ul className="space-y-2 text-gray-400">
            <li><Link href="/about" className="hover:text-white">About</Link></li>
            <li><Link href="/advisories" className="hover:text-white">Advisories</Link></li>
            <li><Link href="/login" className="hover:text-white">Sign in</Link></li>
          </ul>
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-gray-500 mb-3">
            Public
          </div>
          <ul className="space-y-2 text-gray-400">
            <li><Link href="/report" className="hover:text-white">Report phishing</Link></li>
            <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
          </ul>
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-gray-500 mb-3">
            Reach us
          </div>
          <ul className="space-y-2 text-gray-400">
            <li>
              <a href="mailto:takedowns@trusyn.io" className="hover:text-white break-all">
                takedowns@trusyn.io
              </a>
            </li>
            <li className="text-xs text-gray-600">
              DKIM + SPF + DMARC aligned
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6 py-4 flex flex-col sm:flex-row justify-between gap-2 text-xs text-gray-600">
          <div>© {new Date().getFullYear()} Trusyn · trusyn.io</div>
          <div>Operated from Türkiye · Cloudflare-fronted</div>
        </div>
      </div>
    </footer>
  );
}

export function PageShell({
  eyebrow,
  title,
  intro,
  children,
}: {
  eyebrow?: string;
  title: string;
  intro?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <SiteNav />
      <main className="flex-1">
        <header className="border-b border-gray-800 bg-gradient-to-b from-gray-900/40 to-transparent">
          <div className="max-w-4xl mx-auto px-6 pt-16 pb-12">
            {eyebrow && (
              <div className="text-xs uppercase tracking-widest text-blue-400 mb-3">
                {eyebrow}
              </div>
            )}
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
              {title}
            </h1>
            {intro && (
              <p className="mt-4 text-lg text-gray-400 leading-relaxed max-w-2xl">
                {intro}
              </p>
            )}
          </div>
        </header>
        <div className="max-w-4xl mx-auto px-6 py-12">{children}</div>
      </main>
      <SiteFooter />
    </div>
  );
}
