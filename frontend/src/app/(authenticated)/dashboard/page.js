'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, LineChart as EmptyChartIcon } from 'lucide-react';
import { useAuthContext } from '@/context/AuthProvider';
import { useWorkoutLog } from '@/hooks/useWorkoutLog';
import { useCheckIn } from '@/hooks/useCheckIn';
import { useProfile } from '@/hooks/useProfile';
import Button from '@/components/ui/Button';
import { MetricCard } from '@/components/ui/Card';
import { formatNumber, calculateAvgRPE } from '@/lib/utils';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import styles from './dashboard.module.css';

const CHECKUP_FIELDS = [
  { key: 'sleep_quality', label: 'Sono', good: true },
  { key: 'energy_level', label: 'Energia', good: true },
  { key: 'muscle_soreness', label: 'Dor muscular', good: false },
  { key: 'stress_level', label: 'Estresse', good: false },
  { key: 'fatigue_level', label: 'Fadiga', good: false },
];

const chartTooltipStyle = {
  backgroundColor: '#131316',
  border: '1px solid rgba(255,255,255,0.12)',
  borderRadius: '4px',
  color: '#e8e6e1',
  fontSize: '0.8rem',
};

const todayISO = () => new Date().toISOString().slice(0, 10);

function computeReadiness(values) {
  if (!values) return null;
  const positive = [values.sleep_quality, values.energy_level]
    .filter((v) => typeof v === 'number');
  const negative = [values.muscle_soreness, values.stress_level, values.fatigue_level]
    .filter((v) => typeof v === 'number');

  if (!positive.length || !negative.length) return null;

  const positiveAvg = positive.reduce((sum, value) => sum + value, 0) / positive.length;
  const negativeAvg = negative.reduce((sum, value) => sum + value, 0) / negative.length;
  return Math.round(((positiveAvg / 10) * 50) + (((10 - negativeAvg) / 10) * 50));
}

function readinessCopy(score) {
  if (score === null) {
    return {
      title: 'Sem dados de prontidao',
      body: 'Faca o check-up de hoje para calibrar o treino e o proximo microciclo.',
      tone: 'muted',
    };
  }

  if (score >= 75) {
    return {
      title: 'Pronto para progredir',
      body: 'Boa janela de recuperacao. Manter plano, com espaco para progressao conservadora.',
      tone: 'good',
    };
  }

  if (score >= 55) {
    return {
      title: 'Treino normal, com cap',
      body: 'Manter estrutura do dia. Evitar falha e limitar top sets em RPE 8.',
      tone: 'warn',
    };
  }

  return {
    title: 'Recuperacao limitada',
    body: 'Reduzir volume ou transformar a sessao em tecnica/deload. Sinal relevante para o proximo microciclo.',
    tone: 'risk',
  };
}

