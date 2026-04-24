'use client';

import { useState } from 'react';
import { useAuthContext } from '@/context/AuthProvider';
import { useWorkoutLog } from '@/hooks/useWorkoutLog';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import styles from './session.module.css';

const emptySet = () => ({
  exercise_name: '',
  reps: '',
  weight_kg: '',
  rpe: '',
});

export default function SessionPage() {
  const { user } = useAuthContext();
  const { addLog } = useWorkoutLog(user?.id);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const [workoutName, setWorkoutName] = useState('');
  const [duration, setDuration] = useState('');
  const [notes, setNotes] = useState('');
  const [sets, setSets] = useState([emptySet()]);

  const updateSet = (index, field, value) => {
    setSets((prev) =>
      prev.map((s, i) => (i === index ? { ...s, [field]: value } : s))
    );
  };

  const addSet = () => setSets((prev) => [...prev, emptySet()]);

  const removeSet = (index) => {
    if (sets.length <= 1) return;
    setSets((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);

    const payload = {
      workout_name: workoutName,
      session_date: new Date().toISOString(),
      duration_minutes: parseInt(duration),
      notes: notes || null,
      sets: sets.map((s) => ({
        exercise_name: s.exercise_name,
        reps: parseInt(s.reps),
        weight_kg: parseFloat(s.weight_kg),
        rpe: s.rpe ? parseInt(s.rpe) : null,
      })),
    };

    const { error } = await addLog(payload);
    setLoading(false);

    if (error) {
      console.error('Erro ao salvar sessão:', error);
      alert(`Falha ao salvar: ${error.message || JSON.stringify(error)}`);
    } else {
      setSuccess(true);
      setWorkoutName('');
      setDuration('');
      setNotes('');
      setSets([emptySet()]);
      setTimeout(() => setSuccess(false), 4000);
    }
  };

  return (
    <div className={styles.sessionPage}>
      <h1 className={styles.pageTitle}>Registrar Sessão</h1>
      <p className={styles.pageSubtitle}>
        Insira os dados do seu treino em tempo real
      </p>

      {success && (
        <div className={styles.successMsg}>
          ✅ Sessão registrada com sucesso!
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.sessionForm}>
        {/* Info geral */}
        <div className={styles.formSection}>
          <h2 className={styles.sectionTitle}>Informações Gerais</h2>
          <div className={styles.fieldsRow}>
            <Input
              id="session-name"
              label="Nome do treino"
              placeholder="Ex: Treino A — Peito/Tríceps"
              value={workoutName}
              onChange={(e) => setWorkoutName(e.target.value)}
              required
            />
            <Input
              id="session-duration"
              label="Duração (min)"
              type="number"
              placeholder="60"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              min="1"
              required
            />
          </div>
        </div>

        {/* Séries */}
        <div className={styles.formSection}>
          <h2 className={styles.sectionTitle}>Séries Executadas</h2>
          <div className={styles.setsList}>
            {sets.map((set, i) => (
              <div key={i} className={styles.setRow}>
                <Input
                  id={`set-${i}-exercise`}
                  placeholder="Exercício"
                  value={set.exercise_name}
                  onChange={(e) => updateSet(i, 'exercise_name', e.target.value)}
                  required
                />
                <Input
                  id={`set-${i}-reps`}
                  type="number"
                  placeholder="Reps"
                  value={set.reps}
                  onChange={(e) => updateSet(i, 'reps', e.target.value)}
                  min="0"
                  required
                />
                <Input
                  id={`set-${i}-weight`}
                  type="number"
                  placeholder="Kg"
                  step="0.5"
                  value={set.weight_kg}
                  onChange={(e) => updateSet(i, 'weight_kg', e.target.value)}
                  min="0"
                  required
                />
                <Input
                  id={`set-${i}-rpe`}
                  type="number"
                  placeholder="RPE"
                  value={set.rpe}
                  onChange={(e) => updateSet(i, 'rpe', e.target.value)}
                  min="1"
                  max="10"
                />
                <button
                  type="button"
                  className={styles.removeBtn}
                  onClick={() => removeSet(i)}
                  title="Remover série"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={addSet}
            className={styles.addSetBtn}
          >
            + Adicionar Série
          </Button>
        </div>

        {/* Notas */}
        <div className={styles.formSection}>
          <h2 className={styles.sectionTitle}>Observações</h2>
          <textarea
            id="session-notes"
            placeholder="Anotações opcionais sobre o treino..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            style={{
              width: '100%',
              padding: '0.625rem 0.875rem',
              fontFamily: 'var(--font-sans)',
              fontSize: 'var(--text-sm)',
              color: 'var(--color-text-primary)',
              background: 'var(--color-bg-input)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              outline: 'none',
              resize: 'vertical',
            }}
          />
        </div>

        {/* Submit */}
        <div className={styles.formActions}>
          <Button type="submit" loading={loading}>
            Salvar Sessão
          </Button>
        </div>
      </form>
    </div>
  );
}
