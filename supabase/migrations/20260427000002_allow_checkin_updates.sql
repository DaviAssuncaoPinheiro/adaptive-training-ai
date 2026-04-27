-- Allow same-day check-up corrections without creating duplicate rows.

DROP POLICY IF EXISTS "Users can update their own check-ins" ON public.check_ins;

CREATE POLICY "Users can update their own check-ins"
    ON public.check_ins FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
