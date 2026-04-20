'use client';

import { useAuthContext } from '@/context/AuthProvider';
import { useWorkoutLog } from '@/hooks/useWorkoutLog';
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

const chartTooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: '8px',
  color: '#f1f5f9',
  fontSize: '0.8rem',
};

export default function DashboardPage() {
  const { user } = useAuthContext();
  const { logs, loading } = useWorkoutLog(user?.id);

  // Compute metrics
  const totalSessions = logs.length;

  const totalVolume = logs.reduce((sum, log) => {
    const sets = log.sets || [];
    return sum + sets.reduce((s, set) => s + (set.reps || 0) * (set.weight_kg || 0), 0);
  }, 0);

  const allSets = logs.flatMap((log) => log.sets || []);
  const avgRpe = calculateAvgRPE(allSets);

  // Chart data — recent sessions volume over time
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

  // RPE trend per session
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

  return (
    <div className={styles.dashboardPage}>
      <h1 className={styles.pageTitle}>Dashboard</h1>
      <p className={styles.pageSubtitle}>
        Visão geral da sua performance de treino
      </p>

      {/* Metrics */}
      <div className={`${styles.metricsGrid} stagger-children`}>
        <MetricCard value={totalSessions} label="Sessões Registradas" />
        <MetricCard value={formatNumber(totalVolume)} label="Volume Total (kg)" />
        <MetricCard
          value={avgRpe ? formatNumber(avgRpe) : '—'}
          label="RPE Médio"
        />
        <MetricCard
          value={allSets.length}
          label="Séries Totais"
        />
      </div>

      {/* Charts */}
      {logs.length > 0 ? (
        <div className={styles.chartsGrid}>
          <div className={styles.chartCard}>
            <h2 className={styles.chartTitle}>Evolução de Volume (kg)</h2>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={volumeOverTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="volume"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ fill: '#6366f1', r: 4 }}
                  activeDot={{ r: 6, fill: '#a78bfa' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className={styles.chartCard}>
            <h2 className={styles.chartTitle}>Tendência de RPE</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={rpeTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis domain={[0, 10]} stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar
                  dataKey="rpe"
                  fill="url(#rpeGradient)"
                  radius={[4, 4, 0, 0]}
                />
                <defs>
                  <linearGradient id="rpeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0.4} />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📊</div>
          <p>Nenhuma sessão registrada ainda.</p>
          <p>Registre seu primeiro treino para ver suas métricas aqui.</p>
        </div>
      )}
    </div>
  );
}
