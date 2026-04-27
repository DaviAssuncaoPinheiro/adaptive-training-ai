'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Brand from '@/components/brand/Brand';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import styles from '../auth.module.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { signIn, loading, error } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { error: err } = await signIn(email, password);
    if (!err) {
      router.push('/dashboard');
    }
  };

  return (
    <div className={styles.authPage}>
      <div className={styles.authCard}>
        <div className={styles.authHeader}>
          <div className={styles.authLogo}>
            <Brand />
          </div>
          <p className={styles.authEyebrow}>Acesso ao instrumento</p>
          <h1 className={styles.authTitle}>Bem-vindo de volta</h1>
          <p className={styles.authSubtitle}>
            Entre na sua conta para continuar a prescricao adaptativa.
          </p>
        </div>

        {error && <div className={styles.authError}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.authForm}>
          <Input
            id="login-email"
            label="E-mail"
            type="email"
            placeholder="seu@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            id="login-password"
            label="Senha"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" fullWidth loading={loading}>
            Entrar
          </Button>
        </form>

        <div className={styles.authFooter}>
          Nao tem uma conta? <Link href="/register">Criar conta</Link>
        </div>
      </div>
    </div>
  );
}
