'use client';

import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Brand } from '@/types';

type BrandFormState = {
  name: string;
  official_domains: string;
  keywords: string;
  country_restrictions: string;
};
const emptyForm: BrandFormState = {
  name: '',
  official_domains: '',
  keywords: '',
  country_restrictions: 'Worldwide',
};

export default function BrandsPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<BrandFormState>(emptyForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    try {
      const res = await api.get('/brands/');
      setBrands(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingId(null);
    setForm(emptyForm);
    setIsModalOpen(true);
  };

  const openEditModal = (brand: Brand) => {
    setEditingId(brand.id);
    setForm({
      name: brand.name ?? '',
      official_domains: brand.official_domains ?? '',
      keywords: brand.keywords ?? '',
      country_restrictions: brand.country_restrictions ?? 'Worldwide',
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingId(null);
    setForm(emptyForm);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (editingId) {
        await api.put(`/brands/${editingId}`, form);
      } else {
        await api.post('/brands/', form);
      }
      closeModal();
      fetchBrands();
    } catch (err) {
      alert(editingId ? 'Error updating brand' : 'Error creating brand');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (brand: Brand) => {
    if (!confirm(`Delete brand "${brand.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/brands/${brand.id}`);
      fetchBrands();
    } catch (err) {
      alert('Error deleting brand');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">Brand Management</h1>
        <button
          onClick={openCreateModal}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold transition-all"
        >
          + Add New Brand
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {brands.map((brand) => (
          <div key={brand.id} className="bg-gray-800 border border-gray-700 rounded-xl p-6 hover:border-gray-500 transition-all">
            <h3 className="text-xl font-bold text-white mb-2">{brand.name}</h3>
            <div className="space-y-2 text-sm">
              <p className="text-gray-400">
                <span className="text-gray-500 font-medium">Domains:</span> {brand.official_domains}
              </p>
              <p className="text-gray-400">
                <span className="text-gray-500 font-medium">Keywords:</span> {brand.keywords}
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-700 flex gap-2">
              <button
                onClick={() => openEditModal(brand)}
                className="text-xs text-blue-400 hover:text-blue-300 font-bold uppercase"
              >
                Edit
              </button>
              <button
                onClick={() => handleDelete(brand)}
                className="text-xs text-red-400 hover:text-red-300 font-bold uppercase ml-auto"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {brands.length === 0 && !isLoading && (
          <div className="col-span-full py-20 text-center text-gray-500 bg-gray-800/20 rounded-xl border border-dashed border-gray-700">
            No brands registered. Add your first brand to start monitoring.
          </div>
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-white mb-4">
              {editingId ? 'Edit Brand' : 'Register New Brand'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Brand Name</label>
                <input
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white outline-none focus:border-blue-500"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Trusyn Bank"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Official Domains</label>
                <input
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white outline-none focus:border-blue-500"
                  value={form.official_domains}
                  onChange={(e) => setForm({ ...form, official_domains: e.target.value })}
                  placeholder="trusyn.io, trusyn.com"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Keywords (for scanning)</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white outline-none focus:border-blue-500"
                  value={form.keywords}
                  onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                  placeholder="trusyn, login-trusyn, trusyn-verify"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">
                  Country Restrictions
                  <span className="text-gray-600 font-normal normal-case ml-2">
                    (mentioned in abuse reports — Netcraft pattern)
                  </span>
                </label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white outline-none focus:border-blue-500"
                  value={form.country_restrictions}
                  onChange={(e) => setForm({ ...form, country_restrictions: e.target.value })}
                  placeholder="Worldwide, or e.g. Turkey"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-700 text-gray-400 hover:bg-gray-800 transition-all font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 disabled:cursor-not-allowed text-white font-bold transition-all"
                >
                  {isSubmitting ? 'Saving...' : editingId ? 'Update Brand' : 'Save Brand'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
