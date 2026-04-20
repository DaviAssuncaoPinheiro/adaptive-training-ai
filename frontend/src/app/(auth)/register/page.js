'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import styles from '../auth.module.css';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState(null);
  const { signUp, loading, error } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);

    if (password !== confirmPassword) {
      setLocalError('As senhas não coincidem.');
      return;
    }

    if (password.length < 6) {
      setLocalError('A senha deve ter pelo menos 6 caracteres.');
      return;
    }

    const { error: err } = await signUp(email, password);
    if (!err) {
      router.push('/onboarding');
    }
  };

  const displayError = localError || error;

  return (
    <div className={styles.authPage}>
      <div className={styles.authCard}>
        <div className={styles.authHeader}>
          <div className={styles.authLogo}>⚡</div>
          <h1 className={styles.authTitle}>Criar conta</h1>
          <p className={styles.authSubtitle}>
            Comece sua jornada de treino adaptativo
          </p>
        </div>

        {displayError && <div className={styles.authError}>{displayError}</div>}

        <form onSubmit={handleSubmit} className={styles.authForm}>
          <Input
            id="register-email"
            label="E-mail"
            type="email"
            placeholder="seu@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            id="register-password"
            label="Senha"
            type="password"
            placeholder="Mínimo 6 caracteres"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Input
            id="register-confirm"
            label="Confirmar senha"
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
          <Button type="submit" fullWidth loading={loading}>
            Criar conta
          </Button>
        </form>

        <div className={styles.authFooter}>
          Já tem uma conta?{' '}
          <Link href="/login">Entrar</Link>
        </div>
      </div>
    </div>
  );
}
