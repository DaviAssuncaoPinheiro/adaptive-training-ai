-- Async generation jobs for microcycles.
-- Each row tracks one background generation triggered by a user.

CREATE TABLE public.microcycle_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'done', 'failed')),
    error TEXT,
    microcycle_id UUID REFERENCES public.microcycles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX microcycle_jobs_user_idx
    ON public.microcycle_jobs (user_id, created_at DESC);

ALTER TABLE public.microcycle_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own microcycle jobs"
    ON public.microcycle_jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own microcycle jobs"
    ON public.microcycle_jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own microcycle jobs"
    ON public.microcycle_jobs FOR UPDATE
    USING (auth.uid() = user_id);
