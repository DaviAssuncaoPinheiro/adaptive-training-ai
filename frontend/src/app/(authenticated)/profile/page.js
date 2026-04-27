'use client';

import { useEffect, useState } from 'react';
import { useAuthContext } from '@/context/AuthProvider';
import { useProfile } from '@/hooks/useProfile';
import Button from '@/components/ui/Button';
import Input, { Select } from '@/components/ui/Input';
import styles from './profile.module.css';

const EQUIPMENT_OPTIONS = [
  'Barra Reta', 'Halteres', 'Anilhas', 'Banco Ajustável',
  'Polia/Cabo', 'Barra Fixa', 'Leg Press', 'Smith Machine',
  'Kettlebell', 'Elásticos', 'Apenas Corpo',
];

const emptyForm = {
  age: '',
  weight_kg: '',
  height_cm: '',
  fitness_level: 'beginner',
  primary_goal: 'hypertrophy',
  available_equipment: [],
};

export default function ProfilePage() {
  const { user } = useAuthContext();
  const { profile, loading, saveProfile } = useProfile(user?.id);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    if (!profile) return;
    setForm({
      age: String(profile.age ?? ''),
      weight_kg: String(profile.weight_kg ?? ''),
      height_cm: String(profile.height_cm ?? ''),
      fitness_level: profile.fitness_level ?? 'beginner',
      primary_goal: profile.primary_goal ?? 'hypertrophy',
      available_equipment: profile.available_equipment ?? [],
    });
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
      available_equipment: form.available_equipment,
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
        Atualize os dados que alimentam a prescrição da IA.
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
          <h2 className={styles.sectionTitle}>Nível & objetivo</h2>
          <div className={styles.row}>
            <Select
              id="profile-level"
              label="Nível"
              value={form.fitness_level}
              onChange={(e) => updateField('fitness_level', e.target.value)}
            >
              <option value="beginner">Iniciante</option>
              <option value="intermediate">Intermediário</option>
              <option value="advanced">Avançado</option>
            </Select>
            <Select
              id="profile-goal"
              label="Objetivo"
              value={form.primary_goal}
              onChange={(e) => updateField('primary_goal', e.target.value)}
            >
              <option value="hypertrophy">Hipertrofia</option>
              <option value="strength">Força</option>
              <option value="endurance">Resistência</option>
              <option value="weight_loss">Emagrecimento</option>
            </Select>
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Equipamentos disponíveis</h2>
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
          Salvar alterações
        </Button>
      </form>
    </div>
  );
}
