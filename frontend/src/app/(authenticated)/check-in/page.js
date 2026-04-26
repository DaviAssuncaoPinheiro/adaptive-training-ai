'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/context/AuthProvider';
import { useCheckIn } from '@/hooks/useCheckIn';
import Button from '@/components/ui/Button';
import styles from './check-in.module.css';

const QUESTIONS = [
  { key: 'sleep_quality',   label: 'Qualidade do sono',  hint: '1 = péssima · 10 = excelente' },
  { key: 'energy_level',    label: 'Energia hoje',       hint: '1 = exausto · 10 = cheio de energia' },
  { key: 'muscle_soreness', label: 'Dor muscular',       hint: '1 = sem dor · 10 = dor extrema' },
  { key: 'stress_level',    label: 'Estresse',           hint: '1 = relaxado · 10 = sob muita pressão' },
  { key: 'fatigue_level',   label: 'Fadiga geral',       hint: '1 = descansado · 10 = exausto' },
];

const todayISO = () => new Date().toISOString().slice(0, 10);

export default function CheckInPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const { addCheckIn } = useCheckIn(user?.id);

  const [values, setValues] = useState(() =>
    Object.fromEntries(QUESTIONS.map((q) => [q.key, 5]))
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const setValue = (key, v) =>
    setValues((prev) => ({ ...prev, [key]: Number(v) }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) return;
    setSubmitting(true);
    setError(null);

    const { error } = await addCheckIn({ ...values, check_in_date: todayISO() });
    setSubmitting(false);

    if (error) {
      setError(
        error.code === '23505'
          ? 'Você já fez check-in hoje. Volte amanhã.'
          : error.message || 'Erro ao salvar check-in'
      );
      return;
    }
    router.push('/dashboard');
  };

  return (
    <div className={styles.checkInPage}>
      <h1 className={styles.pageTitle}>Check-in diário</h1>
      <p className={styles.pageSubtitle}>
        Como você está hoje? Estes dados ajudam a IA a calibrar seu próximo microciclo.
      </p>

      <form className={styles.card} onSubmit={handleSubmit}>
        {QUESTIONS.map((q) => (
          <div key={q.key} className={styles.field}>
            <div className={styles.labelRow}>
              <label htmlFor={q.key} className={styles.label}>{q.label}</label>
              <span className={styles.value}>{values[q.key]}</span>
            </div>
            <input
              id={q.key}
              type="range"
              min="1"
              max="10"
              step="1"
              value={values[q.key]}
              onChange={(e) => setValue(q.key, e.target.value)}
              className={styles.slider}
            />
            <span className={styles.hint}>{q.hint}</span>
          </div>
        ))}

        {error && <p className={styles.error}>{error}</p>}

        <Button type="submit" loading={submitting} fullWidth>
          Salvar check-in
        </Button>
      </form>
    </div>
  );
}
