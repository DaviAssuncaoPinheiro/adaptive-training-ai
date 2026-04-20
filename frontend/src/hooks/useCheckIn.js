'use client';

import { useState, useEffect, useCallback } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useCheckIn(userId) {
  const [checkIns, setCheckIns] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  const fetchCheckIns = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    const { data, error } = await supabase
      .from('check_ins')
      .select('*')
      .eq('user_id', userId)
      .order('check_in_date', { ascending: false });

    if (!error) setCheckIns(data || []);
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    fetchCheckIns();
  }, [fetchCheckIns]);

  const addCheckIn = async (checkInData) => {
    const { data, error } = await supabase
      .from('check_ins')
      .insert({ ...checkInData, user_id: userId })
      .select()
      .single();

    if (!error && data) {
      setCheckIns((prev) => [data, ...prev]);
    }
    return { data, error };
  };

  return { checkIns, loading, addCheckIn, refetch: fetchCheckIns };
}
