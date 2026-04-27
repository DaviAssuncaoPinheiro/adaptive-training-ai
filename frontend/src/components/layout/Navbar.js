'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Activity,
  CalendarDays,
  Dumbbell,
  LogOut,
  UserRound,
} from 'lucide-react';
import Brand from '@/components/brand/Brand';
import { useAuthContext } from '@/context/AuthProvider';
import styles from './Navbar.module.css';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', Icon: Activity },
  { href: '/session', label: 'Sessao', Icon: Dumbbell },
  { href: '/microcycle', label: 'Microciclo', Icon: CalendarDays },
  { href: '/profile', label: 'Perfil', Icon: UserRound },
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
    : 'AI';

  return (
    <nav className={styles.navbar}>
      <Link href="/dashboard" className={styles.logo} aria-label="Adaptive Training AI">
        <Brand />
      </Link>

      <div className={styles.nav}>
        {NAV_ITEMS.map(({ href, label, Icon }) => {
          const active = pathname === href;

          return (
            <Link
              key={href}
              href={href}
              className={`${styles.navLink} ${active ? styles.navLinkActive : ''}`}
            >
              <Icon aria-hidden="true" size={16} strokeWidth={1.6} />
              <span>{label}</span>
            </Link>
          );
        })}
      </div>

      <div className={styles.userSection}>
        <div className={styles.avatar}>{initials}</div>
        <button
          type="button"
          onClick={handleSignOut}
          className={styles.signOutBtn}
          aria-label="Sair"
          title="Sair"
        >
          <LogOut aria-hidden="true" size={15} strokeWidth={1.6} />
        </button>
      </div>
    </nav>
  );
}
