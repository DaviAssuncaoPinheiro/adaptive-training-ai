'use client';

import { AuthProvider } from '@/context/AuthProvider';
import Navbar from '@/components/layout/Navbar';

export default function AuthenticatedLayout({ children }) {
  return (
    <AuthProvider>
      <Navbar />
      <main className="page-content">{children}</main>
    </AuthProvider>
  );
}
