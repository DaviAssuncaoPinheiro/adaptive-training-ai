/**
 * Formata um número para exibição com no máximo 1 casa decimal.
 */
export function formatNumber(value) {
  if (value === null || value === undefined) return '—';
  return Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 1 });
}

/**
 * Calcula o volume total (séries × reps × peso) a partir de um array de sets.
 */
export function calculateVolume(sets) {
  if (!sets || sets.length === 0) return 0;
  return sets.reduce((total, set) => total + set.reps * set.weight_kg, 0);
}

/**
 * Calcula a média de RPE de um array de sets que possuem RPE.
 */
export function calculateAvgRPE(sets) {
  if (!sets || sets.length === 0) return 0;
  const withRpe = sets.filter((s) => s.rpe !== null && s.rpe !== undefined);
  if (withRpe.length === 0) return 0;
  return withRpe.reduce((sum, s) => sum + s.rpe, 0) / withRpe.length;
}

/**
 * Retorna o nome do dia da semana em português.
 */
export function getDayName(dayNumber) {
  const days = ['', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];
  return days[dayNumber] || '';
}

/**
 * Formata uma data ISO para exibição pt-BR.
 */
export function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}
