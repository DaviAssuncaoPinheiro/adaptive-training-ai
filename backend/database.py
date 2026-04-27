"""
Cliente Supabase singleton.
Utiliza a Service Role Key para operacoes do backend (bypassa RLS quando necessario).
O frontend continua usando a anon key via SDK JS com RLS ativo.
"""

from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY


def get_supabase_client() -> Client:
    """Retorna uma instancia do cliente Supabase configurada com a Service Role Key."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "As variaveis SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar definidas no .env"
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
