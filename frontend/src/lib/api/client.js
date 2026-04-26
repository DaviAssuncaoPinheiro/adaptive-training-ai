export async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };

  const res = await fetch(`/api/bff${path}`, { ...options, headers });
  const text = await res.text();
  const data = text ? safeParse(text) : null;

  if (!res.ok) {
    const message = (data && data.detail) || res.statusText || 'request failed';
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }
  return data;
}

function safeParse(text) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
