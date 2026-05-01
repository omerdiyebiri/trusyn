'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

interface PublicIncident {
  id: string;
  target_url: string;
  defanged_url: string;
  threat_type: string | null;
  status: string | null;
  confidence_band: string;
  confidence_score: number | null;
  discovered_at: string | null;
  brand_name: string | null;
  brand_official_url: string | null;
  has_screenshot: boolean;
  has_whois: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.trusyn.io/api/v1';

const BAND_COLORS: Record<string, string> = {
  HIGH: 'bg-red-500/10 text-red-400 border-red-500/30',
  MEDIUM: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  LOW: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  UNRATED: 'bg-gray-700 text-gray-300 border-gray-600',
};

export default function PublicIncidentPage() {
  const params = useParams();
  const id = (params?.id as string) || '';

  const [data, setData] = useState<PublicIncident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [whoisText, setWhoisText] = useState<string | null>(null);
  const [whoisOpen, setWhoisOpen] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetch(`${API_BASE}/public/incidents/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setData)
      .catch((s) => setError(s === 404 ? 'Incident not found' : 'Failed to load incident'))
      .finally(() => setLoading(false));
  }, [id]);

  const loadWhois = async () => {
    if (!data || whoisText !== null) {
      setWhoisOpen(true);
      return;
    }
    try {
      const r = await fetch(`${API_BASE}/public/incidents/${id}/whois`);
      const t = r.ok ? await r.text() : 'WHOIS not available';
      setWhoisText(t);
      setWhoisOpen(true);
    } catch {
      setWhoisText('WHOIS not available');
      setWhoisOpen(true);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-950 text-gray-400 flex items-center justify-center">
        Loading incident…
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-gray-950 text-gray-300 flex flex-col items-center justify-center p-8">
        <h1 className="text-2xl font-bold mb-2">Incident not found</h1>
        <p className="text-gray-500">The reference you followed does not match an active Trusyn incident.</p>
      </main>
    );
  }

  const bandClass = BAND_COLORS[data.confidence_band] || BAND_COLORS.UNRATED;
  const discovered = data.discovered_at ? new Date(data.discovered_at).toUTCString() : '—';

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <header className="mb-8 pb-6 border-b border-gray-800">
          <div className="text-xs uppercase tracking-widest text-gray-500 mb-2">
            Trusyn Brand Protection — Public Incident Report
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            {data.threat_type === 'typosquatting' ? 'Typosquat / Brand Impersonation'
              : data.threat_type === 'brand_impersonation' ? 'Brand Impersonation'
              : 'Phishing Incident'}
          </h1>
          <div className="text-gray-400 font-mono text-sm break-all">{data.defanged_url}</div>
        </header>

        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-xs uppercase text-gray-500 font-bold">Confidence</div>
            <div className={`mt-2 inline-block px-3 py-1 rounded border text-sm font-bold uppercase ${bandClass}`}>
              {data.confidence_band}
            </div>
            {typeof data.confidence_score === 'number' && (
              <div className="text-xs text-gray-500 mt-2">
                {(data.confidence_score * 100).toFixed(0)}% similarity / match
              </div>
            )}
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-xs uppercase text-gray-500 font-bold">Status</div>
            <div className="text-white font-semibold uppercase mt-2">{data.status || '—'}</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-xs uppercase text-gray-500 font-bold">Discovered</div>
            <div className="text-white text-sm mt-2">{discovered}</div>
          </div>
        </section>

        <section className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-bold text-white mb-3">Targeted Brand</h2>
          <div className="space-y-1 text-sm">
            <div><span className="text-gray-500">Brand:</span> <span className="text-white">{data.brand_name || '—'}</span></div>
            <div><span className="text-gray-500">Legitimate site:</span> <span className="text-white font-mono">{data.brand_official_url || '—'}</span></div>
            <div><span className="text-gray-500">Suspect URL:</span> <span className="text-red-400 font-mono break-all">{data.defanged_url}</span></div>
          </div>
        </section>

        <section className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-bold text-white mb-3">Visual Evidence</h2>
          {data.has_screenshot ? (
            <a
              href={`${API_BASE}/public/incidents/${data.id}/screenshot`}
              target="_blank"
              rel="noreferrer noopener"
              className="block border border-gray-700 rounded overflow-hidden hover:border-blue-500/60 transition-colors"
            >
              <img
                src={`${API_BASE}/public/incidents/${data.id}/screenshot`}
                alt={`Captured page at ${data.defanged_url}`}
                className="w-full h-auto"
                loading="lazy"
              />
            </a>
          ) : (
            <p className="text-gray-500 text-sm italic">Screenshot not yet captured for this incident.</p>
          )}
        </section>

        <section className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold text-white">Registration Record (WHOIS / RDAP)</h2>
            {data.has_whois && (
              <button
                onClick={loadWhois}
                className="text-xs bg-gray-800 hover:bg-gray-700 text-white px-3 py-1 rounded"
              >
                {whoisOpen ? 'Reload' : 'Show'}
              </button>
            )}
          </div>
          {!data.has_whois ? (
            <p className="text-gray-500 text-sm italic">WHOIS not yet collected.</p>
          ) : whoisOpen ? (
            <pre className="text-xs text-green-400 bg-black/40 rounded p-3 overflow-x-auto whitespace-pre-wrap max-h-96">
              {whoisText || 'Loading…'}
            </pre>
          ) : (
            <p className="text-gray-500 text-sm">Hidden — click Show to display.</p>
          )}
        </section>

        <footer className="mt-12 pt-6 border-t border-gray-800 text-xs text-gray-500">
          <div>Incident ID: <span className="font-mono">{data.id}</span></div>
          <div className="mt-1">
            This page is published by Trusyn Brand Protection on behalf of <span className="text-gray-300">{data.brand_name || 'a customer'}</span> as supporting evidence for an abuse report. For correspondence, reply to <a className="text-blue-400 hover:underline" href="mailto:takedowns@trusyn.io">takedowns@trusyn.io</a>.
          </div>
        </footer>
      </div>
    </main>
  );
}
