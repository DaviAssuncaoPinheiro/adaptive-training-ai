'use client';

import { useState, useEffect, useCallback } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useWorkoutLog(userId) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  const fetchLogs = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    const { data, error } = await supabase
      .from('workout_logs')
      .select('*')
      .eq('user_id', userId)
      .order('session_date', { ascending: false });

    if (!error) setLogs(data || []);
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const addLog = async (logData) => {
    const { data, error } = await supabase
      .from('workout_logs')
      .insert({ ...logData, user_id: userId })
      .select()
      .single();

    if (!error && data) {
      setLogs((prev) => [data, ...prev]);
    }
    return { data, error };
  };

  return { logs, loading, addLog, refetch: fetchLogs };
}
