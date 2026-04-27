'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const supabase = createClient();

  const toAuthError = (err) => {
    if (err?.message) return err;
    return {
      message:
        'Nao foi possivel conectar ao Supabase. Verifique as variaveis NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY.',
    };
  };

  const signUp = async (email, password) => {
    setLoading(true);
    setError(null);

    return supabase.auth
      .signUp({
        email,
        password,
      })
      .then(({ data, error: authError }) => {
        if (authError) setError(authError.message);
        return { data, error: authError };
      })
      .catch((err) => {
        const authError = toAuthError(err);
        setError(authError.message);
        return { data: null, error: authError };
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const signIn = async (email, password) => {
    setLoading(true);
    setError(null);

    return supabase.auth
      .signInWithPassword({
        email,
        password,
      })
      .then(({ data, error: authError }) => {
        if (authError) setError(authError.message);
        return { data, error: authError };
      })
      .catch((err) => {
        const authError = toAuthError(err);
        setError(authError.message);
        return { data: null, error: authError };
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch (err) {
      setError(toAuthError(err).message);
    }
  };

  return { signUp, signIn, signOut, loading, error };
}
