'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface Season {
  id: string;
  year: string;
  name: string;
  is_active: boolean;
  registration_open: boolean;
}

interface League {
  id: string;
  season_id: string;
  season_name: string;
  name: string;
  league_code: string;
  participants_count: number;
  max_participants: number;
}

interface Stats {
  seasons_count: number;
  active_season: Season | null;
  leagues_count: number;
  players_count: number;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Stats>({
    seasons_count: 0,
    active_season: null,
    leagues_count: 0,
    players_count: 0,
  });
  const [recentLeagues, setRecentLeagues] = useState<League[]>([]);

  const CLUB_ID = '625f1c55-6d5b-40a9-be1d-8f7abe6fa00e'; // ACC club ID

  useEffect(() => {
    const checkAdminAndLoad = async () => {
      const token = localStorage.getItem('admin_token');
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        // Verify user is admin
        const response = await fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const userData = await response.json();
          if (!userData.is_admin) {
            // Not an admin, redirect to user dashboard
            router.push('/dashboard');
            return;
          }
          // User is admin, load data
          loadDashboardData();
        } else {
          // Token invalid
          localStorage.removeItem('admin_token');
          router.push('/login');
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        router.push('/login');
      }
    };

    checkAdminAndLoad();
  }, [router]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load seasons
      const seasonsResponse = await fetch('/api/admin/seasons', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      // Load leagues
      const leaguesResponse = await fetch('/api/admin/leagues', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        },
      });

      // Load players
      const playersData = await apiClient.getPlayers(CLUB_ID);

      if (seasonsResponse.ok && leaguesResponse.ok) {
        const seasonsData = await seasonsResponse.json();
        const leaguesData = await leaguesResponse.json();

        const activeSeason = (seasonsData.seasons || []).find((s: Season) => s.is_active);

        setStats({
          seasons_count: (seasonsData.seasons || []).length,
          active_season: activeSeason || null,
          leagues_count: (leaguesData.leagues || []).length,
          players_count: playersData.players.length,
        });

        // Get most recent 5 leagues
        setRecentLeagues((leaguesData.leagues || []).slice(0, 5));
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/login');
  };

  const handleToggleMode = async () => {
    try {
      const response = await apiClient.toggleAdminMode();
      // After toggling, redirect to user dashboard
      router.push('/dashboard');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to toggle mode');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cricket-green"></div>
      </div>
    );
  }

  const workflowSteps = [
    {
      number: 1,
      title: 'Create Season',
      description: 'Set up a new cricket season with dates and settings',
      action: 'Manage Seasons',
      link: '/admin/seasons',
      status: stats.seasons_count > 0 ? 'complete' : 'pending',
      stat: `${stats.seasons_count} season${stats.seasons_count !== 1 ? 's' : ''}`,
    },
    {
      number: 2,
      title: 'Create League',
      description: 'Create fantasy leagues for the season',
      action: 'Manage Leagues',
      link: '/admin/leagues',
      status: stats.leagues_count > 0 ? 'complete' : 'pending',
      stat: `${stats.leagues_count} league${stats.leagues_count !== 1 ? 's' : ''}`,
      disabled: stats.seasons_count === 0,
    },
    {
      number: 3,
      title: 'Confirm Roster',
      description: 'Review and edit player roster with multipliers',
      action: 'Manage Roster',
      link: '/admin/roster',
      status: stats.players_count > 0 ? 'complete' : 'pending',
      stat: `${stats.players_count} players`,
    },
    {
      number: 4,
      title: 'Launch Game',
      description: 'Open registration and let users join leagues',
      action: stats.active_season?.registration_open ? 'Registration Open' : 'Confirm Leagues',
      link: stats.active_season?.registration_open ? '/admin/seasons' : '/admin/leagues',
      status: stats.active_season?.registration_open ? 'complete' : 'pending',
      stat: stats.active_season?.is_active ? 'Season active' : 'Confirm leagues to launch',
      disabled: stats.leagues_count === 0 || stats.players_count === 0,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Manage your fantasy cricket platform
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/admin/users')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900"
              >
                User Management
              </button>
              <button
                onClick={handleToggleMode}
                className="px-4 py-2 border border-purple-300 bg-purple-50 rounded-md text-sm font-medium text-purple-700 hover:bg-purple-100"
              >
                Switch to User Mode
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
        {/* Active Season Banner */}
        {stats.active_season ? (
          <div className="mb-8 bg-cricket-green text-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Active Season: {stats.active_season.name}</h2>
                <p className="mt-1 text-green-100">
                  Registration is {stats.active_season.registration_open ? 'open' : 'closed'}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white dark:bg-gray-800 text-cricket-green">
                  {stats.active_season.year}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="mb-8 bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  No active season. Create and activate a season to get started.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Workflow Steps */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Setup Workflow</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {workflowSteps.map((step) => (
              <div
                key={step.number}
                className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 border-l-4 ${
                  step.status === 'complete'
                    ? 'border-green-500'
                    : step.disabled
                    ? 'border-gray-300 dark:border-gray-600 opacity-60'
                    : 'border-yellow-400'
                }`}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div
                      className={`flex items-center justify-center h-12 w-12 rounded-full ${
                        step.status === 'complete'
                          ? 'bg-green-100 text-green-600'
                          : step.disabled
                          ? 'bg-gray-100 text-gray-400'
                          : 'bg-yellow-100 text-yellow-600'
                      }`}
                    >
                      {step.status === 'complete' ? (
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <span className="text-xl font-bold">{step.number}</span>
                      )}
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">{step.title}</h3>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{step.description}</p>
                    <p className="mt-2 text-sm font-medium text-cricket-green">{step.stat}</p>
                    <button
                      onClick={() => !step.disabled && router.push(step.link)}
                      disabled={step.disabled}
                      className={`mt-4 px-4 py-2 rounded-md text-sm font-medium ${
                        step.disabled
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : 'bg-cricket-green text-white hover:bg-green-800'
                      }`}
                    >
                      {step.action}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Leagues */}
        {recentLeagues.length > 0 && (
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Recent Leagues</h2>
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      League Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Season
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Join Code
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Participants
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200">
                  {recentLeagues.map((league) => (
                    <tr key={league.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 dark:bg-gray-900">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {league.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {league.season_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <code className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-cricket-green dark:text-green-400 font-mono text-sm rounded">
                          {league.league_code}
                        </code>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {league.participants_count} / {league.max_participants}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => router.push(`/admin/leagues/${league.id}`)}
                          className="text-cricket-green hover:text-green-900"
                        >
                          Manage
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
