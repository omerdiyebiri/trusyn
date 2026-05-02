'use client';

import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';
import { Brand } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.trusyn.io/api/v1';

export default function VekaletReviewPage() {
  const { user } = useAuth();
  const [pending, setPending] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [previewBrand, setPreviewBrand] = useState<Brand | null>(null);

  useEffect(() => {
    if (user && user.role === 'super_admin') fetchPending();
  }, [user]);

  const fetchPending = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/vekalet/pending');
      setPending(res.data);
    } catch {
      setPending([]);
    } finally {
      setLoading(false);
    }
  };

  const approve = async (brand: Brand) => {
    if (!confirm(`Approve power-of-attorney for ${brand.name}?`)) return;
    setBusyId(brand.id);
    try {
      await api.post(`/admin/brands/${brand.id}/vekalet/approve`);
      await fetchPending();
    } catch {
      alert('Approve failed.');
    } finally {
      setBusyId(null);
    }
  };

  const reject = async (brand: Brand) => {
    const reason = prompt(`Reject reason for ${brand.name}:`, '');
    if (reason === null) return;
    setBusyId(brand.id);
    try {
      await api.post(`/admin/brands/${brand.id}/vekalet/reject`, { reason });
      await fetchPending();
    } catch {
      alert('Reject failed.');
    } finally {
      setBusyId(null);
    }
  };

  const downloadUrl = (brand: Brand) =>
    `${API_BASE}/admin/brands/${brand.id}/vekalet/file`;

  if (user && user.role !== 'super_admin') {
    return (
      <div className="p-8 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300">
        Forbidden — super-admin role required.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Vekalet Review Queue</h1>
          <p className="text-gray-400 text-sm">
            Power-of-attorney documents awaiting approval. No abuse mail goes out
            until the brand has an approved PoA on file.
          </p>
        </div>
        <button
          onClick={fetchPending}
          className="text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 px-3 py-1.5 rounded-md font-bold"
        >
          Refresh
        </button>
      </div>

      <div className="bg-gray-800/30 border border-gray-700 rounded-xl overflow-hidden">
        {loading ? (
          <div className="text-gray-500 py-12 text-center">Loading…</div>
        ) : pending.length === 0 ? (
          <div className="text-gray-500 py-12 text-center">
            Inbox zero — no pending power-of-attorney reviews.
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-900/50 text-[10px] uppercase tracking-widest text-gray-400">
              <tr>
                <th className="px-4 py-3">Brand</th>
                <th className="px-4 py-3">Tenant</th>
                <th className="px-4 py-3">Uploaded</th>
                <th className="px-4 py-3">Document</th>
                <th className="px-4 py-3 text-right">Decision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {pending.map((b) => (
                <tr key={b.id} className="hover:bg-gray-700/20">
                  <td className="px-4 py-3 text-white font-medium">{b.name}</td>
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">{(b as Brand & { tenant_id?: string }).tenant_id || '—'}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {b.vekalet_uploaded_at ? new Date(b.vekalet_uploaded_at).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setPreviewBrand(b)}
                      className="text-xs bg-blue-600/10 hover:bg-blue-600 hover:text-white text-blue-400 border border-blue-600/20 px-2 py-1 rounded"
                    >
                      Preview PDF
                    </button>{' '}
                    <a
                      href={downloadUrl(b)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-gray-400 hover:text-white ml-2"
                    >
                      Open in tab
                    </a>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => approve(b)}
                      disabled={busyId === b.id}
                      className="text-xs bg-green-600/10 hover:bg-green-600 hover:text-white text-green-400 border border-green-600/30 px-3 py-1 rounded font-bold mr-2 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => reject(b)}
                      disabled={busyId === b.id}
                      className="text-xs bg-red-600/10 hover:bg-red-600 hover:text-white text-red-400 border border-red-600/30 px-3 py-1 rounded font-bold disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {previewBrand && (
        <PdfPreview
          url={downloadUrl(previewBrand)}
          title={`Power of attorney — ${previewBrand.name}`}
          onClose={() => setPreviewBrand(null)}
        />
      )}
    </div>
  );
}

function PdfPreview({ url, title, onClose }: { url: string; title: string; onClose: () => void }) {
  // The download endpoint requires a Bearer token. Iframe can't send one
  // automatically, so we fetch as blob through the api client and create
  // a temporary object URL for the iframe.
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    let revokeUrl: string | null = null;
    (async () => {
      try {
        const res = await api.get(url.replace(API_BASE, ''), { responseType: 'blob' });
        if (!live) return;
        revokeUrl = URL.createObjectURL(res.data);
        setBlobUrl(revokeUrl);
      } catch {
        if (live) setError('Failed to load PDF.');
      }
    })();
    return () => {
      live = false;
      if (revokeUrl) URL.revokeObjectURL(revokeUrl);
    };
  }, [url]);

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="text-white font-bold">{title}</div>
          <button onClick={onClose} className="text-gray-400 hover:text-white" aria-label="Close">✕</button>
        </div>
        <div className="flex-1 bg-gray-950">
          {error ? (
            <div className="p-12 text-center text-red-300">{error}</div>
          ) : !blobUrl ? (
            <div className="p-12 text-center text-gray-500">Loading PDF…</div>
          ) : (
            <iframe src={blobUrl} className="w-full h-[75vh]" title={title} />
          )}
        </div>
      </div>
    </div>
  );
}
