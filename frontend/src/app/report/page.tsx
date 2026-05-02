"use client";

import React, { useState } from "react";
import { PageShell } from "@/components/landing/SiteChrome";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://api.trusyn.io/api/v1";

export default function ReportPage() {
  const [form, setForm] = useState({
    suspicious_url: "",
    impersonated_brand: "",
    reporter_email: "",
    notes: "",
  });
  const [status, setStatus] = useState<
    "idle" | "submitting" | "ok" | "error"
  >("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    setErrorMsg("");
    try {
      const res = await fetch(`${API_BASE}/public/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          suspicious_url: form.suspicious_url.trim(),
          impersonated_brand: form.impersonated_brand.trim() || null,
          reporter_email: form.reporter_email.trim() || null,
          notes: form.notes.trim() || null,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j?.detail || `HTTP ${res.status}`);
      }
      setStatus("ok");
      setForm({
        suspicious_url: "",
        impersonated_brand: "",
        reporter_email: "",
        notes: "",
      });
    } catch (err: unknown) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Submission failed");
    }
  };

  return (
    <PageShell
      eyebrow="Public submission"
      title="Report a phishing or spam URL."
      intro="Anyone can report a suspicious URL here. We forward submissions to the Trusyn takedowns inbox and, where the URL impersonates one of our customers, queue it for the dispatch pipeline."
    >
      {status === "ok" ? (
        <SubmittedConfirmation onAgain={() => setStatus("idle")} />
      ) : (
        <form
          onSubmit={submit}
          className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-5"
        >
          <Field
            label="Suspicious URL"
            required
            hint="The full link as you received it. We accept defanged forms (hxxps, [.])."
          >
            <input
              type="text"
              required
              value={form.suspicious_url}
              onChange={(e) =>
                setForm({ ...form, suspicious_url: e.target.value })
              }
              placeholder="https://example-login.tld/secure"
              className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 outline-none font-mono text-sm"
            />
          </Field>

          <Field
            label="Impersonated brand (optional)"
            hint="Bank, fintech, e-commerce site, etc."
          >
            <input
              type="text"
              value={form.impersonated_brand}
              onChange={(e) =>
                setForm({ ...form, impersonated_brand: e.target.value })
              }
              placeholder="e.g. Garanti BBVA"
              className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 outline-none"
            />
          </Field>

          <Field
            label="Your email (optional)"
            hint="Provide if you want a follow-up. Submissions can be anonymous."
          >
            <input
              type="email"
              value={form.reporter_email}
              onChange={(e) =>
                setForm({ ...form, reporter_email: e.target.value })
              }
              placeholder="you@example.com"
              className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-white placeholder-gray-600 focus:border-blue-500 outline-none"
            />
          </Field>

          <Field
            label="Notes (optional)"
            hint="How you received the link, any context that helps triage."
          >
            <textarea
              rows={4}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Received via SMS this morning, claimed to be a bank security alert…"
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
              {status === "submitting" ? "Submitting…" : "Submit report"}
            </button>
            <p className="text-xs text-gray-500">
              Rate-limited: max 5 submissions per 15 minutes per IP.
            </p>
          </div>
        </form>
      )}

      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Note
          title="What happens to your report"
          body="Our automation forwards the URL into the Trusyn detection pipeline. If it impersonates one of our customer brands, abuse mails to the registrar and host go out automatically. Otherwise it lands in the takedowns@ inbox for manual triage."
        />
        <Note
          title="What we do not do"
          body="We don't pursue takedowns for brands that are not Trusyn customers. We do log indicators to URLScan.io and abuse.ch ThreatFox so the wider security community can act on them."
        />
      </div>
    </PageShell>
  );
}

function Field({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
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
      {hint && <span className="block text-xs text-gray-500 mt-1">{hint}</span>}
    </label>
  );
}

function Note({ title, body }: { title: string; body: string }) {
  return (
    <div className="bg-gray-950 border border-gray-800 rounded-lg p-4">
      <div className="font-bold text-white text-sm mb-1">{title}</div>
      <p className="text-xs text-gray-400 leading-relaxed">{body}</p>
    </div>
  );
}

function SubmittedConfirmation({ onAgain }: { onAgain: () => void }) {
  return (
    <div className="bg-gray-900 border border-green-500/40 rounded-lg p-8 text-center">
      <div className="inline-block w-12 h-12 rounded-full bg-green-500/10 border border-green-500/40 mb-4 flex items-center justify-center">
        <span className="text-green-300 text-2xl">✓</span>
      </div>
      <h2 className="text-xl font-bold text-white mb-2">Report received.</h2>
      <p className="text-gray-400 max-w-md mx-auto">
        Thanks. We&apos;ll route it through the takedowns inbox and follow up
        on actionable submissions where you provided an email.
      </p>
      <button
        onClick={onAgain}
        className="mt-6 text-sm text-blue-400 hover:text-blue-300"
      >
        Submit another report →
      </button>
    </div>
  );
}
