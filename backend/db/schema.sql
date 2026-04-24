-- =============================================================================
-- Adaptive Training AI — Schema de Persistencia (Supabase PostgreSQL)
-- =============================================================================
-- Este script deve ser executado no SQL Editor do Supabase.
-- Todas as tabelas referenciam auth.users(id) para vincular dados ao usuario
-- autenticado. Row Level Security (RLS) garante isolamento por usuario.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. PROFILES
-- Dados demograficos e preferencias coletados durante o onboarding.
-- Fonte: backend/schemas/user.py (UserSchema)
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
    id            bigint generated always as identity primary key,
    user_id       uuid not null references auth.users(id) on delete cascade,
    age           integer not null check (age > 0),
    weight_kg     real not null check (weight_kg > 0),
    height_cm     real not null check (height_cm > 0),
    fitness_level text not null check (fitness_level in ('beginner', 'intermediate', 'advanced')),
    primary_goal  text not null check (primary_goal in ('hypertrophy', 'strength', 'endurance', 'weight_loss')),
    available_equipment text[] not null default '{}',
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),

    constraint profiles_user_id_unique unique (user_id)
);

comment on table public.profiles is 'Perfil demografico e preferencias do praticante.';

-- ---------------------------------------------------------------------------
-- 2. WORKOUT_LOGS
-- Registro completo de cada sessao de treino executada pelo praticante.
-- O campo "sets" armazena o array de series como JSONB para flexibilidade.
-- Fonte: backend/schemas/workout_log.py (WorkoutLogSchema, SetLog)
-- ---------------------------------------------------------------------------
create table if not exists public.workout_logs (
    id               bigint generated always as identity primary key,
    user_id          uuid not null references auth.users(id) on delete cascade,
    session_date     timestamptz not null,
    workout_name     text not null,
    duration_minutes integer not null check (duration_minutes > 0),
    sets             jsonb not null default '[]',
    notes            text,
    created_at       timestamptz not null default now()
);

comment on table public.workout_logs is 'Sessoes de treino executadas. Cada linha representa uma sessao completa.';

create index if not exists idx_workout_logs_user_date
    on public.workout_logs (user_id, session_date desc);

-- ---------------------------------------------------------------------------
-- 3. CHECK_INS
-- Metricas subjetivas de prontidao reportadas diariamente pelo praticante.
-- Fonte: backend/schemas/check_in.py (CheckInSchema)
-- ---------------------------------------------------------------------------
create table if not exists public.check_ins (
    id              bigint generated always as identity primary key,
    user_id         uuid not null references auth.users(id) on delete cascade,
    check_in_date   date not null,
    sleep_quality   integer not null check (sleep_quality between 1 and 10),
    energy_level    integer not null check (energy_level between 1 and 10),
    muscle_soreness integer not null check (muscle_soreness between 1 and 10),
    stress_level    integer not null check (stress_level between 1 and 10),
    fatigue_level   integer not null check (fatigue_level between 1 and 10),
    created_at      timestamptz not null default now(),

    constraint check_ins_user_date_unique unique (user_id, check_in_date)
);

comment on table public.check_ins is 'Check-in diario de prontidao, fadiga e recuperacao.';

create index if not exists idx_check_ins_user_date
    on public.check_ins (user_id, check_in_date desc);

-- ---------------------------------------------------------------------------
-- 4. MICROCYCLES
-- Plano semanal de treino gerado pela IA. "workouts" armazena a prescricao
-- completa como JSONB. Inclui metadados de seguranca (safety caps).
-- Fonte: backend/schemas/microcycle.py (MicrocycleSchema)
-- ---------------------------------------------------------------------------
create table if not exists public.microcycles (
    id                          bigint generated always as identity primary key,
    user_id                     uuid not null references auth.users(id) on delete cascade,
    start_date                  date not null,
    end_date                    date not null,
    workouts                    jsonb not null default '[]',
    ai_justification            text not null,
    max_weekly_sets_per_muscle  integer not null,
    max_rpe_cap                 integer not null default 10 check (max_rpe_cap between 1 and 10),
    created_at                  timestamptz not null default now(),

    constraint microcycles_date_range_valid check (end_date >= start_date)
);

comment on table public.microcycles is 'Microciclos semanais prescritos pela IA com limites de seguranca.';

create index if not exists idx_microcycles_user_dates
    on public.microcycles (user_id, start_date desc, end_date desc);

-- ---------------------------------------------------------------------------
-- 5. ROW LEVEL SECURITY (RLS)
-- Cada usuario so pode ler e escrever seus proprios dados.
-- ---------------------------------------------------------------------------

-- profiles
alter table public.profiles enable row level security;

create policy "Users can view own profile"
    on public.profiles for select
    using (auth.uid() = user_id);

create policy "Users can insert own profile"
    on public.profiles for insert
    with check (auth.uid() = user_id);

create policy "Users can update own profile"
    on public.profiles for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- workout_logs
alter table public.workout_logs enable row level security;

create policy "Users can view own workout logs"
    on public.workout_logs for select
    using (auth.uid() = user_id);

create policy "Users can insert own workout logs"
    on public.workout_logs for insert
    with check (auth.uid() = user_id);

-- check_ins
alter table public.check_ins enable row level security;

create policy "Users can view own check-ins"
    on public.check_ins for select
    using (auth.uid() = user_id);

create policy "Users can insert own check-ins"
    on public.check_ins for insert
    with check (auth.uid() = user_id);

-- microcycles
alter table public.microcycles enable row level security;

create policy "Users can view own microcycles"
    on public.microcycles for select
    using (auth.uid() = user_id);

create policy "Users can insert own microcycles"
    on public.microcycles for insert
    with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- 6. TRIGGER: auto-atualizar updated_at em profiles
-- ---------------------------------------------------------------------------
create or replace function public.handle_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger on_profiles_update
    before update on public.profiles
    for each row
    execute function public.handle_updated_at();
