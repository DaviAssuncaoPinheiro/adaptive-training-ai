import { createBrowserClient } from '@supabase/ssr';

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const CONFIG_ERROR =
  'Supabase nao esta configurado. Defina NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY no frontend/.env.local.';

const CONNECTION_ERROR =
  'Nao foi possivel conectar ao Supabase. Verifique se o Supabase local esta rodando ou se as credenciais estao corretas.';

function errorResult(message) {
  return { data: null, error: { message } };
}

function createDisabledQuery(message) {
  const result = errorResult(message);

  const query = {
    select: () => query,
    eq: () => query,
    lte: () => query,
    gte: () => query,
    order: () => query,
    limit: () => query,
    insert: () => query,
    upsert: () => query,
    single: () => Promise.resolve(result),
    maybeSingle: () => Promise.resolve(result),
    then: (resolve, reject) => Promise.resolve(result).then(resolve, reject),
  };

  return query;
}

function createDisabledClient(message) {
  const authResult = () => Promise.resolve(errorResult(message));

  return {
    auth: {
      signUp: authResult,
      signInWithPassword: authResult,
      signOut: authResult,
      getSession: () => Promise.resolve({ data: { session: null }, error: null }),
      onAuthStateChange: () => ({
        data: {
          subscription: {
            unsubscribe: () => {},
          },
        },
      }),
    },
    from: () => createDisabledQuery(message),
  };
}

async function safeFetch(...args) {
  try {
    return await fetch(...args);
  } catch {
    return new Response(JSON.stringify({ message: CONNECTION_ERROR }), {
      status: 503,
      headers: { 'content-type': 'application/json' },
    });
  }
}

export function createClient() {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    return createDisabledClient(CONFIG_ERROR);
  }

  return createBrowserClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    global: {
      fetch: safeFetch,
    },
  });
}
