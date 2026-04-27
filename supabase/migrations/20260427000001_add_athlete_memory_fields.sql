-- Athlete memory fields used by the adaptive prescription engine.
-- These fields are stable inputs captured during onboarding and editable later.

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS weekly_frequency INTEGER CHECK (weekly_frequency >= 1 AND weekly_frequency <= 7),
    ADD COLUMN IF NOT EXISTS session_duration_minutes INTEGER CHECK (session_duration_minutes >= 15 AND session_duration_minutes <= 180),
    ADD COLUMN IF NOT EXISTS injury_notes TEXT,
    ADD COLUMN IF NOT EXISTS exercise_preferences TEXT,
    ADD COLUMN IF NOT EXISTS training_constraints TEXT;
