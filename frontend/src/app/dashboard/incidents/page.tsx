'use client';

import React, { useEffect, useMemo, useState } from 'react';
import api from '@/services/api';
import { Brand, Incident, IncidentStatus, ThreatType } from '@/types';
import IncidentDetailModal from '@/components/IncidentDetailModal';

type ConfBand = 'all' | 'high' | 'medium' | 'low' | 'unrated';

const STATUS_COLOR: Record<IncidentStatus, string> = {
  detected: 'bg-gray-700 text-gray-300',
  analyzing: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
  validated: 'bg-red-500/10 text-red-400 border border-red-500/20',
  reported: 'bg-orange-500/10 text-orange-400 border border-orange-500/20',
  resolved: 'bg-green-500/10 text-green-400 border border-green-500/20',
  false_positive: 'bg-gray-700 text-gray-500',
};

function bandOf(score: number | undefined | null): ConfBand {
  if (score == null) return 'unrated';
  if (score >= 0.85) return 'high';
  if (score >= 0.5) return 'medium';
  return 'low';
}

export default function IncidentsListPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Incident | null>(null);

  // filters
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | 'all'>('all');
  const [threatFilter, setThreatFilter] = useState<ThreatType | 'all'>('all');
  const [brandFilter, setBrandFilter] = useState<string>('all');
  const [bandFilter, setBandFilter] = useState<ConfBand>('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [iRes, bRes] = await Promise.all([
        api.get('/incidents/'),
        api.get('/brands/'),
      ]);
      setIncidents(iRes.data);
      setBrands(bRes.data);
    } finally {
      setLoading(false);
    }
  };

  const brandsById = useMemo(() => {
    const m = new Map<string, Brand>();
    brands.forEach((b) => m.set(b.id, b));
    return m;
  }, [brands]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return [...incidents]
      .filter((i) => statusFilter === 'all' || i.status === statusFilter)
      .filter((i) => threatFilter === 'all' || i.threat_type === threatFilter)
      .filter((i) => brandFilter === 'all' || i.brand_id === brandFilter)
      .filter((i) => bandFilter === 'all' || bandOf(i.confidence_score) === bandFilter)
      .filter((i) => !q || i.target_url?.toLowerCase().includes(q))
      .sort((a, b) => +new Date(b.discovered_at) - +new Date(a.discovered_at));
  }, [incidents, statusFilter, threatFilter, brandFilter, bandFilter, search]);

  const counts = useMemo(() => {
    const c = { all: incidents.length, validated: 0, reported: 0, resolved: 0 };
    incidents.forEach((i) => {
      if (i.status === 'validated') c.validated++;
      else if (i.status === 'reported') c.reported++;
      else if (i.status === 'resolved') c.resolved++;
    });
    return c;
  }, [incidents]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Incidents</h1>
          <p className="text-gray-400 text-sm">All detections across your brands.</p>
        </div>
        <div className="flex gap-3 text-xs">
          <Pill label="Total" value={counts.all} />
          <Pill label="Validated" value={counts.validated} tone="red" />
          <Pill label="Reported" value={counts.reported} tone="orange" />
          <Pill label="Resolved" value={counts.resolved} tone="green" />
        </div>
      </div>

      <div className="bg-gray-800/30 border border-gray-700 rounded-xl p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <Select label="Status" value={statusFilter} onChange={(v) => setStatusFilter(v as IncidentStatus | 'all')} options={[
          ['all', 'All'],
          ['detected', 'Detected'],
          ['analyzing', 'Analyzing'],
          ['validated', 'Validated'],
          ['reported', 'Reported'],
          ['resolved', 'Resolved'],
          ['false_positive', 'False positive'],
        ]} />
        <Select label="Threat type" value={threatFilter} onChange={(v) => setThreatFilter(v as ThreatType | 'all')} options={[
          ['all', 'All'],
          ['phishing', 'Phishing'],
          ['brand_impersonation', 'Brand impersonation'],
          ['typosquatting', 'Typosquatting'],
        ]} />
        <Select label="Brand" value={brandFilter} onChange={setBrandFilter} options={[
          ['all', 'All brands'],
          ...brands.map((b) => [b.id, b.name] as [string, string]),
        ]} />
        <Select label="Confidence" value={bandFilter} onChange={(v) => setBandFilter(v as ConfBand)} options={[
          ['all', 'All bands'],
          ['high', 'HIGH (≥85%)'],
          ['medium', 'MEDIUM (50-85%)'],
          ['low', 'LOW (<50%)'],
          ['unrated', 'Unrated'],
        ]} />
        <div>
          <div className="text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">Search URL</div>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="example.com"
            className="w-full bg-gray-900 border border-gray-700 rounded-md px-2 py-1.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 outline-none"
          />
        </div>
      </div>

      <div className="bg-gray-800/30 border border-gray-700 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-900/50 text-gray-400 text-[10px] uppercase font-bold tracking-widest">
              <tr>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Threat</th>
                <th className="px-4 py-3">Brand</th>
                <th className="px-4 py-3">URL</th>
                <th className="px-4 py-3">Conf.</th>
                <th className="px-4 py-3">Discovered</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr><td colSpan={7} className="text-center text-gray-500 py-12">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={7} className="text-center text-gray-500 py-12">No incidents match the current filters.</td></tr>
              ) : filtered.map((i) => {
                const b = brandsById.get(i.brand_id);
                const band = bandOf(i.confidence_score);
                return (
                  <tr key={i.id} className="hover:bg-gray-700/30">
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${STATUS_COLOR[i.status as IncidentStatus] || 'bg-gray-700 text-gray-300'}`}>
                        {i.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{i.threat_type || '—'}</td>
                    <td className="px-4 py-3 text-gray-300">{b?.name || <span className="text-gray-600">—</span>}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-200 break-all max-w-[280px]">{i.target_url}</td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] uppercase font-bold ${
                        band === 'high' ? 'text-red-400'
                          : band === 'medium' ? 'text-yellow-400'
                          : band === 'low' ? 'text-blue-400'
                          : 'text-gray-500'
                      }`}>
                        {band}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                      {i.discovered_at ? new Date(i.discovered_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelected(i)}
                        className="text-xs bg-blue-600/10 hover:bg-blue-600 hover:text-white text-blue-400 border border-blue-600/20 px-3 py-1 rounded-md font-bold"
                      >
                        Investigate
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selected && (
        <IncidentDetailModal
          incident={selected}
          brand={brandsById.get(selected.brand_id)}
          onClose={() => setSelected(null)}
          onUpdated={fetchAll}
        />
      )}
    </div>
  );
}

function Pill({ label, value, tone }: { label: string; value: number; tone?: 'red' | 'orange' | 'green' }) {
  const cls =
    tone === 'red' ? 'border-red-500/30 text-red-300'
    : tone === 'orange' ? 'border-orange-500/30 text-orange-300'
    : tone === 'green' ? 'border-green-500/30 text-green-300'
    : 'border-gray-700 text-gray-300';
  return (
    <div className={`px-3 py-1.5 rounded-md border bg-gray-900 ${cls}`}>
      <div className="text-[10px] uppercase tracking-widest text-gray-500">{label}</div>
      <div className="font-bold">{value}</div>
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<[string, string]>;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">{label}</div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-gray-900 border border-gray-700 rounded-md px-2 py-1.5 text-sm text-white focus:border-blue-500 outline-none"
      >
        {options.map(([v, l]) => (
          <option key={v} value={v}>{l}</option>
        ))}
      </select>
    </div>
  );
}
