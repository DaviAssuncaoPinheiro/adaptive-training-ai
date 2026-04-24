-- Habilitar RLS em todas as tabelas
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.check_ins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.microcycles ENABLE ROW LEVEL SECURITY;

-- Políticas para Profiles
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- Políticas para Check-ins
CREATE POLICY "Users can view their own check-ins"
    ON public.check_ins FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own check-ins"
    ON public.check_ins FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Políticas para Workout Logs
CREATE POLICY "Users can view their own workout logs"
    ON public.workout_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own workout logs"
    ON public.workout_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Políticas para Microcycles
CREATE POLICY "Users can view their own microcycles"
    ON public.microcycles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own microcycles"
    ON public.microcycles FOR INSERT
    WITH CHECK (auth.uid() = user_id);
