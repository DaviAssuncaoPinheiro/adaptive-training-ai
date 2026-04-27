'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useCheckIn(userId) {
  const [checkIns, setCheckIns] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabase = useMemo(() => createClient(), []);

  const fetchCheckIns = useCallback(async () => {
    if (!userId) {
      setCheckIns([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    const { data, error } = await supabase
      .from('check_ins')
      .select('*')
      .eq('user_id', userId)
      .order('check_in_date', { ascending: false });

    if (!error) setCheckIns(data || []);
    setLoading(false);
  }, [supabase, userId]);

  useEffect(() => {
    const timerId = setTimeout(() => {
      fetchCheckIns();
    }, 0);

    return () => clearTimeout(timerId);
  }, [fetchCheckIns]);

  const addCheckIn = async (checkInData) => {
    const { data, error } = await supabase
      .from('check_ins')
      .upsert(
        { ...checkInData, user_id: userId },
        { onConflict: 'user_id,check_in_date' }
      )
      .select()
      .single();

    if (!error && data) {
      setCheckIns((prev) => [data, ...prev.filter((item) => item.id !== data.id)]);
    }
    return { data, error };
  };

  return { checkIns, loading, addCheckIn, refetch: fetchCheckIns };
}
