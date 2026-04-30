'use client';

import React from 'react';

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Security Overview</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium">Protected Brands</h3>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium">Active Incidents</h3>
          <p className="text-3xl font-bold mt-2 text-red-500">0</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium">Takedowns (Monthly)</h3>
          <p className="text-3xl font-bold mt-2 text-green-500">0</p>
        </div>
      </div>
      
      <div className="mt-8 bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h3 className="text-lg font-medium text-white mb-4">Recent Alerts</h3>
        <div className="text-gray-500 text-center py-12">
          No recent incidents detected.
        </div>
      </div>
    </div>
  );
}
