'use client';

import { useMemo, useState } from 'react';
import { CalendarDays, CheckCircle2, Plus, Save, Sparkles, X } from 'lucide-react';
import { useAuthContext } from '@/context/AuthProvider';
import { useMicrocycle } from '@/hooks/useMicrocycle';
import { useWorkoutLog } from '@/hooks/useWorkoutLog';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { getDayName } from '@/lib/utils';
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
  const { microcycle } = useMicrocycle(user?.id);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [sessionFeedback, setSessionFeedback] = useState(null);

  const [workoutName, setWorkoutName] = useState('');
  const [duration, setDuration] = useState('');
  const [notes, setNotes] = useState('');
  const [sets, setSets] = useState([emptySet()]);
  const planned = useMemo(() => pickPlannedWorkout(microcycle), [microcycle]);

  const usePlannedWorkout = () => {
    if (!planned?.workout) return;
    setWorkoutName(planned.workout.session_name || '');
    setSets(buildSetsFromPlan(planned.workout));
    setNotes(buildPlanNote(microcycle, planned.workout));
    setSuccess(false);
  };

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
      console.error('Erro ao salvar sessao:', error);
      alert(`Falha ao salvar: ${error.message || JSON.stringify(error)}`);
    } else {
      setSuccess(true);
      setSessionFeedback(buildSessionFeedback(payload));
      setWorkoutName('');
      setDuration('');
      setNotes('');
      setSets([emptySet()]);
      setTimeout(() => setSuccess(false), 4000);
    }
  };

  return (
    <div className={styles.sessionPage}>
      <header className={styles.pageHeader}>
        <p className={styles.eyebrow}>№ 05 · Sessão</p>
        <h1 className={styles.pageTitle}>Registrar Sessão</h1>
        <p className={styles.pageSubtitle}>
          Log de treino com séries, carga, reps e RPE em formato denso.
        </p>
      </header>

      {success && (
        <div className={styles.successMsg}>
          <CheckCircle2 aria-hidden="true" size={18} strokeWidth={1.6} />
          Sessão registrada com sucesso.
        </div>
      )}

      {sessionFeedback && (
        <div className={styles.feedbackCard}>
          <p className={styles.sectionEyebrow}>№ 04 · Feedback pós-sessão</p>
          <h2 className={styles.sectionTitle}>{sessionFeedback.title}</h2>
          <p>{sessionFeedback.body}</p>
          <div className={styles.feedbackStats}>
            <span>{sessionFeedback.sets} séries</span>
            <span>{sessionFeedback.tonnage} kg</span>
            <span>RPE {sessionFeedback.avgRpe}</span>
          </div>
        </div>
      )}

      {planned?.workout && (
        <section className={styles.plannedCard}>
          <div className={styles.plannedHeader}>
            <div>
              <p className={styles.sectionEyebrow}>
                Nº 00 · {planned.isToday ? 'Sessao de hoje' : 'Proxima sessao planejada'}
              </p>
              <h2 className={styles.sectionTitle}>{planned.workout.session_name}</h2>
              <p className={styles.plannedMeta}>
                <CalendarDays aria-hidden="true" size={15} strokeWidth={1.7} />
                {getDayName(planned.workout.day_of_week)} · {(planned.workout.exercises || []).length} exercicios
              </p>
            </div>
            <Button type="button" variant="secondary" onClick={usePlannedWorkout}>
              <Sparkles aria-hidden="true" size={15} strokeWidth={1.7} />
              Usar plano
            </Button>
          </div>

          <div className={styles.plannedExerciseList}>
            {(planned.workout.exercises || []).map((exercise, index) => (
              <div key={`${exercise.exercise_name}-${index}`} className={styles.plannedExercise}>
                <span>{exercise.exercise_name}</span>
                <strong>
                  {exercise.target_sets}x{exercise.target_reps} · RPE {exercise.target_rpe} · {exercise.rest_seconds}s
                </strong>
              </div>
            ))}
          </div>

          {microcycle?.ai_justification && (
            <p className={styles.plannedInsight}>
              {microcycle.ai_justification}
            </p>
          )}
        </section>
      )}

      <form onSubmit={handleSubmit} className={styles.sessionForm}>
        <section className={styles.formSection}>
          <p className={styles.sectionEyebrow}>№ 01 · Geral</p>
          <h2 className={styles.sectionTitle}>Informações Gerais</h2>
          <div className={styles.fieldsRow}>
            <Input
              id="session-name"
              label="Nome do treino"
              placeholder="Treino A - Peito/Triceps"
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
        </section>

        <section className={styles.formSection}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.sectionEyebrow}>№ 02 · Sets</p>
              <h2 className={styles.sectionTitle}>Séries Executadas</h2>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={addSet}
              className={styles.addSetBtn}
            >
              <Plus aria-hidden="true" size={14} strokeWidth={1.8} />
              Adicionar série
            </Button>
          </div>

          <div className={styles.setsList}>
            {sets.map((set, i) => (
              <div key={i} className={styles.setRow}>
                <div className={styles.setNumber}>{String(i + 1).padStart(2, '0')}</div>
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
                  aria-label={`Remover serie ${i + 1}`}
                >
                  <X aria-hidden="true" size={15} strokeWidth={1.8} />
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.formSection}>
          <p className={styles.sectionEyebrow}>№ 03 · Nota</p>
          <h2 className={styles.sectionTitle}>Observações</h2>
          <textarea
            id="session-notes"
            placeholder="Anotações opcionais sobre a sessão..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className={styles.textarea}
          />
        </section>

        <div className={styles.formActions}>
          <Button type="submit" loading={loading}>
            <Save aria-hidden="true" size={15} strokeWidth={1.8} />
            Salvar sessão
          </Button>
        </div>
      </form>
    </div>
  );
}

