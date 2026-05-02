'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

type NavItem = { name: string; href: string; icon: string };

const PRIMARY_NAV: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard',           icon: '📊' },
  { name: 'Brands',    href: '/dashboard/brands',    icon: '🛡️' },
  { name: 'Incidents', href: '/dashboard/incidents', icon: '🚨' },
  { name: 'Settings',  href: '/dashboard/settings',  icon: '⚙️' },
];

const ADMIN_NAV: NavItem[] = [
  { name: 'Vekalet Review', href: '/dashboard/admin/vekalet', icon: '📜' },
  { name: 'Tenants',        href: '/dashboard/admin/tenants', icon: '🏢' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();
  const isSuperAdmin = user?.role === 'super_admin';

  return (
    <div className="flex flex-col w-64 bg-gray-800 border-r border-gray-700 min-h-screen">
      <div className="flex items-center justify-center h-20 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white">Trusyn</h1>
      </div>
      <div className="flex flex-col flex-1 overflow-y-auto">
        <nav className="flex-1 px-2 py-4 space-y-1">
          {PRIMARY_NAV.map((item) => (
            <SidebarLink
              key={item.href}
              item={item}
              active={pathname === item.href}
            />
          ))}

          {isSuperAdmin && (
            <>
              <div className="pt-6 pb-2 px-3 text-[10px] uppercase tracking-widest text-gray-500 font-bold">
                Admin
              </div>
              {ADMIN_NAV.map((item) => (
                <SidebarLink
                  key={item.href}
                  item={item}
                  active={pathname?.startsWith(item.href) || false}
                />
              ))}
            </>
          )}
        </nav>
      </div>
      <div className="flex-shrink-0 flex flex-col gap-2 border-t border-gray-700 p-4">
        {user && (
          <div className="text-[10px] text-gray-500 truncate" title={user.email}>
            {user.email}
            <span className="ml-1 text-gray-600 uppercase">· {user.role}</span>
          </div>
        )}
        <button
          onClick={logout}
          className="text-gray-400 hover:text-white text-left text-sm font-medium flex items-center"
        >
          <span className="mr-3">🚪</span>
          Logout
        </button>
      </div>
    </div>
  );
}

function SidebarLink({ item, active }: { item: NavItem; active: boolean }) {
  return (
    <Link
      href={item.href}
      className={`${
        active
          ? 'bg-gray-900 text-white'
          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
      } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
    >
      <span className="mr-3">{item.icon}</span>
      {item.name}
    </Link>
  );
}
