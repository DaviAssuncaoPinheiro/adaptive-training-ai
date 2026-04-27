'use client';

import { useState } from 'react';
import { CalendarDays, FlaskConical, Gauge, ShieldCheck } from 'lucide-react';
import { useAuthContext } from '@/context/AuthProvider';
import { useMicrocycle } from '@/hooks/useMicrocycle';
import { useMicrocycleGeneration } from '@/hooks/useMicrocycleGeneration';
import Button from '@/components/ui/Button';
import { getDayName, formatDate } from '@/lib/utils';
import styles from './microcycle.module.css';

function WaveMotif() {
  return (
    <svg className={styles.wave} viewBox="0 0 900 82" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="microcycleWave" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="#ff4d2e" />
          <stop offset="45%" stopColor="#f7b26b" />
          <stop offset="100%" stopColor="#7fe3d4" />
        </linearGradient>
      </defs>
      <path
        d="M0 46 C96 4 156 4 252 46 S408 88 504 46 S660 4 756 46 S852 88 900 46"
        stroke="url(#microcycleWave)"
      />
    </svg>
  );
}

export default function MicrocyclePage() {
  const { user } = useAuthContext();
  const { microcycle, loading, refetch } = useMicrocycle(user?.id);
  const [adjustment, setAdjustment] = useState('');
  const [briefing, setBriefing] = useState({
    weekly_focus: '',
    constraints: '',
    intensity_preference: 'auto',
  });

  const generation = useMicrocycleGeneration({
    onDone: () => refetch(),
  });

  const isGenerating = generation.status === 'generating';
  const updateBriefing = (field, value) =>
    setBriefing((prev) => ({ ...prev, [field]: value }));
  const requestAdjustment = () => {
    if (!adjustment.trim()) return;
    generation.generate({
      weekly_focus: `Ajustar microciclo ativo conforme pedido do atleta: ${adjustment}`,
      constraints: adjustment,
      intensity_preference: 'auto',
    });
  };

  if (loading) {
    return (
      <div className={styles.microcyclePage}>
        <p className={styles.eyebrow}>№ 04 · Microciclo</p>
        <h1 className={styles.pageTitle}>Microciclo</h1>
        <p className={styles.pageSubtitle}>Carregando prescrição semanal.</p>
      </div>
    );
  }

  if (!microcycle) {
    return (
      <div className={styles.microcyclePage}>
        <header className={styles.pageHeader}>
          <p className={styles.eyebrow}>№ 04 · Microciclo</p>
          <h1 className={styles.pageTitle}>Microciclo</h1>
          <p className={styles.pageSubtitle}>
            Plano semanal de treino gerado pela IA a partir do seu perfil e histórico.
          </p>
        </header>

        <div className={styles.emptyState}>
          <CalendarDays aria-hidden="true" size={42} strokeWidth={1.4} />
          <p>Nenhum microciclo ativo encontrado.</p>
          <span>Antes de gerar, informe o briefing da semana. Isso evita plano generico e reduz conversa desnecessaria.</span>
          <div className={styles.briefingForm}>
            <label className={styles.textareaField}>
              <span>Foco da semana</span>
              <textarea
                value={briefing.weekly_focus}
                onChange={(e) => updateBriefing('weekly_focus', e.target.value)}
                placeholder="Ex: priorizar costas e manter pernas moderado."
                rows={3}
              />
            </label>
            <label className={styles.textareaField}>
              <span>Restricoes desta semana</span>
              <textarea
                value={briefing.constraints}
                onChange={(e) => updateBriefing('constraints', e.target.value)}
                placeholder="Ex: sexta sem treino; ombro direito sensivel; tenho 45 min por sessao."
                rows={3}
              />
            </label>
            <label className={styles.selectField}>
              <span>Agressividade</span>
              <select
                value={briefing.intensity_preference}
                onChange={(e) => updateBriefing('intensity_preference', e.target.value)}
              >
                <option value="auto">Automatica</option>
                <option value="conservative">Conservadora</option>
                <option value="standard">Padrao</option>
                <option value="aggressive">Mais agressiva</option>
              </select>
            </label>
          </div>
          <Button onClick={() => generation.generate(briefing)} loading={isGenerating}>
            {isGenerating ? 'Gerando microciclo...' : 'Gerar com briefing'}
          </Button>
          {isGenerating && (
            <span className={styles.helperText}>
              O motor esta combinando memoria do atleta, check-ups, historico e briefing.
            </span>
          )}
          {generation.status === 'failed' && (
            <span className={styles.errorText}>Erro: {generation.error}</span>
          )}
        </div>
      </div>
    );
  }

  const workouts = microcycle.workouts || [];

  return (
    <div className={styles.microcyclePage}>
      <header className={styles.pageHeader}>
        <div>
          <p className={styles.eyebrow}>№ 04 · Microciclo</p>
          <h1 className={styles.pageTitle}>Microciclo</h1>
          <p className={styles.pageSubtitle}>
            {formatDate(microcycle.start_date)} - {formatDate(microcycle.end_date)}
          </p>
        </div>
      </header>

      <WaveMotif />

      <div className={styles.safetyRow}>
        <span className={`${styles.badge} ${styles.badgeInfo}`}>
          <ShieldCheck aria-hidden="true" size={15} strokeWidth={1.6} />
          Volume max/musculo: {microcycle.max_weekly_sets_per_muscle} series
        </span>
        <span className={`${styles.badge} ${styles.badgeWarning}`}>
          <Gauge aria-hidden="true" size={15} strokeWidth={1.6} />
          RPE cap: {microcycle.max_rpe_cap}/10
        </span>
      </div>

      <div className={`${styles.workoutsGrid} stagger-children`}>
        {workouts.map((workout, i) => (
          <div key={`${workout.day_of_week}-${i}`} className={styles.workoutCard}>
            <div className={styles.workoutEyebrow}>№ {String(i + 1).padStart(2, '0')}</div>
            <div className={styles.workoutDay}>{getDayName(workout.day_of_week)}</div>
            <div className={styles.workoutName}>{workout.session_name}</div>

            <div className={styles.exerciseList}>
              {(workout.exercises || []).map((ex, j) => (
                <div key={`${ex.exercise_name}-${j}`} className={styles.exerciseRow}>
                  <span className={styles.exerciseName}>{ex.exercise_name}</span>
                  <span className={styles.exerciseMeta}>
                    {ex.target_sets}x{ex.target_reps} @ RPE {ex.target_rpe} · {ex.rest_seconds}s
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {microcycle.ai_justification && (
        <div className={styles.justificationCard}>
          <div className={styles.justificationTitle}>
            <FlaskConical aria-hidden="true" size={18} strokeWidth={1.6} />
            <span>Justificativa fundamentada pela IA</span>
          </div>
          <p className={styles.justificationText}>{microcycle.ai_justification}</p>
        </div>
      )}

      <div className={styles.adjustmentCard}>
        <div>
          <p className={styles.eyebrow}>No. 05 · Ajuste sob demanda</p>
          <h2 className={styles.adjustmentTitle}>Conversar com a IA somente quando precisar</h2>
          <p className={styles.adjustmentCopy}>
            Descreva uma troca, restricao ou sensacao importante. O sistema gera uma nova versao do microciclo usando o plano atual, seu perfil e os check-ups.
          </p>
        </div>
        <textarea
          className={styles.adjustmentTextarea}
          value={adjustment}
          onChange={(event) => setAdjustment(event.target.value)}
          placeholder="Ex: troca agachamento por leg press esta semana; ombro direito incomodou no supino."
          rows={3}
        />
        <Button
          type="button"
          variant="secondary"
          onClick={requestAdjustment}
          loading={isGenerating}
          disabled={!adjustment.trim()}
        >
          Pedir ajuste a IA
        </Button>
        {generation.status === 'failed' && (
          <span className={styles.errorText}>Erro: {generation.error}</span>
        )}
      </div>
    </div>
  );
}
