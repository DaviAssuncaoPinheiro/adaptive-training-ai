'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const supabase = createClient();

  const signUp = async (email, password) => {
    setLoading(true);
    setError(null);
    const { data, error: authError } = await supabase.auth.signUp({
      email,
      password,
    });
    setLoading(false);
    if (authError) setError(authError.message);
    return { data, error: authError };
  };

  const signIn = async (email, password) => {
    setLoading(true);
    setError(null);
    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    setLoading(false);
    if (authError) setError(authError.message);
    return { data, error: authError };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return { signUp, signIn, signOut, loading, error };
}
