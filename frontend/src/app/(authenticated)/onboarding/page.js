'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/context/AuthProvider';
import { createClient } from '@/lib/supabase/client';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { Select } from '@/components/ui/Input';
import styles from './onboarding.module.css';

const EQUIPMENT_OPTIONS = [
  'Barra Reta', 'Halteres', 'Anilhas', 'Banco Ajustável',
  'Polia/Cabo', 'Barra Fixa', 'Leg Press', 'Smith Machine',
  'Kettlebell', 'Elásticos', 'Apenas Corpo',
];

const TOTAL_STEPS = 3;

export default function OnboardingPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const supabase = createClient();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    age: '',
    weight_kg: '',
    height_cm: '',
    fitness_level: 'beginner',
    primary_goal: 'hypertrophy',
    available_equipment: [],
  });

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

    const { error } = await supabase.from('profiles').upsert({
      user_id: user.id,
      age: parseInt(formData.age),
      weight_kg: parseFloat(formData.weight_kg),
      height_cm: parseFloat(formData.height_cm),
      fitness_level: formData.fitness_level,
      primary_goal: formData.primary_goal,
      available_equipment: formData.available_equipment,
    });

    setLoading(false);
    if (!error) {
      router.push('/dashboard');
    }
  };

  return (
    <div className={styles.onboardingPage}>
      <div className={styles.onboardingCard}>
        <div className={styles.onboardingHeader}>
          <h1 className={styles.onboardingTitle}>Anamnese Inicial</h1>
          <p className={styles.onboardingSubtitle}>
            Passo {step} de {TOTAL_STEPS} — Vamos conhecer seu perfil
          </p>
        </div>

        {/* Progress bar */}
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

        {/* Step 1: Dados pessoais */}
        {step === 1 && (
          <div className={styles.stepContent}>
            <div>
              <h2 className={styles.stepTitle}>Dados Pessoais</h2>
              <p className={styles.stepDescription}>
                Informações básicas para calibrar as prescrições.
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

        {/* Step 2: Nível e objetivo */}
        {step === 2 && (
          <div className={styles.stepContent}>
            <div>
              <h2 className={styles.stepTitle}>Nível & Objetivo</h2>
              <p className={styles.stepDescription}>
                Isto define a intensidade e a progressão do seu treino.
              </p>
            </div>
            <Select
              id="onb-level"
              label="Nível de condicionamento"
              value={formData.fitness_level}
              onChange={(e) => updateField('fitness_level', e.target.value)}
            >
              <option value="beginner">Iniciante</option>
              <option value="intermediate">Intermediário</option>
              <option value="advanced">Avançado</option>
            </Select>
            <Select
              id="onb-goal"
              label="Objetivo principal"
              value={formData.primary_goal}
              onChange={(e) => updateField('primary_goal', e.target.value)}
            >
              <option value="hypertrophy">Hipertrofia</option>
              <option value="strength">Força</option>
              <option value="endurance">Resistência</option>
              <option value="weight_loss">Emagrecimento</option>
            </Select>
          </div>
        )}

        {/* Step 3: Equipamentos */}
        {step === 3 && (
          <div className={styles.stepContent}>
            <div>
              <h2 className={styles.stepTitle}>Equipamentos Disponíveis</h2>
              <p className={styles.stepDescription}>
                Selecione tudo que você tem acesso. Isto personaliza os exercícios prescritos.
              </p>
            </div>
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

        {/* Navigation */}
        <div className={styles.stepActions}>
          {step > 1 ? (
            <Button variant="secondary" onClick={() => setStep(step - 1)}>
              Voltar
            </Button>
          ) : (
            <div />
          )}

          {step < TOTAL_STEPS ? (
            <Button onClick={() => setStep(step + 1)}>Próximo</Button>
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
