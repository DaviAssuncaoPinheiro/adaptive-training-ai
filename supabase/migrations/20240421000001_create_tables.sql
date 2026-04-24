-- Tabela de Usuários (Profiles)
CREATE TABLE public.profiles (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    age INTEGER CHECK (age > 0),
    weight_kg NUMERIC CHECK (weight_kg > 0),
    height_cm NUMERIC CHECK (height_cm > 0),
    fitness_level TEXT NOT NULL,
    primary_goal TEXT NOT NULL,
    available_equipment JSONB DEFAULT '[]'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Tabela de Check-ins Diários
CREATE TABLE public.check_ins (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    check_in_date DATE NOT NULL,
    sleep_quality INTEGER CHECK (sleep_quality >= 1 AND sleep_quality <= 10),
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),
    muscle_soreness INTEGER CHECK (muscle_soreness >= 1 AND muscle_soreness <= 10),
    stress_level INTEGER CHECK (stress_level >= 1 AND stress_level <= 10),
    fatigue_level INTEGER CHECK (fatigue_level >= 1 AND fatigue_level <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, check_in_date)
);

-- Tabela de Logs de Treino (Sessão Executada)
CREATE TABLE public.workout_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    session_date TIMESTAMP WITH TIME ZONE NOT NULL,
    workout_name TEXT NOT NULL,
    duration_minutes INTEGER CHECK (duration_minutes > 0),
    sets JSONB DEFAULT '[]'::JSONB,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Tabela de Microciclos (Treinos Planejados pela IA)
CREATE TABLE public.microcycles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    workouts JSONB NOT NULL,
    ai_justification TEXT NOT NULL,
    max_weekly_sets_per_muscle INTEGER NOT NULL,
    max_rpe_cap INTEGER CHECK (max_rpe_cap <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
