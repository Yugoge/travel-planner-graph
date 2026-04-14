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
const EDITH_UPSTREAM = 'edith.xiaohongshu.com';
const EDITH_UPSTREAM_ORIGIN = 'https://edith.xiaohongshu.com';

const INJECT_SCRIPT = `<script>
(function() {
  var edithOrigin = 'https://edith.xiaohongshu.com';
  var proxyEdith = '/api-edith';

  // Override fetch
  var origFetch = window.fetch;
  window.fetch = function(input, init) {
    if (typeof input === 'string' && input.indexOf(edithOrigin) === 0) {
      input = proxyEdith + input.slice(edithOrigin.length);
    } else if (input instanceof Request && input.url.indexOf(edithOrigin) === 0) {
      input = new Request(proxyEdith + input.url.slice(edithOrigin.length), input);
    }
    return origFetch.call(this, input, init);
  };

  // Override XMLHttpRequest.open
  var origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url) {
    if (typeof url === 'string' && url.indexOf(edithOrigin) === 0) {
      arguments[1] = proxyEdith + url.slice(edithOrigin.length);
    }
    return origOpen.apply(this, arguments);
  };
})();
</script>`;

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

    const requestOrigin = request.headers.get('origin') || '*';

    if (request.method === 'OPTIONS') {
      return buildPreflightResponse(request, requestOrigin);
    }

    return forwardToUpstream(request, url, proxyHost, requestOrigin);
  },
};

function buildPreflightResponse(request, requestOrigin) {
  return new Response(null, {
    status: 204,
    headers: {
      'access-control-allow-origin': requestOrigin,
      'access-control-allow-credentials': 'true',
      'access-control-allow-methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
      'access-control-allow-headers': request.headers.get('access-control-request-headers') || '*',
      'access-control-max-age': '86400',
    },
  });
}

function forwardToUpstream(request, url, proxyHost, requestOrigin) {
  const isEdith = isEdithRoute(url);
  const targetHost = isEdith ? EDITH_UPSTREAM : UPSTREAM;
  const upstreamURL = buildUpstreamURL(url);
  const upstreamHeaders = buildUpstreamHeaders(request, targetHost, isEdith);
  return proxyToUpstream(request, upstreamURL, upstreamHeaders, proxyHost, requestOrigin);
}

async function proxyToUpstream(request, upstreamURL, upstreamHeaders, proxyHost, requestOrigin) {
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
  return buildProxyResponse(response, proxyHost, requestOrigin);
}

function isAllowedIP(request, env) {
  if (!env.ALLOWED_IPS) return true;
  const clientIP = request.headers.get('cf-connecting-ip');
  const allowed = env.ALLOWED_IPS.split(',').map(s => s.trim());
  return allowed.includes(clientIP);
}

function isEdithRoute(url) {
  return url.pathname.startsWith('/api-edith/') || url.pathname === '/api-edith';
}

function buildUpstreamURL(url) {
  if (isEdithRoute(url)) {
    const edithPath = url.pathname.replace('/api-edith', '') || '/';
    return new URL(edithPath + url.search, EDITH_UPSTREAM_ORIGIN);
  }
  return new URL(url.pathname + url.search, UPSTREAM_ORIGIN);
}

function buildUpstreamHeaders(request, targetHost, isEdith) {
  const headers = new Headers();
  for (const [key, value] of request.headers.entries()) {
    if (HOP_BY_HOP.has(key.toLowerCase())) continue;
    headers.set(key, value);
  }
  headers.set('Host', targetHost);
  if (!isEdith) {
    // Only override Origin/Referer for www pages, not for edith API calls
    headers.set('Origin', `https://${targetHost}`);
    headers.set('Referer', `https://${targetHost}/`);
  }
  // For edith: keep original Origin/Referer from browser (matches x-s-common)
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

async function buildProxyResponse(response, proxyHost, requestOrigin) {
  const responseHeaders = buildResponseHeaders(response, proxyHost, requestOrigin);
  const contentType = response.headers.get('content-type') || '';
  const isRewritable = isRewritableContent(contentType);

  if (isRewritable) {
    const body = await response.text();
    let rewritten = rewriteBody(body, proxyHost);
    if (contentType.includes('text/html')) {
      rewritten = rewritten.replace(/<head([^>]*)>/i, `<head$1>${INJECT_SCRIPT}`);
    }
    responseHeaders.delete('content-encoding');
    responseHeaders.delete('content-length');
    return new Response(rewritten, { status: response.status, headers: responseHeaders });
  }

  return new Response(response.body, { status: response.status, headers: responseHeaders });
}

function buildResponseHeaders(response, proxyHost, requestOrigin) {
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
  headers.set('access-control-allow-origin', requestOrigin);
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
    if (parsed.hostname === 'edith.xiaohongshu.com') {
      return `https://${proxyHost}/api-edith${parsed.pathname}${parsed.search}`;
    }
    if (parsed.hostname === UPSTREAM || parsed.hostname.endsWith('.xiaohongshu.com')) {
      parsed.hostname = proxyHost;
      return parsed.toString();
    }
  } catch {
    // Relative URL or malformed
  }
  return url;
}
