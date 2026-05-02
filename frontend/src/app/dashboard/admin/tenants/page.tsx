'use client';

import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { useAuth } from '@/context/AuthContext';
import { User as UserType } from '@/types';

interface TenantRow {
  id: string;
  name: string;
  subscription_plan?: string;
  created_at?: string;
}

const PLANS: Array<['basic' | 'pro' | 'enterprise', string]> = [
  ['basic', 'Basic'],
  ['pro', 'Pro'],
  ['enterprise', 'Enterprise'],
];

export default function TenantsAdminPage() {
  const { user } = useAuth();
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (user && user.role === 'super_admin') fetchTenants();
  }, [user]);

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/tenants');
      setTenants(res.data);
    } catch {
      setTenants([]);
    } finally {
      setLoading(false);
    }
  };

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
          <h1 className="text-2xl font-bold text-white">Tenants</h1>
          <p className="text-gray-400 text-sm">
            All tenants in the system. Click a row to manage its users.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-2 rounded-md text-sm"
        >
          + New tenant
        </button>
      </div>

      <div className="bg-gray-800/30 border border-gray-700 rounded-xl overflow-hidden">
        {loading ? (
          <div className="text-gray-500 py-12 text-center">Loading…</div>
        ) : tenants.length === 0 ? (
          <div className="text-gray-500 py-12 text-center">No tenants yet.</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-900/50 text-[10px] uppercase tracking-widest text-gray-400">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Plan</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Tenant ID</th>
                <th className="px-4 py-3 text-right">Users</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {tenants.map((t) => (
                <React.Fragment key={t.id}>
                  <tr className="hover:bg-gray-700/20">
                    <td className="px-4 py-3 text-white font-medium">{t.name}</td>
                    <td className="px-4 py-3 text-gray-300 uppercase text-xs">{t.subscription_plan || '—'}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {t.created_at ? new Date(t.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">{t.id}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setExpandedId(expandedId === t.id ? null : t.id)}
                        className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 px-3 py-1 rounded font-bold"
                      >
                        {expandedId === t.id ? 'Hide' : 'Manage'}
                      </button>
                    </td>
                  </tr>
                  {expandedId === t.id && (
                    <tr>
                      <td colSpan={5} className="bg-gray-950/50 p-4 border-t border-gray-800">
                        <TenantUsersPanel tenantId={t.id} />
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <CreateTenantModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            fetchTenants();
          }}
        />
      )}
    </div>
  );
}

function CreateTenantModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState('');
  const [plan, setPlan] = useState<'basic' | 'pro' | 'enterprise'>('basic');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null); setBusy(true);
    try {
      await api.post('/admin/tenants', { name, subscription_plan: plan });
      onCreated();
    } catch (caught: unknown) {
      const e = caught as { response?: { data?: { detail?: string } } };
      setErr(e.response?.data?.detail || 'Create failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <form onSubmit={submit} className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">New tenant</h2>
        <label className="block">
          <span className="block text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">Name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
          />
        </label>
        <label className="block">
          <span className="block text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">Plan</span>
          <select
            value={plan}
            onChange={(e) => setPlan(e.target.value as 'basic' | 'pro' | 'enterprise')}
            className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
          >
            {PLANS.map(([v, l]) => (<option key={v} value={v}>{l}</option>))}
          </select>
        </label>
        {err && <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded px-3 py-2">{err}</div>}
        <div className="flex gap-3 justify-end">
          <button type="button" onClick={onClose} className="text-sm border border-gray-700 hover:bg-gray-800 text-gray-200 px-4 py-2 rounded-md">Cancel</button>
          <button type="submit" disabled={busy} className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-bold px-4 py-2 rounded-md">
            {busy ? 'Creating…' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  );
}

function TenantUsersPanel({ tenantId }: { tenantId: string }) {
  const [users, setUsers] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/tenants/${tenantId}/users`);
      setUsers(res.data);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [tenantId]);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs uppercase tracking-widest font-bold text-gray-400">Users in this tenant</div>
        <button
          onClick={() => setShowCreate(true)}
          className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-bold px-3 py-1 rounded"
        >
          + Add user
        </button>
      </div>
      {loading ? (
        <div className="text-gray-500 text-xs py-4">Loading…</div>
      ) : users.length === 0 ? (
        <div className="text-gray-500 text-xs py-4">No users yet.</div>
      ) : (
        <table className="w-full text-left text-xs">
          <thead className="text-[10px] uppercase text-gray-500">
            <tr>
              <th className="px-2 py-2">Email</th>
              <th className="px-2 py-2">Role</th>
              <th className="px-2 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-gray-800">
                <td className="px-2 py-2 text-gray-200">{u.email}</td>
                <td className="px-2 py-2 text-gray-400 uppercase">{u.role}</td>
                <td className="px-2 py-2 text-gray-500">{u.created_at ? new Date(u.created_at).toLocaleString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {showCreate && (
        <CreateUserModal
          tenantId={tenantId}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); fetchUsers(); }}
        />
      )}
    </div>
  );
}

function CreateUserModal({ tenantId, onClose, onCreated }: { tenantId: string; onClose: () => void; onCreated: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'tenant_admin' | 'tenant_staff' | 'super_admin'>('tenant_staff');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null); setBusy(true);
    try {
      await api.post(`/admin/tenants/${tenantId}/users`, { email, password, role });
      onCreated();
    } catch (caught: unknown) {
      const e = caught as { response?: { data?: { detail?: string } } };
      setErr(e.response?.data?.detail || 'Create failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <form onSubmit={submit} className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">Add user</h2>
        <label className="block">
          <span className="block text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">Email</span>
          <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:border-blue-500 outline-none" />
        </label>
        <label className="block">
          <span className="block text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">Initial password (≥8 chars)</span>
          <input required type="text" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:border-blue-500 outline-none" />
        </label>
        <label className="block">
          <span className="block text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-1">Role</span>
          <select value={role} onChange={(e) => setRole(e.target.value as 'tenant_admin' | 'tenant_staff' | 'super_admin')}
            className="w-full bg-gray-950 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:border-blue-500 outline-none">
            <option value="tenant_staff">Tenant staff</option>
            <option value="tenant_admin">Tenant admin</option>
            <option value="super_admin">Super admin</option>
          </select>
        </label>
        {err && <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded px-3 py-2">{err}</div>}
        <div className="flex gap-3 justify-end">
          <button type="button" onClick={onClose} className="text-sm border border-gray-700 hover:bg-gray-800 text-gray-200 px-4 py-2 rounded-md">Cancel</button>
          <button type="submit" disabled={busy} className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-bold px-4 py-2 rounded-md">
            {busy ? 'Creating…' : 'Create user'}
          </button>
        </div>
      </form>
    </div>
  );
}
