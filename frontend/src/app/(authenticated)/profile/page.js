'use client';

import { useEffect, useState } from 'react';
import { useAuthContext } from '@/context/AuthProvider';
import { useProfile } from '@/hooks/useProfile';
import Button from '@/components/ui/Button';
import Input, { Select } from '@/components/ui/Input';
import styles from './profile.module.css';

const EQUIPMENT_OPTIONS = [
  'Barra Reta', 'Halteres', 'Anilhas', 'Banco Ajustavel',
  'Polia/Cabo', 'Barra Fixa', 'Leg Press', 'Smith Machine',
  'Kettlebell', 'Elasticos', 'Apenas Corpo',
];

const emptyForm = {
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
};

export default function ProfilePage() {
  const { user } = useAuthContext();
  const { profile, loading, saveProfile } = useProfile(user?.id);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    if (!profile) return;
    const timerId = setTimeout(() => {
      setForm({
        age: String(profile.age ?? ''),
        weight_kg: String(profile.weight_kg ?? ''),
        height_cm: String(profile.height_cm ?? ''),
        fitness_level: profile.fitness_level ?? 'beginner',
        primary_goal: profile.primary_goal ?? 'hypertrophy',
        weekly_frequency: String(profile.weekly_frequency ?? '4'),
        session_duration_minutes: String(profile.session_duration_minutes ?? '60'),
        available_equipment: profile.available_equipment ?? [],
        injury_notes: profile.injury_notes ?? '',
        exercise_preferences: profile.exercise_preferences ?? '',
        training_constraints: profile.training_constraints ?? '',
      });
    }, 0);

    return () => clearTimeout(timerId);
  }, [profile]);

  const updateField = (field, value) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const toggleEquipment = (item) =>
    setForm((prev) => ({
      ...prev,
      available_equipment: prev.available_equipment.includes(item)
        ? prev.available_equipment.filter((e) => e !== item)
        : [...prev.available_equipment, item],
    }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFeedback(null);

    const { error } = await saveProfile({
      age: parseInt(form.age, 10),
      weight_kg: parseFloat(form.weight_kg),
      height_cm: parseFloat(form.height_cm),
      fitness_level: form.fitness_level,
      primary_goal: form.primary_goal,
      weekly_frequency: parseInt(form.weekly_frequency, 10),
      session_duration_minutes: parseInt(form.session_duration_minutes, 10),
      available_equipment: form.available_equipment,
      injury_notes: form.injury_notes || null,
      exercise_preferences: form.exercise_preferences || null,
      training_constraints: form.training_constraints || null,
    });

    setSaving(false);
    setFeedback(
      error
        ? { type: 'error', message: error.message || 'Erro ao salvar' }
        : { type: 'success', message: 'Perfil atualizado.' }
    );
  };

  if (loading) {
    return (
      <div className={styles.profilePage}>
        <h1 className={styles.pageTitle}>Perfil</h1>
        <p className={styles.pageSubtitle}>Carregando...</p>
      </div>
    );
  }

  return (
    <div className={styles.profilePage}>
      <h1 className={styles.pageTitle}>Perfil</h1>
      <p className={styles.pageSubtitle}>
        Atualize a memoria do atleta que alimenta a prescricao da IA.
      </p>

      <form className={styles.card} onSubmit={handleSubmit}>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Dados pessoais</h2>
          <div className={styles.row}>
            <Input
              id="profile-age"
              label="Idade"
              type="number"
              min="14"
              max="100"
              value={form.age}
              onChange={(e) => updateField('age', e.target.value)}
              required
            />
            <Input
              id="profile-weight"
              label="Peso (kg)"
              type="number"
              step="0.1"
              value={form.weight_kg}
              onChange={(e) => updateField('weight_kg', e.target.value)}
              required
            />
            <Input
              id="profile-height"
              label="Altura (cm)"
              type="number"
              value={form.height_cm}
              onChange={(e) => updateField('height_cm', e.target.value)}
              required
            />
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Nivel & objetivo</h2>
          <div className={styles.row}>
            <Select
              id="profile-level"
              label="Nivel"
              value={form.fitness_level}
              onChange={(e) => updateField('fitness_level', e.target.value)}
            >
              <option value="beginner">Iniciante</option>
              <option value="intermediate">Intermediario</option>
              <option value="advanced">Avancado</option>
            </Select>
            <Select
              id="profile-goal"
              label="Objetivo"
              value={form.primary_goal}
              onChange={(e) => updateField('primary_goal', e.target.value)}
            >
              <option value="hypertrophy">Hipertrofia</option>
              <option value="strength">Forca</option>
              <option value="endurance">Resistencia</option>
              <option value="weight_loss">Emagrecimento</option>
            </Select>
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Rotina</h2>
          <div className={styles.row}>
            <Input
              id="profile-frequency"
              label="Dias por semana"
              type="number"
              min="1"
              max="7"
              value={form.weekly_frequency}
              onChange={(e) => updateField('weekly_frequency', e.target.value)}
              required
            />
            <Input
              id="profile-duration"
              label="Tempo por sessao (min)"
              type="number"
              min="15"
              max="180"
              step="5"
              value={form.session_duration_minutes}
              onChange={(e) => updateField('session_duration_minutes', e.target.value)}
              required
            />
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Equipamentos disponiveis</h2>
          <div className={styles.chipGrid}>
            {EQUIPMENT_OPTIONS.map((item) => (
              <button
                key={item}
                type="button"
                className={`${styles.chip} ${
                  form.available_equipment.includes(item) ? styles.chipSelected : ''
                }`}
                onClick={() => toggleEquipment(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Memoria do atleta</h2>
          <label className={styles.textareaField}>
            <span>Lesoes, dores ou restricoes</span>
            <textarea
              value={form.injury_notes}
              onChange={(e) => updateField('injury_notes', e.target.value)}
              placeholder="Ex: ombro direito sensivel em desenvolvimento acima da cabeca."
              rows={3}
            />
          </label>
          <label className={styles.textareaField}>
            <span>Preferencias de exercicios</span>
            <textarea
              value={form.exercise_preferences}
              onChange={(e) => updateField('exercise_preferences', e.target.value)}
              placeholder="Ex: prefiro leg press a agachamento livre; gosto de barras."
              rows={3}
            />
          </label>
          <label className={styles.textareaField}>
            <span>Restricoes de agenda ou contexto</span>
            <textarea
              value={form.training_constraints}
              onChange={(e) => updateField('training_constraints', e.target.value)}
              placeholder="Ex: sexta costuma ser curta; academia cheia no horario noturno."
              rows={3}
            />
          </label>
        </section>

        {feedback && (
          <p
            className={
              feedback.type === 'error' ? styles.feedbackError : styles.feedbackOk
            }
          >
            {feedback.message}
          </p>
        )}

        <Button type="submit" loading={saving} fullWidth>
          Salvar alteracoes
        </Button>
      </form>
    </div>
  );
}
