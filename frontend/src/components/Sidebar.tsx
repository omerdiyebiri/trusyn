'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊' },
  { name: 'Brands', href: '/dashboard/brands', icon: '🛡️' },
  { name: 'Incidents', href: '/dashboard/incidents', icon: '🚨' },
  { name: 'Settings', href: '/dashboard/settings', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <div className="flex flex-col w-64 bg-gray-800 border-r border-gray-700 min-h-screen">
      <div className="flex items-center justify-center h-20 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white">Trusyn</h1>
      </div>
      <div className="flex flex-col flex-1 overflow-y-auto">
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`${
                pathname === item.href
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.name}
            </Link>
          ))}
        </nav>
      </div>
      <div className="flex-shrink-0 flex border-t border-gray-700 p-4">
        <button
          onClick={logout}
          className="flex-shrink-0 w-full group block text-gray-400 hover:text-white text-left"
        >
          <div className="flex items-center">
            <span className="mr-3">🚪</span>
            <div className="ml-3">
              <p className="text-sm font-medium">Logout</p>
            </div>
          </div>
        </button>
      </div>
    </div>
  );
}
