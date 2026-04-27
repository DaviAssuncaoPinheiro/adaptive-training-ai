'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useProfile(userId) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const supabase = useMemo(() => createClient(), []);

  const fetchProfile = useCallback(async () => {
    if (!userId) {
      setProfile(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    const { data } = await supabase
      .from('profiles')
      .select('*')
      .eq('user_id', userId)
      .maybeSingle();
    setProfile(data);
    setLoading(false);
  }, [supabase, userId]);

  useEffect(() => {
    const timerId = setTimeout(() => {
      fetchProfile();
    }, 0);

    return () => clearTimeout(timerId);
  }, [fetchProfile]);

  const saveProfile = async (next) => {
    const payload = { ...next, user_id: userId };
    const { data, error } = await supabase
      .from('profiles')
      .upsert(payload, { onConflict: 'user_id' })
      .select()
      .single();
    if (!error && data) setProfile(data);
    return { data, error };
  };

  return { profile, loading, saveProfile, refetch: fetchProfile };
}
