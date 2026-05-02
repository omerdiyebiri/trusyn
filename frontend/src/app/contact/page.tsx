"use client";

import React, { useState } from "react";
import { PageShell } from "@/components/landing/SiteChrome";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://api.trusyn.io/api/v1";

export default function ContactPage() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    organization: "",
    message: "",
  });
  const [status, setStatus] = useState<"idle" | "submitting" | "ok" | "error">(
    "idle"
  );
  const [errorMsg, setErrorMsg] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    setErrorMsg("");
    try {
      const res = await fetch(`${API_BASE}/public/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          email: form.email.trim(),
          organization: form.organization.trim() || null,
          message: form.message.trim(),
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j?.detail || `HTTP ${res.status}`);
      }
      setStatus("ok");
      setForm({ name: "", email: "", organization: "", message: "" });
    } catch (err: unknown) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Submission failed");
    }
  };

  return (
    <PageShell
      eyebrow="Contact"
      title="Reach the takedowns desk."
      intro="Sales, onboarding, abuse correspondence, and press all flow through the same inbox. Replies are typically same-day during European working hours."
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {status === "ok" ? (
            <SubmittedConfirmation onAgain={() => setStatus("idle")} />
          ) : (
            <form
              onSubmit={submit}
              className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-5"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Name" required>
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 outline-none"
                  />
                </Field>
                <Field label="Email" required>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) =>
                      setForm({ ...form, email: e.target.value })
                    }
                    className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 outline-none"
                  />
                </Field>
              </div>
              <Field label="Organization (optional)">
                <input
                  type="text"
                  value={form.organization}
                  onChange={(e) =>
                    setForm({ ...form, organization: e.target.value })
                  }
                  className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 outline-none"
                />
              </Field>
              <Field label="Message" required>
                <textarea
                  required
                  rows={6}
                  value={form.message}
                  onChange={(e) =>
                    setForm({ ...form, message: e.target.value })
                  }
                  placeholder="Tell us what you need — onboarding, integration, abuse correspondence, press inquiry…"
                  className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 outline-none resize-y"
                />
              </Field>

              {status === "error" && (
                <div className="text-sm text-red-300 border border-red-500/30 bg-red-500/5 rounded-md px-3 py-2">
                  Submission failed: {errorMsg || "please try again."}
                </div>
              )}

              <div className="flex flex-wrap gap-3 items-center">
                <button
                  type="submit"
                  disabled={status === "submitting"}
                  className="bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-bold px-5 py-2.5 rounded-md transition-colors"
                >
                  {status === "submitting" ? "Sending…" : "Send message"}
                </button>
                <p className="text-xs text-gray-500">
                  Rate-limited: max 5 submissions per 15 minutes per IP.
                </p>
              </div>
            </form>
          )}
        </div>

        <aside className="space-y-4">
          <ContactBlock
            title="Takedowns desk"
            mail="takedowns@trusyn.io"
            note="Operational mailbox for outbound abuse correspondence and inbound replies. The same address handles sales and onboarding."
          />
          <ContactBlock
            title="Spam &amp; phishing reports"
            mail="takedowns@trusyn.io"
            cta={{ href: "/report", label: "Use the public form" }}
            note="If you want to report a suspicious URL, the structured form is faster than email."
          />
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
            <div className="text-xs uppercase tracking-widest font-bold text-gray-400 mb-2">
              Mail hygiene
            </div>
            <ul className="text-xs text-gray-500 space-y-1.5 leading-relaxed">
              <li>DKIM signed via Google Workspace</li>
              <li>SPF: trusyn.io with Google &amp; Coolify includes</li>
              <li>DMARC: p=none → progressively to quarantine</li>
              <li>Cloudflare-fronted; abuse routing handled directly</li>
            </ul>
          </div>
        </aside>
      </div>
    </PageShell>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block text-xs uppercase tracking-widest font-bold text-gray-400 mb-1">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </span>
      {children}
    </label>
  );
}

function ContactBlock({
  title,
  mail,
  note,
  cta,
}: {
  title: string;
  mail: string;
  note?: string;
  cta?: { href: string; label: string };
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <div className="text-xs uppercase tracking-widest font-bold text-gray-400 mb-2">
        {title}
      </div>
      <a
        href={`mailto:${mail}`}
        className="block text-blue-400 hover:underline font-mono text-sm break-all"
      >
        {mail}
      </a>
      {note && <p className="text-xs text-gray-500 mt-2 leading-relaxed">{note}</p>}
      {cta && (
        <a
          href={cta.href}
          className="inline-block mt-3 text-xs text-blue-300 hover:text-blue-200"
        >
          {cta.label} →
        </a>
      )}
    </div>
  );
}

function SubmittedConfirmation({ onAgain }: { onAgain: () => void }) {
  return (
    <div className="bg-gray-900 border border-green-500/40 rounded-lg p-8 text-center">
      <div className="inline-block w-12 h-12 rounded-full bg-green-500/10 border border-green-500/40 mb-4 flex items-center justify-center">
        <span className="text-green-300 text-2xl">✓</span>
      </div>
      <h2 className="text-xl font-bold text-white mb-2">Message sent.</h2>
      <p className="text-gray-400 max-w-md mx-auto">
        We received your note and will reply within one business day.
      </p>
      <button
        onClick={onAgain}
        className="mt-6 text-sm text-blue-400 hover:text-blue-300"
      >
        Send another message →
      </button>
    </div>
  );
}
