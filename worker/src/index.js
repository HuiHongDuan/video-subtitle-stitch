const ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'];

function corsHeaders(request) {
  const requestedHeaders = request.headers.get('Access-Control-Request-Headers');
  const headers = new Headers();
  headers.set('Access-Control-Allow-Origin', '*');
  headers.set('Access-Control-Allow-Methods', ALLOWED_METHODS.join(','));
  headers.set('Access-Control-Allow-Headers', requestedHeaders || '*');
  headers.set('Access-Control-Max-Age', '86400');
  return headers;
}

function withCors(response, request) {
  const headers = new Headers(response.headers);
  const cors = corsHeaders(request);
  for (const [key, value] of cors.entries()) {
    headers.set(key, value);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function normalizeBackendOrigin(env) {
  const origin = env.BACKEND_ORIGIN;
  if (!origin || !origin.trim()) return null;
  return origin.trim().replace(/\/+$/, '');
}

export default {
  async fetch(request, env) {
    const incomingUrl = new URL(request.url);

    if (!incomingUrl.pathname.startsWith('/api/')) {
      return new Response('Not Found', { status: 404 });
    }

    if (!ALLOWED_METHODS.includes(request.method)) {
      return withCors(new Response('Method Not Allowed', { status: 405 }), request);
    }

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(request) });
    }

    const backendOrigin = normalizeBackendOrigin(env);
    if (!backendOrigin) {
      return withCors(new Response('BACKEND_ORIGIN is not configured', { status: 500 }), request);
    }

    const upstreamPath = incomingUrl.pathname.replace(/^\/api/, '') || '/';
    const upstreamUrl = new URL(`${backendOrigin}${upstreamPath}${incomingUrl.search}`);

    const headers = new Headers(request.headers);
    headers.set('X-Forwarded-Proto', incomingUrl.protocol.replace(':', ''));
    headers.set('X-Forwarded-Host', incomingUrl.host);

    const init = {
      method: request.method,
      headers,
      redirect: 'manual',
    };
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      init.body = request.body;
    }

    try {
      const upstreamResp = await fetch(upstreamUrl.toString(), init);
      return withCors(upstreamResp, request);
    } catch {
      return withCors(new Response('Bad Gateway', { status: 502 }), request);
    }
  },
};
