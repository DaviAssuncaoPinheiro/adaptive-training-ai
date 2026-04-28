import { createClient } from '@/lib/supabase/server';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

async function proxy(request, ctx) {
  const { path } = await ctx.params;

  const supabase = await createClient();
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    return Response.json({ detail: 'unauthorized' }, { status: 401 });
  }

  const url = new URL(`${FASTAPI_URL}/api/${path.join('/')}`);
  url.search = new URL(request.url).search;

  const init = {
    method: request.method,
    headers: {
      Authorization: `Bearer ${session.access_token}`,
    },
    cache: 'no-store',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    const contentType = request.headers.get('content-type');
    if (contentType) init.headers['Content-Type'] = contentType;
    init.body = await request.text();
  }

  try {
    const upstream = await fetch(url, init);
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: {
        'Content-Type': upstream.headers.get('content-type') || 'application/json',
      },
    });
  } catch (error) {
    console.error(`BFF Proxy Error: failed to fetch ${url}`, error);
    return Response.json({ detail: 'Server disconnected or unreachable' }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
