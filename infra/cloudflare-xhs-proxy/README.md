# Xiaohongshu Cloudflare Worker Proxy

Reverse proxy that forwards requests to xiaohongshu.com through Cloudflare's
network, bypassing IP-based blocks (error 300012 "IP at risk") that affect the
Hetzner server.

## How it works

```
Playwright (rednote-mcp on Hetzner)
  -> https://xhs.life-ai.app/explore
    -> Cloudflare Worker (edge)
      -> https://www.xiaohongshu.com/explore
```

The Worker rewrites URLs in HTML/JS/CSS responses so the browser stays on the
proxy domain. Cookies are forwarded transparently. The origin server sees a
Cloudflare edge IP, not the Hetzner IP.

## Why reverse proxy (not CONNECT proxy)

Cloudflare Workers cannot act as CONNECT proxies (no raw TCP socket support).
Playwright's `proxy` option requires a CONNECT-capable proxy for HTTPS traffic.
The only viable approach is a reverse proxy where we change the target URLs in
rednote-mcp to point at our proxy domain.

## Prerequisites

- Cloudflare account with `life-ai.app` zone (already configured)
- `wrangler` CLI (already installed: v4.81.1)
- Authenticated with Cloudflare: `npx wrangler login`

## Deployment

```bash
cd /root/travel-planner/infra/cloudflare-xhs-proxy

# 1. Login to Cloudflare (one-time)
#    Option A: Interactive (needs browser -- use SSH tunnel)
npx wrangler login
#    Option B: API token (set env var)
export CLOUDFLARE_API_TOKEN="your-token-here"

# 2. Deploy the Worker
npx wrangler deploy

# 3. Add custom domain in Cloudflare Dashboard:
#    Workers & Pages > xhs-proxy > Settings > Triggers > Custom Domains
#    Add: xhs.life-ai.app
#
#    The Worker will also be available at xhs-proxy.<your-subdomain>.workers.dev

# 4. (Optional) Restrict access to your server IP only
npx wrangler secret put ALLOWED_IPS
# Enter your server IP, e.g.: 5.161.xxx.xxx

# 5. Verify
curl -I https://xhs.life-ai.app/__health
# Should return: HTTP/2 200
```

## Modifying rednote-mcp

After deploying the Worker, modify these files to use the proxy domain.

### File 1: /usr/lib/node_modules/rednote-mcp/dist/auth/authManager.js

Line 112 (login page navigation):
```javascript
// BEFORE:
await this.page.goto('https://www.xiaohongshu.com/explore', {
// AFTER:
await this.page.goto('https://xhs.life-ai.app/explore', {
```

### File 2: /usr/lib/node_modules/rednote-mcp/dist/tools/rednoteTools.js

Line 33 (login check):
```javascript
// BEFORE:
await this.page.goto('https://www.xiaohongshu.com');
// AFTER:
await this.page.goto('https://xhs.life-ai.app');
```

Line 79 (URL regex for parsing share links):
```javascript
// BEFORE:
const xiaohongshuRegex = /(https?:\/\/(?:www\.)?xiaohongshu\.com\/[^，\s]+)/i;
// AFTER:
const xiaohongshuRegex = /(https?:\/\/(?:www\.)?(?:xiaohongshu\.com|xhs\.life-ai\.app)\/[^，\s]+)/i;
```

Line 94 (search):
```javascript
// BEFORE:
await this.page.goto(`https://www.xiaohongshu.com/search_result?keyword=...`);
// AFTER:
await this.page.goto(`https://xhs.life-ai.app/search_result?keyword=...`);
```

### Cookie reset

After switching to the proxy, delete existing cookies and re-login:
```bash
rm ~/.mcp/rednote/cookies.json
```

## Edith API handling

Xiaohongshu uses `edith.xiaohongshu.com` for internal API calls (note details,
user info, etc.). The Worker rewrites these URLs to route through
`xhs.life-ai.app/api-edith/*`. No additional configuration needed -- the
rewriting happens in both the JS/HTML responses and in redirect handling.

## Cloudflare Worker Free Tier Limits

| Resource | Free Tier | Estimated usage |
|----------|-----------|-----------------|
| Requests/day | 100,000 | 500-2,000 |
| CPU time/request | 10ms | 2-5ms |
| Script size | 1 MB | ~4 KB |
| Subrequests/request | 50 | 1 |

Free tier is more than sufficient for rednote-mcp usage.

## Troubleshooting

**Still getting 300012**: XHS may fingerprint the browser beyond IP. Try
setting a realistic User-Agent, viewport size, or switching to
`headless: 'new'` mode in Playwright.

**Cookies not working**: Delete `~/.mcp/rednote/cookies.json` and re-login
through the proxy. Check `npx wrangler tail` for Set-Cookie rewriting errors.

**502 from Worker**: Check live logs with `npx wrangler tail`.

**CORS errors**: The Worker sets `access-control-allow-origin: *` and strips
CSP headers. Should not occur in normal operation.

## Security

- Set `ALLOWED_IPS` to restrict access to your server IP.
- No secrets or credentials are stored in the Worker code.
- The Worker does not log or store request/response data.
