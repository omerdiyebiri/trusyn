'use client';

import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { Brand, Incident } from '@/types';
import IncidentDetailModal from '@/components/IncidentDetailModal';

export default function DashboardPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  
  // Quick Scan state
  const [scanUrl, setScanUrl] = useState('');
  const [scanBrandId, setScanBrandId] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [brandsRes, incidentsRes] = await Promise.all([
        api.get('/brands/'),
        api.get('/incidents/')
      ]);
      setBrands(brandsRes.data);
      setIncidents(incidentsRes.data);
      if (brandsRes.data.length > 0 && !scanBrandId) {
        setScanBrandId(brandsRes.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scanUrl || !scanBrandId) return;
    
    setIsScanning(true);
    try {
      await api.post('/incidents/', {
        brand_id: scanBrandId,
        target_url: scanUrl.startsWith('http') ? scanUrl : `http://${scanUrl}`,
        threat_type: 'phishing',
      });
      setScanUrl('');
      fetchData();
      alert('Manual scan triggered. Evidence collection started in the background.');
    } catch (error) {
      alert('Error triggering scan');
    } finally {
      setIsScanning(false);
    }
  };

  const getBrandForIncident = (brandId: string) => {
    return brands.find(b => b.id === brandId);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full text-gray-400">Loading security data...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col lg:flex-row justify-between items-start gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Security Overview</h1>
          <p className="text-gray-400">Monitoring brand impersonation and phishing threats.</p>
        </div>
        
        {/* Quick Scan Input */}
        <form onSubmit={handleQuickScan} className="flex flex-col sm:flex-row gap-2 bg-gray-800/50 p-2 rounded-xl border border-gray-700 w-full max-w-xl">
          <select 
            className="bg-gray-700 text-white text-xs rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-blue-500"
            value={scanBrandId}
            onChange={(e) => setScanBrandId(e.target.value)}
          >
            {brands.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
          <input 
            className="bg-transparent text-white text-sm flex-1 px-2 py-2 outline-none"
            placeholder="Enter suspicious URL to scan..."
            value={scanUrl}
            onChange={(e) => setScanUrl(e.target.value)}
          />
          <button 
            disabled={isScanning}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap"
          >
            {isScanning ? 'Scanning...' : 'Quick Scan'}
          </button>
        </form>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800/50 p-6 rounded-xl border border-gray-700 shadow-sm hover:border-gray-600 transition-all">
          <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Protected Brands</h3>
          <p className="text-4xl font-bold mt-2 text-white">{brands.length}</p>
        </div>
        <div className="bg-gray-800/50 p-6 rounded-xl border border-gray-700 shadow-sm hover:border-gray-600 transition-all">
          <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Active Incidents</h3>
          <p className="text-4xl font-bold mt-2 text-red-500">
            {incidents.filter(i => i.status !== 'resolved' && i.status !== 'false_positive').length}
          </p>
        </div>
        <div className="bg-gray-800/50 p-6 rounded-xl border border-gray-700 shadow-sm hover:border-gray-600 transition-all">
          <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Detection Confidence</h3>
          <p className="text-4xl font-bold mt-2 text-blue-400">High</p>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="bg-gray-800/30 rounded-xl border border-gray-700 overflow-hidden shadow-lg">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-bold text-white uppercase tracking-tight">Recent Security Alerts</h3>
          <span className="text-xs text-gray-500">Live monitoring active</span>
        </div>
        
        <div className="overflow-x-auto">
          {incidents.length > 0 ? (
            <table className="w-full text-left">
              <thead className="bg-gray-900/50 text-gray-400 text-xs uppercase font-bold">
                <tr>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Threat Type</th>
                  <th className="px-6 py-4">Target URL</th>
                  <th className="px-6 py-4">Confidence</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/50">
                {[...incidents].reverse().map((incident) => (
                  <tr key={incident.id} className="hover:bg-gray-700/30 transition-colors group">
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${
                        incident.status === 'validated' ? 'bg-red-500/10 text-red-500 border border-red-500/20' :
                        incident.status === 'reported' ? 'bg-orange-500/10 text-orange-500 border border-orange-500/20' :
                        incident.status === 'resolved' ? 'bg-green-500/10 text-green-500 border border-green-500/20' :
                        incident.status === 'analyzing' ? 'bg-blue-500/10 text-blue-500 animate-pulse' :
                        incident.status === 'false_positive' ? 'bg-gray-700 text-gray-500' :
                        'bg-gray-700 text-gray-400'
                      }`}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-white font-medium">{incident.threat_type || 'Scanning...'}</div>
                      <div className="text-gray-500 text-xs">{getBrandForIncident(incident.brand_id)?.name}</div>
                    </td>
                    <td className="px-6 py-4 text-gray-300 font-mono text-xs">{incident.target_url}</td>
                    <td className="px-6 py-4">
                      <div className="w-24 bg-gray-700 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className={`h-full ${incident.confidence_score && incident.confidence_score > 0.8 ? 'bg-red-500' : 'bg-yellow-500'}`}
                          style={{ width: `${(incident.confidence_score || 0) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-[10px] text-gray-500 mt-1 block">{( (incident.confidence_score || 0) * 100).toFixed(0)}% Certainty</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => setSelectedIncident(incident)}
                        className="bg-blue-600/10 text-blue-400 hover:bg-blue-600 hover:text-white px-4 py-1.5 rounded-lg text-sm font-bold transition-all border border-blue-600/20"
                      >
                        Investigate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-gray-500 text-center py-20 bg-gray-800/10">
              <svg className="w-12 h-12 mx-auto mb-4 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              No active threats detected for your brands.
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {selectedIncident && (
        <IncidentDetailModal
          incident={selectedIncident}
          brand={getBrandForIncident(selectedIncident.brand_id)}
          onClose={() => setSelectedIncident(null)}
          onUpdated={fetchData}
        />
      )}
    </div>
  );
}
