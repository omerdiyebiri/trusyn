'use client';

import React, { useState } from 'react';
import api from '@/services/api';
import { Incident, Brand } from '@/types';

interface IncidentDetailModalProps {
  incident: Incident;
  brand: Brand | undefined;
  onClose: () => void;
  onUpdated?: () => void;
}

export default function IncidentDetailModal({ incident, brand, onClose, onUpdated }: IncidentDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'evidence' | 'abuse'>('details');
  const [isReporting, setIsReporting] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [isIgnoring, setIsIgnoring] = useState(false);

  const getConfidenceColor = (score: number) => {
    if (score > 0.8) return 'text-red-500';
    if (score > 0.5) return 'text-yellow-500';
    return 'text-blue-500';
  };

  const triggerReports = async () => {
    if (!confirm(`Send abuse reports for ${incident.target_url}?\n\nThis will dispatch emails to Cloudflare/hosting/registrar abuse desks based on WHOIS evidence.`)) return;
    setIsReporting(true);
    try {
      await api.post(`/incidents/${incident.id}/report`);
      alert('Abuse reports queued. They will be sent in the background.');
      onUpdated?.();
    } catch (err) {
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
    } catch (err) {
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
                <span className="text-gray-400 text-xs uppercase font-bold">WHOIS Excerpt</span>
                <pre className="text-xs text-green-500 mt-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {incident.whois_raw || 'No WHOIS data available yet — evidence collection may still be in progress.'}
                </pre>
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <div className="space-y-4 text-center">
              {incident.screenshot_path ? (
                <div className="border border-gray-700 rounded-lg overflow-hidden bg-gray-800 py-12 text-gray-400">
                  <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                  Screenshot captured at:<br/>
                  <code className="text-xs">{incident.screenshot_path}</code>
                </div>
              ) : (
                <div className="py-12 text-gray-500 italic">No screenshot captured yet.</div>
              )}
            </div>
          )}

          {activeTab === 'abuse' && (
            <div className="space-y-4">
              <div className="bg-gray-800 p-4 rounded-lg border border-yellow-900/30">
                <h4 className="text-yellow-500 font-bold text-sm uppercase mb-2">Auto Dispatch</h4>
                <p className="text-gray-300 text-sm mb-4">
                  When triggered, the backend will determine the applicable abuse desks (Cloudflare,
                  hosting provider, registrar, Google DMCA) from WHOIS/DNS evidence and dispatch
                  templated emails via SMTP. Each report is logged with status tracking.
                </p>
                <button
                  onClick={triggerReports}
                  disabled={isReporting}
                  className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all"
                >
                  {isReporting ? 'Dispatching...' : 'Send Abuse Reports'}
                </button>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg">
                <h4 className="text-gray-400 font-bold text-xs uppercase mb-2">Subject Preview</h4>
                <p className="text-xs text-gray-300 font-mono">
                  Urgent: Phishing/Brand Impersonation Notification — {targetHost} — {brand?.name}
                </p>
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
