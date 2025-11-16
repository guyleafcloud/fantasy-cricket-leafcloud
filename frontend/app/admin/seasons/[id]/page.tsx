'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface Season {
  id: string;
  year: string;
  name: string;
  start_date: string;
  end_date: string;
  description?: string;
  is_active: boolean;
  registration_open: boolean;
  created_at: string;
}

export default function SeasonDetailPage() {
  const router = useRouter();
  const params = useParams();
  const seasonId = params.id as string;

  const [season, setSeason] = useState<Season | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    year: '',
    name: '',
    start_date: '',
    end_date: '',
    description: '',
    is_active: false,
    registration_open: false,
  });

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadSeason();
  }, [router, seasonId]);

  const loadSeason = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/seasons/${seasonId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSeason(data);
        setFormData({
          year: data.year,
          name: data.name,
          start_date: data.start_date.split('T')[0],
          end_date: data.end_date.split('T')[0],
          description: data.description || '',
          is_active: data.is_active,
          registration_open: data.registration_open,
        });
      } else if (response.status === 401) {
        router.push('/login');
      } else {
        setError('Failed to load season');
      }
    } catch (err: any) {
      setError('Failed to load season');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      const response = await fetch(`/api/admin/seasons/${seasonId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsEditing(false);
        await loadSeason();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update season');
      }
    } catch (err: any) {
      setError('Failed to update season');
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async () => {
    try {
      const response = await fetch(`/api/admin/seasons/${seasonId}/activate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      if (response.ok) {
        await loadSeason();
      } else {
        setError('Failed to activate season');
      }
    } catch (err: any) {
      setError('Failed to activate season');
    }
  };

  const handleToggleRegistration = async () => {
    try {
      const newStatus = !season?.registration_open;
      const response = await fetch(`/api/admin/seasons/${seasonId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          registration_open: newStatus,
        }),
      });

      if (response.ok) {
        await loadSeason();
      } else {
        setError('Failed to update registration status');
      }
    } catch (err: any) {
      setError('Failed to update registration status');
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cricket-green"></div>
      </div>
    );
  }

  if (!season) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Season Not Found</h2>
          <button
            onClick={() => router.push('/admin/seasons')}
            className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800"
          >
            Back to Seasons
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{season.name}</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {season.year} Season
              </p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => router.push('/admin/seasons')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Back to Seasons
              </button>
              <button
                onClick={() => router.push('/admin/roster')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Roster
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Season Status */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Season Status</h2>
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Active:</span>
                  <span className={`px-3 py-1 rounded text-sm font-medium ${
                    season.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800 dark:text-gray-200'
                  }`}>
                    {season.is_active ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Registration:</span>
                  <span className={`px-3 py-1 rounded text-sm font-medium ${
                    season.registration_open
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800 dark:text-gray-200'
                  }`}>
                    {season.registration_open ? 'Open' : 'Closed'}
                  </span>
                </div>
              </div>
            </div>
            <div className="space-x-3">
              {!season.is_active && (
                <button
                  onClick={handleActivate}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Activate Season
                </button>
              )}
              <button
                onClick={handleToggleRegistration}
                className={`px-4 py-2 rounded-md ${
                  season.registration_open
                    ? 'bg-gray-600 text-white hover:bg-gray-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {season.registration_open ? 'Close Registration' : 'Open Registration'}
              </button>
            </div>
          </div>
        </div>

        {/* Season Details */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Season Details</h2>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                Edit
              </button>
            )}
          </div>

          {isEditing ? (
            <form onSubmit={handleSave}>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Year *
                    </label>
                    <input
                      type="text"
                      required
                      className="w-full px-3 py-2 border rounded-md"
                      value={formData.year}
                      onChange={(e) => setFormData({...formData, year: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Name *
                    </label>
                    <input
                      type="text"
                      required
                      className="w-full px-3 py-2 border rounded-md"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Start Date *
                    </label>
                    <input
                      type="date"
                      required
                      className="w-full px-3 py-2 border rounded-md"
                      value={formData.start_date}
                      onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      End Date *
                    </label>
                    <input
                      type="date"
                      required
                      className="w-full px-3 py-2 border rounded-md"
                      value={formData.end_date}
                      onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border rounded-md"
                    rows={3}
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false);
                    setFormData({
                      year: season.year,
                      name: season.name,
                      start_date: season.start_date.split('T')[0],
                      end_date: season.end_date.split('T')[0],
                      description: season.description || '',
                      is_active: season.is_active,
                      registration_open: season.registration_open,
                    });
                  }}
                  className="px-4 py-2 border rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cricket-green text-white rounded-md hover:bg-green-800 disabled:opacity-50"
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Year:</span>
                  <p className="text-gray-900 dark:text-white font-medium">{season.year}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Name:</span>
                  <p className="text-gray-900 dark:text-white font-medium">{season.name}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Start Date:</span>
                  <p className="text-gray-900 dark:text-white font-medium">
                    {new Date(season.start_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">End Date:</span>
                  <p className="text-gray-900 dark:text-white font-medium">
                    {new Date(season.end_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
              {season.description && (
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Description:</span>
                  <p className="text-gray-900 dark:text-white">{season.description}</p>
                </div>
              )}
              <div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Created:</span>
                <p className="text-gray-900 dark:text-white">
                  {new Date(season.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Tournament Management - Coming Soon */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Tournament Management</h2>
          <div className="text-center py-8">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Tournament and match management coming soon
            </p>
            <div className="space-x-3">
              <button
                disabled
                className="px-4 py-2 bg-gray-300 text-gray-500 dark:text-gray-400 rounded-md cursor-not-allowed"
              >
                View Tournaments
              </button>
              <button
                disabled
                className="px-4 py-2 bg-gray-300 text-gray-500 dark:text-gray-400 rounded-md cursor-not-allowed"
              >
                View Registrations
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