export default function DashboardPage() {
  const { user } = useAuthContext();
  const { logs } = useWorkoutLog(user?.id);
  const { checkIns, addCheckIn } = useCheckIn(user?.id);
  const { profile } = useProfile(user?.id);
  const [checkup, setCheckup] = useState({
    sleep_quality: 5,
    energy_level: 5,
    muscle_soreness: 5,
    stress_level: 5,
    fatigue_level: 5,
  });
  const [savingCheckup, setSavingCheckup] = useState(false);
  const [checkupError, setCheckupError] = useState(null);

  const todayCheckIn = useMemo(() => {
    const today = todayISO();
    return checkIns.find((item) => item.check_in_date === today);
  }, [checkIns]);

  const readinessSource = todayCheckIn || checkup;
  const readiness = computeReadiness(readinessSource);
  const readinessInfo = readinessCopy(readiness);
  const needsAnamnesis = !profile || (
    !profile.weekly_frequency ||
    !profile.session_duration_minutes ||
    !profile.available_equipment
  );

  const totalSessions = logs.length;
  const totalVolume = logs.reduce((sum, log) => {
    const sets = log.sets || [];
    return sum + sets.reduce((s, set) => s + (set.reps || 0) * (set.weight_kg || 0), 0);
  }, 0);
  const allSets = logs.flatMap((log) => log.sets || []);
  const avgRpe = calculateAvgRPE(allSets);

  const volumeOverTime = logs
    .slice(0, 12)
    .reverse()
    .map((log) => {
      const sets = log.sets || [];
      const vol = sets.reduce((s, set) => s + (set.reps || 0) * (set.weight_kg || 0), 0);
      const date = new Date(log.session_date).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
      });
      return { date, volume: vol };
    });

  const rpeTrend = logs
    .slice(0, 12)
    .reverse()
    .map((log) => {
      const sets = log.sets || [];
      const rpe = calculateAvgRPE(sets);
      const date = new Date(log.session_date).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
      });
      return { date, rpe: parseFloat(rpe.toFixed(1)) };
    });

  const handleCheckupSubmit = async (event) => {
    event.preventDefault();
    if (!user) return;

    setSavingCheckup(true);
    setCheckupError(null);
    const { error } = await addCheckIn({
      ...checkup,
      check_in_date: todayISO(),
    });
    setSavingCheckup(false);

    if (error) {
      setCheckupError(error.message || 'Nao foi possivel salvar o check-up.');
    }
  };

  return (
    <div className={styles.dashboardPage}>
      <header className={styles.pageHeader}>
        <div>
          <p className={styles.eyebrow}>№ 01 · Performance</p>
          <h1 className={styles.pageTitle}>Dashboard</h1>
          <p className={styles.pageSubtitle}>
            Centro diario de decisao: prontidao, carga recente e proximo ajuste.
          </p>
        </div>
        <span className={styles.headerMeta}>
          {new Date().toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
          })}
        </span>
      </header>

      <section className={styles.commandGrid}>
        {needsAnamnesis && (
          <div className={styles.profileNotice}>
            <div>
              <p className={styles.eyebrow}>No. 00 · Anamnese incompleta</p>
              <h2>Complete o formulario inicial</h2>
              <span>
                Sua conta ja existia. Falta atualizar a memoria base para o microciclo usar rotina, restricoes e preferencias.
              </span>
            </div>
            <Link href="/onboarding" className={styles.noticeAction}>
              Completar agora
            </Link>
          </div>
        )}

        <div className={styles.checkupCard}>
          <div className={styles.cardHeaderLine}>
            <div>
              <p className={styles.eyebrow}>№ 00 · Check-up diario</p>
              <h2 className={styles.cardTitle}>
                {todayCheckIn ? 'Check-up concluido' : 'Check-up pendente'}
              </h2>
            </div>
            {todayCheckIn && (
              <span className={styles.doneBadge}>
                <CheckCircle2 aria-hidden="true" size={15} strokeWidth={1.7} />
                salvo
              </span>
            )}
          </div>

          {todayCheckIn ? (
            <div className={styles.checkupDone}>
              <div className={styles.readinessNumber}>{readiness}</div>
              <div>
                <p className={styles.readinessLabel}>Readiness /100</p>
                <h2 className={styles.cardTitle}>{readinessInfo.title}</h2>
                <p className={styles.readinessText}>{readinessInfo.body}</p>
                <div className={styles.signalRows}>
                  <span>Uso no sistema</span>
                  <strong>microciclo · carga · deload</strong>
                </div>
              </div>
            </div>
          ) : (
            <form className={styles.checkupForm} onSubmit={handleCheckupSubmit}>
              {CHECKUP_FIELDS.map((field) => (
                <label key={field.key} className={styles.sliderField}>
                  <span className={styles.sliderLabel}>
                    {field.label}
                    <strong>{checkup[field.key]}</strong>
                  </span>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    step="1"
                    value={checkup[field.key]}
                    className={styles.slider}
                    onChange={(event) =>
                      setCheckup((prev) => ({
                        ...prev,
                        [field.key]: Number(event.target.value),
                      }))
                    }
                  />
                </label>
              ))}

              {checkupError && <p className={styles.errorText}>{checkupError}</p>}
              <Button type="submit" loading={savingCheckup} fullWidth>
                Salvar check-up
              </Button>
            </form>
          )}
        </div>
      </section>

      <div className={`${styles.metricsGrid} stagger-children`}>
        <MetricCard
          eyebrow="Sessoes"
          value={totalSessions}
          label="Sessões registradas"
          delta="n total"
        />
        <MetricCard
          eyebrow="Volume"
          value={formatNumber(totalVolume)}
          unit="kg"
          label="Volume total"
        />
        <MetricCard
          eyebrow="RPE"
          value={avgRpe ? formatNumber(avgRpe) : '-'}
          unit="/10"
          label="RPE médio"
        />
        <MetricCard
          eyebrow="Series"
          value={allSets.length}
          label="Séries totais"
        />
      </div>

      {logs.length > 0 ? (
        <div className={styles.chartsGrid}>
          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <p className={styles.eyebrow}>№ 02 · Volume (kg)</p>
              <h2 className={styles.chartTitle}>Evolução de Volume</h2>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={volumeOverTime}>
                <CartesianGrid strokeDasharray="2 6" stroke="rgba(255,255,255,0.07)" />
                <XAxis dataKey="date" stroke="#686870" fontSize={11} tickLine={false} />
                <YAxis stroke="#686870" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="volume"
                  stroke="#ff4d2e"
                  strokeWidth={2}
                  dot={{ fill: '#ff4d2e', r: 3 }}
                  activeDot={{ r: 5, fill: '#ff4d2e', stroke: '#0b0b0d' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <p className={styles.eyebrow}>№ 03 · RPE</p>
              <h2 className={styles.chartTitle}>Tendência de RPE</h2>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={rpeTrend}>
                <CartesianGrid strokeDasharray="2 6" stroke="rgba(255,255,255,0.07)" />
                <XAxis dataKey="date" stroke="#686870" fontSize={11} tickLine={false} />
                <YAxis domain={[0, 10]} stroke="#686870" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="rpe" fill="#ff4d2e" radius={[1, 1, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className={styles.emptyState}>
          <EmptyChartIcon aria-hidden="true" size={42} strokeWidth={1.4} />
          <p>Nenhuma sessão registrada ainda.</p>
          <span>Registre seu primeiro treino para ver métricas, volume e RPE.</span>
        </div>
      )}
    </div>
  );
}
