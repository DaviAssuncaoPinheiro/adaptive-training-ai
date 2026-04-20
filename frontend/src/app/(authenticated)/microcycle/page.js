'use client';

import { useAuthContext } from '@/context/AuthProvider';
import { useMicrocycle } from '@/hooks/useMicrocycle';
import { getDayName, formatDate } from '@/lib/utils';
import styles from './microcycle.module.css';

export default function MicrocyclePage() {
  const { user } = useAuthContext();
  const { microcycle, loading } = useMicrocycle(user?.id);

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
          <p>Um novo plano será gerado quando houver dados suficientes no seu perfil.</p>
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

      {/* Safety badges */}
      <div className={styles.safetyRow}>
        <span className={`${styles.badge} ${styles.badgeInfo}`}>
          🛡️ Volume máx/músculo: {microcycle.max_weekly_sets_per_muscle} séries
        </span>
        <span className={`${styles.badge} ${styles.badgeWarning}`}>
          ⚠️ RPE cap: {microcycle.max_rpe_cap}/10
        </span>
      </div>

      {/* Workout cards */}
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

      {/* AI Justification */}
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
