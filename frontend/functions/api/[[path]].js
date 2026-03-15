const ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];

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

function buildUpstreamUrl(requestUrl, backendOrigin) {
  const incomingUrl = new URL(requestUrl);
  const upstreamPath = incomingUrl.pathname.replace(/^\/api/, '') || '/';
  return `${backendOrigin}${upstreamPath}${incomingUrl.search}`;
}

export async function onRequest(context) {
  const { request, env } = context;
  const incomingUrl = new URL(request.url);

  if (!(incomingUrl.pathname === '/api' || incomingUrl.pathname.startsWith('/api/'))) {
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

  const upstreamUrl = buildUpstreamUrl(request.url, backendOrigin);
  const headers = new Headers(request.headers);
  headers.set('X-Forwarded-Proto', incomingUrl.protocol.replace(':', ''));
  headers.set('X-Forwarded-Host', incomingUrl.host);

  const init = {
    method: request.method,
    headers,
    redirect: 'manual',
  };

  if (!['GET', 'HEAD'].includes(request.method)) {
    init.body = request.body;
  }

  try {
    const upstreamResp = await fetch(upstreamUrl, init);
    return withCors(upstreamResp, request);
  } catch (err) {
    return withCors(
      new Response(`Bad Gateway: ${err?.message || 'upstream fetch failed'}`, { status: 502 }),
      request
    );
  }
}