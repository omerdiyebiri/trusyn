'use client';

import React, { useState } from 'react';
import { Incident, Brand } from '@/types';

interface IncidentDetailModalProps {
  incident: Incident;
  brand: Brand | undefined;
  onClose: () => void;
}

export default function IncidentDetailModal({ incident, brand, onClose }: IncidentDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'evidence' | 'abuse'>('details');

  const getConfidenceColor = (score: number) => {
    if (score > 0.8) return 'text-red-500';
    if (score > 0.5) return 'text-yellow-500';
    return 'text-blue-500';
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-800 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Incident Analysis</h2>
            <p className="text-gray-400 text-sm">{incident.target_url}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Tabs */}
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

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {activeTab === 'details' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800 p-4 rounded-lg">
                  <span className="text-gray-400 text-xs uppercase font-bold">Threat Type</span>
                  <p className="text-white mt-1 font-semibold">{incident.threat_type || 'PENDING'}</p>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg">
                  <span className="text-gray-400 text-xs uppercase font-bold">Confidence Score</span>
                  <p className={`text-xl font-bold mt-1 ${getConfidenceColor(incident.confidence_score || 0)}`}>
                    {((incident.confidence_score || 0) * 100).toFixed(1)}%
                  </p>
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
                  {incident.whois_raw || 'No WHOIS data available'}
                </pre>
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <div className="space-y-4 text-center">
              {incident.screenshot_path ? (
                <div className="border border-gray-700 rounded-lg overflow-hidden">
                  {/* Note: In a real app, this would be an actual URL from an image server */}
                  <div className="bg-gray-800 py-12 text-gray-400">
                    <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                    Screenshot stored at:<br/>
                    <code className="text-xs">{incident.screenshot_path}</code>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-gray-500 italic">No screenshot captured yet.</div>
              )}
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors">
                View Full DOM Snapshot
              </button>
            </div>
          )}

          {activeTab === 'abuse' && (
            <div className="space-y-4">
              <div className="bg-gray-800 p-4 rounded-lg border border-yellow-900/30">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-yellow-500 font-bold text-sm uppercase">Auto-Generated Report (Registrar)</h4>
                  <button className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded">Copy</button>
                </div>
                <div className="text-xs text-gray-300 font-mono space-y-2">
                  <p><strong>Subject:</strong> Urgent: Phishing Infrastructure Notification - {incident.target_url.split('/')[2]} - {brand?.name}</p>
                  <hr className="border-gray-700" />
                  <p>To the Abuse Department...</p>
                  <p>This is a formal notification regarding a domain used for Phishing...</p>
                  <p>Requested Action: Immediate suspension...</p>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                <button className="bg-gray-700 hover:bg-gray-600 text-white text-xs py-2 rounded">Cloudflare Report</button>
                <button className="bg-gray-700 hover:bg-gray-600 text-white text-xs py-2 rounded">Hosting Report</button>
                <button className="bg-gray-700 hover:bg-gray-600 text-white text-xs py-2 rounded">DMCA Request</button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-gray-800 flex justify-end gap-3 bg-gray-900/50">
          <button className="px-6 py-2 rounded-lg border border-gray-700 text-gray-400 hover:bg-gray-800 transition-colors">Ignore</button>
          <button className="px-6 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white font-bold transition-colors">Mark as Resolved</button>
        </div>
      </div>
    </div>
  );
}
