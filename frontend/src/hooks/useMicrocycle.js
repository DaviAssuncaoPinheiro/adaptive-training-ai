'use client';

import { useState, useEffect, useCallback } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useMicrocycle(userId) {
  const [microcycle, setMicrocycle] = useState(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  const fetchActive = useCallback(async () => {
    if (!userId) return;
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
  }, [userId]);

  useEffect(() => {
    fetchActive();
  }, [fetchActive]);

  return { microcycle, loading, refetch: fetchActive };
}
