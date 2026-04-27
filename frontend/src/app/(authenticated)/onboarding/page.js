'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/context/AuthProvider';
import { useProfile } from '@/hooks/useProfile';
import { createClient } from '@/lib/supabase/client';
import Button from '@/components/ui/Button';
import Input, { Select } from '@/components/ui/Input';
import styles from './onboarding.module.css';

const EQUIPMENT_OPTIONS = [
  'Barra Reta', 'Halteres', 'Anilhas', 'Banco Ajustavel',
  'Polia/Cabo', 'Barra Fixa', 'Leg Press', 'Smith Machine',
  'Kettlebell', 'Elasticos', 'Apenas Corpo',
];

const TOTAL_STEPS = 4;

export default function OnboardingPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const supabase = useMemo(() => createClient(), []);
  const { profile } = useProfile(user?.id);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hydratedFromProfile, setHydratedFromProfile] = useState(false);

  const [formData, setFormData] = useState({
    age: '',
    weight_kg: '',
    height_cm: '',
    fitness_level: 'beginner',
    primary_goal: 'hypertrophy',
    weekly_frequency: '4',
    session_duration_minutes: '60',
    available_equipment: [],
    injury_notes: '',
    exercise_preferences: '',
    training_constraints: '',
  });

  useEffect(() => {
    if (!profile || hydratedFromProfile) return;
    const timerId = setTimeout(() => {
      setFormData(profileToFormData(profile));
      setHydratedFromProfile(true);
    }, 0);
    return () => clearTimeout(timerId);
  }, [hydratedFromProfile, profile]);

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleEquipment = (item) => {
    setFormData((prev) => ({
      ...prev,
      available_equipment: prev.available_equipment.includes(item)
        ? prev.available_equipment.filter((e) => e !== item)
        : [...prev.available_equipment, item],
    }));
  };

  const handleSubmit = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);

    const { error: saveError } = await supabase.from('profiles').upsert({
      user_id: user.id,
      age: parseInt(formData.age, 10),
      weight_kg: parseFloat(formData.weight_kg),
      height_cm: parseFloat(formData.height_cm),
      fitness_level: formData.fitness_level,
      primary_goal: formData.primary_goal,
      weekly_frequency: parseInt(formData.weekly_frequency, 10),
      session_duration_minutes: parseInt(formData.session_duration_minutes, 10),
      available_equipment: formData.available_equipment,
      injury_notes: formData.injury_notes || null,
      exercise_preferences: formData.exercise_preferences || null,
      training_constraints: formData.training_constraints || null,
    });

    setLoading(false);
    if (saveError) {
      if (isMissingMemoryColumn(saveError)) {
        setError('O banco ainda precisa aplicar a migration dos campos de memoria do atleta antes de salvar esta anamnese.');
      } else {
        setError(saveError.message || 'Nao foi possivel salvar sua anamnese.');
      }
      return;
    }

    router.push('/dashboard');
  };

  return (
    <div className={styles.onboardingPage}>
      <div className={styles.onboardingCard}>
        <div className={styles.onboardingHeader}>
          <h1 className={styles.onboardingTitle}>Anamnese Inicial</h1>
          <p className={styles.onboardingSubtitle}>
            Passo {step} de {TOTAL_STEPS} - memoria base para a prescricao.
          </p>
        </div>

        <div className={styles.progressBar}>
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <div
              key={i}
              className={`${styles.progressStep} ${
                i < step ? styles.progressStepActive : ''
              }`}
            />
          ))}
        </div>

        {step === 1 && (
          <div className={styles.stepContent}>
            <div>
              <h2 className={styles.stepTitle}>Dados pessoais</h2>
              <p className={styles.stepDescription}>
                Informacoes fisicas usadas para calibrar volume, progressao e seguranca.
              </p>
            </div>
            <Input
              id="onb-age"
              label="Idade"
              type="number"
              placeholder="25"
              value={formData.age}
              onChange={(e) => updateField('age', e.target.value)}
              min="14"
              max="100"
              required
            />
            <Input
              id="onb-weight"
              label="Peso (kg)"
              type="number"
              placeholder="75"
              step="0.1"
              value={formData.weight_kg}
              onChange={(e) => updateField('weight_kg', e.target.value)}
              required
            />
            <Input
              id="onb-height"
              label="Altura (cm)"
              type="number"
              placeholder="175"
              value={formData.height_cm}
              onChange={(e) => updateField('height_cm', e.target.value)}
              required
            />
          </div>
        )}

        {step === 2 && (
          <div className={styles.stepContent}>
            <div>
              <h2 className={styles.stepTitle}>Rotina de treino</h2>
              <p className={styles.stepDescription}>
                O motor usa disponibilidade real para nao prescrever um plano que voce nao consegue executar.
              </p>
            </div>
            <Input
              id="onb-frequency"
              label="Dias por semana"
              type="number"
              min="1"
              max="7"
              value={formData.weekly_frequency}
              onChange={(e) => updateField('weekly_frequency', e.target.value)}
              required
            />
            <Input
              id="onb-duration"
              label="Tempo por sessao (min)"
              type="number"
              min="15"
              max="180"
              step="5"
              value={formData.session_duration_minutes}
              onChange={(e) => updateField('session_duration_minutes', e.target.value)}
              required
            />
            <Select
              id="onb-goal"
              label="Objetivo principal"
              value={formData.primary_goal}
              onChange={(e) => updateField('primary_goal', e.target.value)}
            >
              <option value="hypertrophy">Hipertrofia</option>
              <option value="strength">Forca</option>
              <option value="endurance">Resistencia</option>
              <option value="weight_loss">Emagrecimento</option>
            </Select>
          </div>
        )}

        {step === 3 && (
          <div className={styles.stepContent}>
            <div>
              <h2 className={styles.stepTitle}>Nivel & equipamentos</h2>
              <p className={styles.stepDescription}>
                Selecione tudo que voce tem acesso. Isso restringe os exercicios prescritos.
              </p>
            </div>
            <Select
              id="onb-level"
              label="Nivel de condicionamento"
              value={formData.fitness_level}
              onChange={(e) => updateField('fitness_level', e.target.value)}
            >
              <option value="beginner">Iniciante</option>
              <option value="intermediate">Intermediario</option>
              <option value="advanced">Avancado</option>
            </Select>
            <div className={styles.chipGrid}>
              {EQUIPMENT_OPTIONS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`${styles.chip} ${
                    formData.available_equipment.includes(item)
                      ? styles.chipSelected
                      : ''
                  }`}
                  onClick={() => toggleEquipment(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 4 && (
          <div className={styles.stepContent}>
            <div>
              <h2 className={styles.stepTitle}>Restricoes & preferencias</h2>
              <p className={styles.stepDescription}>
                Aqui nasce a memoria do atleta. Depois voce pode editar tudo em Perfil.
              </p>
            </div>
            <label className={styles.textareaField}>
              <span>Lesoes, dores ou restricoes</span>
              <textarea
                value={formData.injury_notes}
                onChange={(e) => updateField('injury_notes', e.target.value)}
                placeholder="Ex: ombro direito sensivel em desenvolvimento acima da cabeca."
                rows={3}
              />
            </label>
            <label className={styles.textareaField}>
              <span>Preferencias de exercicios</span>
              <textarea
                value={formData.exercise_preferences}
                onChange={(e) => updateField('exercise_preferences', e.target.value)}
                placeholder="Ex: prefiro leg press a agachamento livre; gosto de barras."
                rows={3}
              />
            </label>
            <label className={styles.textareaField}>
              <span>Restricoes de agenda ou contexto</span>
              <textarea
                value={formData.training_constraints}
                onChange={(e) => updateField('training_constraints', e.target.value)}
                placeholder="Ex: treino em academia cheia de noite; sexta costuma ser curta."
                rows={3}
              />
            </label>
          </div>
        )}

        {error && <p className={styles.errorText}>{error}</p>}

        <div className={styles.stepActions}>
          {step > 1 ? (
            <Button variant="secondary" onClick={() => setStep(step - 1)}>
              Voltar
            </Button>
          ) : (
            <div />
          )}

          {step < TOTAL_STEPS ? (
            <Button onClick={() => setStep(step + 1)}>Proximo</Button>
          ) : (
            <Button onClick={handleSubmit} loading={loading}>
              Finalizar
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function isMissingMemoryColumn(error) {
  const text = `${error?.message || ''} ${error?.details || ''}`.toLowerCase();
  return [
    'weekly_frequency',
    'session_duration_minutes',
    'injury_notes',
    'exercise_preferences',
    'training_constraints',
  ].some((column) => text.includes(column));
}

function profileToFormData(profile) {
  return {
    age: profile.age ? String(profile.age) : '',
    weight_kg: profile.weight_kg ? String(profile.weight_kg) : '',
    height_cm: profile.height_cm ? String(profile.height_cm) : '',
    fitness_level: profile.fitness_level || 'beginner',
    primary_goal: profile.primary_goal || 'hypertrophy',
    weekly_frequency: profile.weekly_frequency ? String(profile.weekly_frequency) : '4',
    session_duration_minutes: profile.session_duration_minutes
      ? String(profile.session_duration_minutes)
      : '60',
    available_equipment: Array.isArray(profile.available_equipment)
      ? profile.available_equipment
      : [],
    injury_notes: profile.injury_notes || '',
    exercise_preferences: profile.exercise_preferences || '',
    training_constraints: profile.training_constraints || '',
  };
}
