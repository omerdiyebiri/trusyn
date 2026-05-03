'use client';

import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { Incident, Brand, Report, ReportStatus } from '@/types';

interface IncidentDetailModalProps {
  incident: Incident;
  brand: Brand | undefined;
  onClose: () => void;
  onUpdated?: () => void;
}

const STATUS_STYLES: Record<ReportStatus, string> = {
  pending: 'bg-gray-700 text-gray-300',
  sent: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
  form_only: 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
  received: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20',
  actioned: 'bg-green-500/10 text-green-400 border border-green-500/20',
  declined: 'bg-orange-500/10 text-orange-400 border border-orange-500/20',
  failed: 'bg-red-500/10 text-red-400 border border-red-500/20',
  pending_review: 'bg-gray-700 text-gray-300',
};

export default function IncidentDetailModal({ incident, brand, onClose, onUpdated }: IncidentDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'evidence' | 'abuse'>('details');
  const [reports, setReports] = useState<Report[]>([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [isReporting, setIsReporting] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [isIgnoring, setIsIgnoring] = useState(false);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [expandedReportId, setExpandedReportId] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoadingReports(true);
    try {
      const res = await api.get(`/incidents/${incident.id}/reports`);
      setReports(res.data);
    } catch {
      setReports([]);
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'abuse') fetchReports();
  }, [activeTab, incident.id]);

  const getConfidenceColor = (score: number) => {
    if (score > 0.8) return 'text-red-500';
    if (score > 0.5) return 'text-yellow-500';
    return 'text-blue-500';
  };

  const reanalyze = async () => {
    setIsReanalyzing(true);
    try {
      await api.post(`/incidents/${incident.id}/reanalyze`);
      alert('Re-analysis started. WHOIS / screenshot / DNS will refresh in ~30 seconds.');
      onUpdated?.();
    } catch {
      alert('Failed to trigger re-analysis.');
    } finally {
      setIsReanalyzing(false);
    }
  };

  const triggerReports = async () => {
    if (!confirm(`Send abuse reports for ${incident.target_url}?\n\nThis will dispatch emails to the applicable Cloudflare / hosting / registrar abuse desks based on WHOIS evidence and queue a Google Safe Browsing audit entry.`)) return;
    setIsReporting(true);
    try {
      await api.post(`/incidents/${incident.id}/report`);
      alert('Abuse reports queued. They will be sent in the background and appear in this list within ~1 minute.');
      setTimeout(fetchReports, 3000);
      onUpdated?.();
    } catch {
      alert('Failed to trigger reports.');
    } finally {
      setIsReporting(false);
    }
  };

  const markStatus = async (status: 'resolved' | 'false_positive') => {
    const label = status === 'resolved' ? 'resolved' : 'false positive';
    if (!confirm(`Mark this incident as ${label}?`)) return;
    if (status === 'resolved') setIsResolving(true);
    else setIsIgnoring(true);
    try {
      await api.patch(`/incidents/${incident.id}`, { status });
      onUpdated?.();
      onClose();
    } catch {
      alert('Failed to update incident.');
    } finally {
      setIsResolving(false);
      setIsIgnoring(false);
    }
  };

  const targetHost = (() => {
    try {
      return new URL(incident.target_url).hostname;
    } catch {
      return incident.target_url;
    }
  })();

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-gray-800 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Incident Analysis</h2>
            <p className="text-gray-400 text-sm font-mono">{incident.target_url}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white" aria-label="Close">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div className="flex border-b border-gray-800 px-6">
          {(['details', 'evidence', 'abuse'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-6 border-b-2 transition-colors capitalize ${
                activeTab === tab ? 'border-blue-500 text-blue-500' : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {activeTab === 'details' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800 p-4 rounded-lg">
                  <span className="text-gray-400 text-xs uppercase font-bold">Status</span>
                  <p className="text-white mt-1 font-semibold uppercase">{incident.status || 'detected'}</p>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg">
                  <span className="text-gray-400 text-xs uppercase font-bold">Threat Type</span>
                  <p className="text-white mt-1 font-semibold">{incident.threat_type || 'pending'}</p>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg">
                  <span className="text-gray-400 text-xs uppercase font-bold">Confidence Score</span>
                  <p className={`text-xl font-bold mt-1 ${getConfidenceColor(incident.confidence_score || 0)}`}>
                    {((incident.confidence_score || 0) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg">
                  <span className="text-gray-400 text-xs uppercase font-bold">Target Host</span>
                  <p className="text-white mt-1 font-mono text-sm">{targetHost}</p>
                </div>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg">
                <span className="text-gray-400 text-xs uppercase font-bold">Targeted Brand</span>
                <p className="text-white mt-1">{brand?.name || 'Unknown'}</p>
                <p className="text-gray-400 text-sm">Official: {brand?.official_domains}</p>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400 text-xs uppercase font-bold">WHOIS Excerpt</span>
                  <button
                    onClick={reanalyze}
                    disabled={isReanalyzing}
                    className="text-xs bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white px-3 py-1 rounded transition-colors"
                  >
                    {isReanalyzing ? 'Re-running…' : 'Re-run Analysis'}
                  </button>
                </div>
                <pre className="text-xs text-green-500 whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {incident.whois_raw || 'No WHOIS data available yet — evidence collection may still be in progress.'}
                </pre>
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <EvidenceTab incident={incident} onUpdated={onUpdated} />
          )}

          {activeTab === 'abuse' && (
            <div className="space-y-4">
              <div className="bg-gray-800 p-4 rounded-lg border border-yellow-900/30">
                <h4 className="text-yellow-500 font-bold text-sm uppercase mb-2">Auto Dispatch</h4>
                <p className="text-gray-300 text-sm mb-4">
                  Determines applicable abuse desks (Cloudflare, hosting, registrar, Google
                  Safe Browsing) from WHOIS / DNS evidence and dispatches templated emails
                  via SMTP. Each report is logged below with status tracking.
                </p>
                {brand?.vekalet_status !== 'approved' && (
                  <div className="mb-4 p-3 rounded border border-yellow-700/40 bg-yellow-900/10 text-yellow-200 text-xs">
                    <strong className="block mb-1">Power of attorney required.</strong>
                    Abuse reports cannot be dispatched until an admin approves
                    the brand’s signed PoA. Current status:{' '}
                    <span className="font-mono">
                      {brand?.vekalet_status || 'not_uploaded'}
                    </span>. Upload a signed PDF on the brand page.
                  </div>
                )}
                <div className="flex gap-3">
                  <button
                    onClick={triggerReports}
                    disabled={isReporting || brand?.vekalet_status !== 'approved'}
                    title={brand?.vekalet_status !== 'approved' ? 'Power of attorney must be approved first' : ''}
                    className="bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-bold transition-all"
                  >
                    {isReporting ? 'Dispatching...' : 'Send Abuse Reports'}
                  </button>
                  <button
                    onClick={fetchReports}
                    disabled={loadingReports}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all"
                  >
                    {loadingReports ? 'Loading...' : 'Refresh'}
                  </button>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                  <h4 className="text-gray-200 font-bold text-sm uppercase">Dispatched Reports</h4>
                </div>
                {reports.length === 0 ? (
                  <div className="p-8 text-center text-gray-500 text-sm">
                    {loadingReports ? 'Loading…' : 'No reports dispatched yet for this incident.'}
                  </div>
                ) : (
                  <div className="divide-y divide-gray-700/60">
                    {reports.map((r) => {
                      const expanded = expandedReportId === r.id;
                      return (
                        <div key={r.id} className="p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-bold uppercase text-gray-300">
                                  {r.recipient_type?.replace('_', ' ')}
                                </span>
                                {r.status && (
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${STATUS_STYLES[r.status] ?? ''}`}>
                                    {r.status.replace('_', ' ')}
                                  </span>
                                )}
                                {r.recipient_name && (
                                  <span className="text-xs text-gray-500">— {r.recipient_name}</span>
                                )}
                              </div>
                              <div className="mt-1 text-xs text-gray-400 font-mono break-all">
                                {r.recipient_email || (r.recipient_form_url ? `form: ${r.recipient_form_url}` : '—')}
                              </div>
                              {r.subject && (
                                <div className="mt-1 text-xs text-gray-300 truncate">{r.subject}</div>
                              )}
                              {r.error_message && (
                                <div className={`mt-1 text-xs italic ${
                                  r.status === 'failed' ? 'text-red-400' : 'text-gray-500'
                                }`}>{r.error_message}</div>
                              )}
                            </div>
                            <div className="text-[10px] text-gray-500 whitespace-nowrap text-right">
                              {r.sent_at && new Date(r.sent_at).toLocaleString()}
                              <button
                                onClick={() => setExpandedReportId(expanded ? null : r.id)}
                                className="block mt-1 text-blue-400 hover:text-blue-300 underline text-[10px]"
                              >
                                {expanded ? 'Hide body' : 'View body'}
                              </button>
                            </div>
                          </div>
                          {expanded && r.raw_content && (
                            <pre className="mt-3 text-xs text-gray-300 bg-gray-900 p-3 rounded overflow-x-auto whitespace-pre-wrap">
                              {r.raw_content}
                            </pre>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-800 flex justify-end gap-3 bg-gray-900/50">
          <button
            onClick={() => markStatus('false_positive')}
            disabled={isIgnoring}
            className="px-6 py-2 rounded-lg border border-gray-700 text-gray-400 hover:bg-gray-800 disabled:opacity-50 transition-colors"
          >
            {isIgnoring ? 'Marking...' : 'False Positive'}
          </button>
          <button
            onClick={() => markStatus('resolved')}
            disabled={isResolving}
            className="px-6 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-bold transition-colors"
          >
            {isResolving ? 'Resolving...' : 'Mark as Resolved'}
          </button>
        </div>
      </div>
    </div>
  );
}


const API_BASE_FOR_IMG =
  process.env.NEXT_PUBLIC_API_URL || 'https://api.trusyn.io/api/v1';

function EvidenceTab({
  incident,
  onUpdated,
}: {
  incident: Incident;
  onUpdated?: () => void;
}) {
  const [refetching, setRefetching] = useState(false);
  const src = incident.screenshot_source;
  const isBlocked = src === 'playwright_blocked';
  const isFallback = src === 'fallback';

  const refetch = async () => {
    if (!confirm('Re-fetch the screenshot via URLScan / PageSpeed cascade?\n\nUseful when Playwright landed on a Cloudflare block page. Takes ~30-60 seconds; refresh after.')) return;
    setRefetching(true);
    try {
      await api.post(`/incidents/${incident.id}/refetch-screenshot`);
      alert('Fallback screenshot retry started. Refresh in ~60 seconds to see the new image.');
      onUpdated?.();
    } catch {
      alert('Retry failed.');
    } finally {
      setRefetching(false);
    }
  };

  const imgUrl = `${API_BASE_FOR_IMG}/public/incidents/${incident.id}/screenshot`;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        {isBlocked && (
          <span className="text-[10px] uppercase font-bold bg-red-500/10 text-red-300 border border-red-500/40 px-2 py-1 rounded">
            Cloudflare block captured
          </span>
        )}
        {isFallback && (
          <span className="text-[10px] uppercase font-bold bg-blue-500/10 text-blue-300 border border-blue-500/40 px-2 py-1 rounded">
            Sourced via fallback (URLScan / PageSpeed)
          </span>
        )}
        {src === 'playwright' && (
          <span className="text-[10px] uppercase font-bold bg-green-500/10 text-green-300 border border-green-500/40 px-2 py-1 rounded">
            Playwright direct capture
          </span>
        )}
        <button
          onClick={refetch}
          disabled={refetching}
          className="ml-auto text-xs bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white px-3 py-1.5 rounded font-bold"
          title="Run URLScan + PageSpeed fallback against this URL and overwrite the screenshot. Useful when CF blocked our scanner."
        >
          {refetching ? 'Retrying…' : 'Re-fetch via fallback'}
        </button>
      </div>

      {incident.screenshot_path ? (
        <a
          href={imgUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="block border border-gray-700 rounded-lg overflow-hidden bg-gray-800 hover:border-blue-500/40 transition-colors"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imgUrl}
            alt={`Screenshot for ${incident.target_url}`}
            className="w-full h-auto"
            loading="lazy"
          />
        </a>
      ) : (
        <div className="py-12 text-gray-500 italic text-center">
          No screenshot captured yet.
        </div>
      )}

      {isBlocked && (
        <div className="text-xs text-yellow-300 bg-yellow-900/10 border border-yellow-700/40 rounded p-3">
          The captured page is a Cloudflare block — our Playwright scan was
          rejected. Click <strong>Re-fetch via fallback</strong> above to try
          URLScan&apos;s capture (different network) and Google PageSpeed
          Insights. If both also fail, the target likely enforces an
          IP-level fence and a Turkish residential proxy is required.
        </div>
      )}
    </div>
  );
}
