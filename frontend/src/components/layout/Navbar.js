'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthContext } from '@/context/AuthProvider';
import styles from './Navbar.module.css';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/session', label: 'Sessão' },
  { href: '/check-in', label: 'Check-in' },
  { href: '/microcycle', label: 'Microciclo' },
  { href: '/profile', label: 'Perfil' },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut } = useAuthContext();

  if (!user) return null;

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
  };

  const initials = user.email
    ? user.email.substring(0, 2).toUpperCase()
    : '??';

  return (
    <nav className={styles.navbar}>
      <Link href="/dashboard" className={styles.logo}>
        <span className={styles.logoIcon}>⚡</span>
        Adaptive AI
      </Link>

      <div className={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`${styles.navLink} ${
              pathname === item.href ? styles.navLinkActive : ''
            }`}
          >
            {item.label}
          </Link>
        ))}
      </div>

      <div className={styles.userSection}>
        <div className={styles.avatar}>{initials}</div>
        <button onClick={handleSignOut} className={styles.signOutBtn}>
          Sair
        </button>
      </div>
    </nav>
  );
}
