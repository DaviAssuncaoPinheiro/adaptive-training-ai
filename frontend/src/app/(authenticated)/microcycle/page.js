'use client';

import { useAuthContext } from '@/context/AuthProvider';
import { useMicrocycle } from '@/hooks/useMicrocycle';
import { useMicrocycleGeneration } from '@/hooks/useMicrocycleGeneration';
import Button from '@/components/ui/Button';
import { getDayName, formatDate } from '@/lib/utils';
import styles from './microcycle.module.css';

export default function MicrocyclePage() {
  const { user } = useAuthContext();
  const { microcycle, loading, refetch } = useMicrocycle(user?.id);

  const generation = useMicrocycleGeneration({
    onDone: () => refetch(),
  });

  const isGenerating = generation.status === 'generating';

  if (loading) {
    return (
      <div className={styles.microcyclePage}>
        <h1 className={styles.pageTitle}>Microciclo</h1>
        <p className={styles.pageSubtitle}>Carregando...</p>
      </div>
    );
  }

  if (!microcycle) {
    return (
      <div className={styles.microcyclePage}>
        <h1 className={styles.pageTitle}>Microciclo</h1>
        <p className={styles.pageSubtitle}>Seu plano semanal de treino gerado pela IA</p>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🗓️</div>
          <p>Nenhum microciclo ativo encontrado.</p>
          <p>Gere um plano personalizado a partir do seu perfil e histórico.</p>
          <Button onClick={generation.generate} loading={isGenerating}>
            {isGenerating ? 'Gerando microciclo…' : 'Gerar meu microciclo'}
          </Button>
          {isGenerating && (
            <p className={styles.pageSubtitle}>
              Isso pode levar de 30s a 2min — a IA está analisando seu histórico.
            </p>
          )}
          {generation.status === 'failed' && (
            <p style={{ color: 'var(--color-warning)' }}>
              Erro: {generation.error}
            </p>
          )}
        </div>
      </div>
    );
  }

  const workouts = microcycle.workouts || [];

  return (
    <div className={styles.microcyclePage}>
      <h1 className={styles.pageTitle}>Microciclo</h1>
      <p className={styles.pageSubtitle}>
        {formatDate(microcycle.start_date)} — {formatDate(microcycle.end_date)}
      </p>

      <div className={styles.safetyRow}>
        <span className={`${styles.badge} ${styles.badgeInfo}`}>
          🛡️ Volume máx/músculo: {microcycle.max_weekly_sets_per_muscle} séries
        </span>
        <span className={`${styles.badge} ${styles.badgeWarning}`}>
          ⚠️ RPE cap: {microcycle.max_rpe_cap}/10
        </span>
      </div>

      <div className={`${styles.workoutsGrid} stagger-children`}>
        {workouts.map((workout, i) => (
          <div key={i} className={styles.workoutCard}>
            <div className={styles.workoutDay}>
              {getDayName(workout.day_of_week)}
            </div>
            <div className={styles.workoutName}>{workout.session_name}</div>

            <div className={styles.exerciseList}>
              {(workout.exercises || []).map((ex, j) => (
                <div key={j} className={styles.exerciseRow}>
                  <span className={styles.exerciseName}>{ex.exercise_name}</span>
                  <span className={styles.exerciseMeta}>
                    {ex.target_sets}×{ex.target_reps} @RPE {ex.target_rpe} | {ex.rest_seconds}s
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {microcycle.ai_justification && (
        <div className={styles.justificationCard}>
          <h2 className={styles.justificationTitle}>
            🤖 Justificativa da IA
          </h2>
          <p className={styles.justificationText}>
            {microcycle.ai_justification}
          </p>
        </div>
      )}
    </div>
  );
}
