'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useMicrocycle(userId) {
  const [microcycle, setMicrocycle] = useState(null);
  const [loading, setLoading] = useState(true);
  const supabase = useMemo(() => createClient(), []);

  const fetchActive = useCallback(async () => {
    if (!userId) {
      setMicrocycle(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    const today = new Date().toISOString().split('T')[0];

    const { data, error } = await supabase
      .from('microcycles')
      .select('*')
      .eq('user_id', userId)
      .lte('start_date', today)
      .gte('end_date', today)
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (!error) setMicrocycle(data);
    setLoading(false);
  }, [supabase, userId]);

  useEffect(() => {
    const timerId = setTimeout(() => {
      fetchActive();
    }, 0);

    return () => clearTimeout(timerId);
  }, [fetchActive]);

  return { microcycle, loading, refetch: fetchActive };
}
