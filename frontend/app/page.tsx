'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkUserAndRedirect = async () => {
      const token = localStorage.getItem('admin_token');

      if (!token) {
        router.push('/login');
        return;
      }

      try {
        // Check if user is admin
        const response = await fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const userData = await response.json();

          // Redirect based on admin status
          if (userData.is_admin) {
            router.push('/admin/roster');
          } else {
            router.push('/dashboard');
          }
        } else {
          // Token invalid, go to login
          localStorage.removeItem('admin_token');
          router.push('/login');
        }
      } catch (error) {
        console.error('Error checking user status:', error);
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    checkUserAndRedirect();
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cricket-green mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading...</p>
      </div>
    </div>
  );
}