function buildSessionFeedback(log) {
  const validSets = log.sets || [];
  const tonnage = validSets.reduce(
    (sum, set) => sum + (set.reps || 0) * (set.weight_kg || 0),
    0
  );
  const rpes = validSets
    .map((set) => set.rpe)
    .filter((value) => typeof value === 'number' && !Number.isNaN(value));
  const avgRpe = rpes.length
    ? rpes.reduce((sum, value) => sum + value, 0) / rpes.length
    : null;

  if (avgRpe !== null && avgRpe >= 9) {
    return {
      title: 'Sessão pesada registrada',
      body: 'RPE alto. O próximo check-up deve pesar mais na decisão de carga para evitar acúmulo desnecessário de fadiga.',
      sets: validSets.length,
      tonnage: Math.round(tonnage),
      avgRpe: avgRpe.toFixed(1),
    };
  }

  if (avgRpe !== null && avgRpe <= 6) {
    return {
      title: 'Estímulo moderado',
      body: 'Sessão controlada. Se a recuperação seguir boa, o próximo microciclo pode aceitar progressão conservadora.',
      sets: validSets.length,
      tonnage: Math.round(tonnage),
      avgRpe: avgRpe.toFixed(1),
    };
  }

  return {
    title: 'Sessão dentro do alvo',
    body: 'Dados salvos na memória do atleta. A IA usa esse padrão para ajustar volume, RPE e progressão semanal.',
    sets: validSets.length,
    tonnage: Math.round(tonnage),
    avgRpe: avgRpe !== null ? avgRpe.toFixed(1) : 'n/d',
  };
}

function pickPlannedWorkout(microcycle) {
  const workouts = [...(microcycle?.workouts || [])].sort(
    (a, b) => (a.day_of_week || 0) - (b.day_of_week || 0)
  );
  if (!workouts.length) return null;

  const today = currentPlanDay();
  const todayWorkout = workouts.find((workout) => workout.day_of_week === today);
  if (todayWorkout) return { workout: todayWorkout, isToday: true };

  const nextWorkout = workouts.find((workout) => workout.day_of_week > today) || workouts[0];
  return { workout: nextWorkout, isToday: false };
}

function currentPlanDay() {
  const jsDay = new Date().getDay();
  return jsDay === 0 ? 7 : jsDay;
}

function buildSetsFromPlan(workout) {
  const rows = (workout.exercises || []).flatMap((exercise) =>
    Array.from({ length: Math.max(1, Number(exercise.target_sets) || 1) }).map(() => ({
      exercise_name: exercise.exercise_name || '',
      reps: '',
      weight_kg: '',
      rpe: exercise.target_rpe ? String(exercise.target_rpe) : '',
    }))
  );
  return rows.length ? rows : [emptySet()];
}

function buildPlanNote(microcycle, workout) {
  const cap = microcycle?.max_rpe_cap ? `RPE cap ${microcycle.max_rpe_cap}/10.` : '';
  return `Sessao importada do microciclo: ${workout.session_name}. ${cap}`.trim();
}
