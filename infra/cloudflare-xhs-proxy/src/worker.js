/**
 * Cloudflare Worker: Xiaohongshu (小红书) Reverse Proxy
 *
 * Proxies requests from rednote-mcp's Playwright browser to xiaohongshu.com
 * through Cloudflare's network, bypassing IP-based blocks (error 300012).
 *
 * Approach: Full reverse proxy. The browser navigates to this Worker's domain
 * instead of xiaohongshu.com. All requests are forwarded to the real origin,
 * and responses have URLs rewritten so the browser stays on the proxy domain.
 */

const UPSTREAM = 'www.xiaohongshu.com';
const UPSTREAM_ORIGIN = 'https://www.xiaohongshu.com';

const HOP_BY_HOP = new Set([
  'connection', 'keep-alive', 'transfer-encoding', 'te',
  'trailer', 'upgrade', 'proxy-authorization', 'proxy-authenticate',
]);

const LEAK_HEADERS = [
  'cf-connecting-ip', 'cf-ipcountry', 'cf-ray',
  'cf-visitor', 'x-forwarded-for', 'x-forwarded-proto', 'x-real-ip',
];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const proxyHost = url.host;

    if (url.pathname === '/__health') {
      return new Response('ok', { status: 200 });
    }

    if (!isAllowedIP(request, env)) {
      return new Response('Forbidden', { status: 403 });
    }

    const upstreamURL = buildUpstreamURL(url);
    const upstreamHeaders = buildUpstreamHeaders(request);
    const upstreamRequest = buildUpstreamRequest(request, upstreamURL, upstreamHeaders);

    let response;
    try {
      response = await fetch(upstreamRequest);
    } catch (err) {
      return new Response(`Upstream error: ${err.message}`, { status: 502 });
    }

    if (isRedirect(response)) {
      return handleRedirect(response, proxyHost);
    }

    return buildProxyResponse(response, proxyHost);
  },
};

function isAllowedIP(request, env) {
  if (!env.ALLOWED_IPS) return true;
  const clientIP = request.headers.get('cf-connecting-ip');
  const allowed = env.ALLOWED_IPS.split(',').map(s => s.trim());
  return allowed.includes(clientIP);
}

function buildUpstreamURL(url) {
  return new URL(url.pathname + url.search, UPSTREAM_ORIGIN);
}

function buildUpstreamHeaders(request) {
  const headers = new Headers();
  for (const [key, value] of request.headers.entries()) {
    if (HOP_BY_HOP.has(key.toLowerCase())) continue;
    headers.set(key, value);
  }
  headers.set('Host', UPSTREAM);
  headers.set('Origin', UPSTREAM_ORIGIN);
  headers.set('Referer', UPSTREAM_ORIGIN + '/');
  for (const h of LEAK_HEADERS) {
    headers.delete(h);
  }
  return headers;
}

function buildUpstreamRequest(request, url, headers) {
  return new Request(url.toString(), {
    method: request.method,
    headers,
    body: (request.method !== 'GET' && request.method !== 'HEAD')
      ? request.body
      : undefined,
    redirect: 'manual',
  });
}

function isRedirect(response) {
  return [301, 302, 303, 307, 308].includes(response.status);
}

function handleRedirect(response, proxyHost) {
  const location = response.headers.get('location');
  if (!location) return response;
  const newLocation = rewriteUrl(location, proxyHost);
  const headers = new Headers(response.headers);
  headers.set('location', newLocation);
  return new Response(null, { status: response.status, headers });
}

async function buildProxyResponse(response, proxyHost) {
  const responseHeaders = buildResponseHeaders(response, proxyHost);
  const contentType = response.headers.get('content-type') || '';
  const isRewritable = isRewritableContent(contentType);

  if (isRewritable) {
    const body = await response.text();
    const rewritten = rewriteBody(body, proxyHost);
    responseHeaders.delete('content-encoding');
    responseHeaders.delete('content-length');
    return new Response(rewritten, { status: response.status, headers: responseHeaders });
  }

  return new Response(response.body, { status: response.status, headers: responseHeaders });
}

function buildResponseHeaders(response, proxyHost) {
  const headers = new Headers();
  for (const [key, value] of response.headers.entries()) {
    if (HOP_BY_HOP.has(key.toLowerCase())) continue;
    if (key.toLowerCase() === 'set-cookie') {
      headers.append(key, rewriteCookie(value, proxyHost));
      continue;
    }
    headers.set(key, value);
  }
  headers.delete('content-security-policy');
  headers.delete('content-security-policy-report-only');
  headers.set('access-control-allow-origin', '*');
  headers.set('access-control-allow-credentials', 'true');
  return headers;
}

function rewriteCookie(cookie, proxyHost) {
  return cookie.replace(/domain=\.?xiaohongshu\.com/gi, `domain=${proxyHost}`);
}

function isRewritableContent(contentType) {
  return contentType.includes('text/html')
    || contentType.includes('application/javascript')
    || contentType.includes('text/javascript')
    || contentType.includes('application/json')
    || contentType.includes('text/css');
}

function rewriteBody(body, proxyHost) {
  let result = body;
  result = result.replaceAll('https://www.xiaohongshu.com', `https://${proxyHost}`);
  result = result.replaceAll('http://www.xiaohongshu.com', `https://${proxyHost}`);
  result = result.replaceAll('//www.xiaohongshu.com', `//${proxyHost}`);
  result = result.replaceAll('www.xiaohongshu.com', proxyHost);
  result = result.replaceAll('https://edith.xiaohongshu.com', `https://${proxyHost}/api-edith`);
  result = result.replaceAll('edith.xiaohongshu.com', `${proxyHost}/api-edith`);
  return result;
}

function rewriteUrl(url, proxyHost) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname === UPSTREAM || parsed.hostname.endsWith('.xiaohongshu.com')) {
      parsed.hostname = proxyHost;
      return parsed.toString();
    }
  } catch {
    // Relative URL or malformed
  }
  return url;
}
