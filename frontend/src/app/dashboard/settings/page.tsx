'use client';

import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';

interface TenantInfo {
  id: string;
  name: string;
  subscription_plan: string | null;
  created_at: string | null;
}

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await refreshUser();
      try {
        const res = await api.get('/me/tenant');
        if (!cancelled) setTenant(res.data);
      } catch {
        if (!cancelled) setTenant(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 text-sm">Profile, security, and tenant info.</p>
      </div>

      <Card title="Profile">
        {loading ? (
          <div className="text-gray-500">Loading…</div>
        ) : (
          <Row label="Email" value={user?.email || '—'} />
        )}
        {user && <Row label="Role" value={user.role.replace('_', ' ').toUpperCase()} />}
        {user?.created_at && (
          <Row label="Member since" value={new Date(user.created_at).toLocaleString()} />
        )}
      </Card>

      <PasswordCard />

      <Card title="Tenant">
        {loading ? (
          <div className="text-gray-500">Loading…</div>
        ) : tenant ? (
          <>
            <Row label="Name" value={tenant.name} />
            <Row label="Plan" value={tenant.subscription_plan ? tenant.subscription_plan.toUpperCase() : '—'} />
            {tenant.created_at && (
              <Row label="Created" value={new Date(tenant.created_at).toLocaleString()} />
            )}
            <Row label="Tenant ID" value={tenant.id} mono />
          </>
        ) : (
          <div className="text-gray-500">No tenant attached to this account.</div>
        )}
      </Card>

      <Card title="Mail stack">
        <p className="text-xs text-gray-500 mb-3">
          Outbound abuse mail is sent from <span className="font-mono text-gray-300">takedowns@trusyn.io</span>.
          Reply tracking is handled by an IMAP poller against the same mailbox.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <Indicator label="DKIM" hint="google._domainkey" />
          <Indicator label="SPF"  hint="v=spf1 include:_spf.google.com ~all" />
          <Indicator label="DMARC" hint="v=DMARC1; p=none; rua=…" />
          <Indicator label="IMAP poller" hint="Reply classification active" />
        </div>
      </Card>

      <Card title="Notifications">
        <p className="text-sm text-gray-400">
          Email alerts on new HIGH-confidence incidents and registrar replies are coming
          in a future release. For now, the dashboard is the source of truth — bookmark{' '}
          <span className="font-mono text-gray-300">/dashboard/incidents</span> for the
          live queue.
        </p>
      </Card>
    </div>
  );
}

function PasswordCard() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    if (next.length < 8) {
      setMsg({ ok: false, text: 'New password must be at least 8 characters.' });
      return;
    }
    if (next !== confirm) {
      setMsg({ ok: false, text: 'New password and confirmation do not match.' });
      return;
    }
    setBusy(true);
    try {
      await api.post('/me/password', { current_password: current, new_password: next });
      setMsg({ ok: true, text: 'Password changed.' });
      setCurrent(''); setNext(''); setConfirm('');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMsg({ ok: false, text: e.response?.data?.detail || 'Password change failed.' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Change password">
      <form onSubmit={submit} className="space-y-3 max-w-md">
        <PwdField label="Current password" value={current} onChange={setCurrent} />
        <PwdField label="New password" value={next} onChange={setNext} />
        <PwdField label="Confirm new password" value={confirm} onChange={setConfirm} />
        {msg && (
          <div className={`text-xs rounded px-3 py-2 ${msg.ok ? 'bg-green-500/10 text-green-300 border border-green-500/30' : 'bg-red-500/10 text-red-300 border border-red-500/30'}`}>
            {msg.text}
          </div>
        )}
        <button
          type="submit"
          disabled={busy}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-bold px-4 py-2 rounded-md text-sm transition-colors"
        >
          {busy ? 'Updating…' : 'Update password'}
        </button>
      </form>
    </Card>
  );
}

function PwdField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block">
      <span className="block text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">{label}</span>
      <input
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
        autoComplete="off"
      />
    </label>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-800/30 border border-gray-700 rounded-xl p-6">
      <h2 className="text-sm uppercase tracking-widest font-bold text-gray-400 mb-4">{title}</h2>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-4 py-1">
      <div className="text-xs uppercase tracking-widest text-gray-500">{label}</div>
      <div className={`text-sm text-gray-200 break-all ${mono ? 'font-mono text-xs' : ''}`}>{value}</div>
    </div>
  );
}

function Indicator({ label, hint }: { label: string; hint: string }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-md px-3 py-2 flex items-center gap-3">
      <span className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
      <div>
        <div className="text-[11px] font-bold text-white uppercase tracking-widest">{label}</div>
        <div className="text-[10px] text-gray-500 font-mono">{hint}</div>
      </div>
    </div>
  );
}
