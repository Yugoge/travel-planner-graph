# Context Document: XHS/RedNote Login Fix

**Created**: 2026-04-14
**Purpose**: Complete context for the next agent to permanently fix the rednote-mcp login issue

---

## 1. Problem Summary

`rednote-mcp` (Playwright-based Xiaohongshu scraper MCP tool) cannot authenticate on the Hetzner server. Two layered failures:

1. **IP Ban (error 300012)**: Hetzner datacenter IP `188.245.32.161` is blocklisted by XHS anti-fraud system ("当前IP存在风险"). All direct requests to `www.xiaohongshu.com` and `edith.xiaohongshu.com` are rejected.
2. **Cloudflare Worker proxy incomplete**: A reverse proxy Worker at `xhs.life-ai.app` was deployed to bypass the IP ban. HTML pages load, but the `/api-edith` routing is **BROKEN** -- the Worker sends `/api-edith/*` to `www.xiaohongshu.com/api-edith/*` instead of `edith.xiaohongshu.com/*`. Login QR code generation fails with 404.

---

## 2. Architecture

```
┌─────────────────────┐     ┌───────────────────────┐     ┌──────────────────────┐
│ Hetzner Server      │     │ Cloudflare Worker      │     │ XHS Origin Servers   │
│ 188.245.32.161      │     │ xhs.life-ai.app        │     │                      │
│                     │     │                        │     │ www.xiaohongshu.com  │
│ rednote-mcp         │────►│ Reverse proxy          │────►│ edith.xiaohongshu.com│
│ (Playwright browser)│     │ URL rewrite            │     │ (API server)         │
│                     │     │ Cookie domain rewrite  │     │                      │
└─────────────────────┘     └───────────────────────┘     └──────────────────────┘
```

**Playwright route intercepts** (in both authManager.js and rednoteTools.js):
- `**://edith.xiaohongshu.com/**` → `https://xhs.life-ai.app/api-edith`
- `**://xhslink.com/**` → `https://xhs.life-ai.app`
- `**://www.xiaohongshu.com/**` → `https://xhs.life-ai.app`
- `**/website-login/error**` → abort

**Worker** rewrites response body:
- `www.xiaohongshu.com` → `xhs.life-ai.app`
- `edith.xiaohongshu.com` → `xhs.life-ai.app/api-edith`
- Cookie domains: `.xiaohongshu.com` → `xhs.life-ai.app`

---

## 3. File Inventory

### Core rednote-mcp files (globally installed, edit `.js` only)
| File | Lines | Description |
|------|-------|-------------|
| `/usr/lib/node_modules/rednote-mcp/dist/auth/authManager.js` | 207 | Login flow: launches browser, navigates to explore, waits for QR code, saves cookies. Already patched with route intercepts and proxy URLs. |
| `/usr/lib/node_modules/rednote-mcp/dist/auth/cookieManager.js` | 47 | Simple file-based cookie persistence (load/save/clear). No issues. |
| `/usr/lib/node_modules/rednote-mcp/dist/tools/rednoteTools.js` | 291 | Search/content/comments tools. Already patched with route intercepts and proxy URLs. |
| `/usr/lib/node_modules/rednote-mcp/dist/tools/noteDetail.js` | 66 | DOM extraction logic for note content. No issues. |
| `/usr/lib/node_modules/rednote-mcp/dist/cli.js` | 252 | MCP server + CLI commands (init, search, etc). Uses AuthManager and RedNoteTools. |
| `/usr/lib/node_modules/rednote-mcp/package.json` | 65 | `rednote-mcp@0.2.3`, playwright@1.42.1 |

### Cloudflare Worker
| File | Lines | Description |
|------|-------|-------------|
| `/root/travel-planner/infra/cloudflare-xhs-proxy/src/worker.js` | 175 | Reverse proxy Worker. **BUG**: `buildUpstreamURL()` sends ALL paths to `www.xiaohongshu.com`, including `/api-edith/*` which should go to `edith.xiaohongshu.com`. |
| `/root/travel-planner/infra/cloudflare-xhs-proxy/wrangler.toml` | 22 | Route: `xhs.life-ai.app/*` on zone `life-ai.app` |

### Cookie files
| File | Description |
|------|-------------|
| `/root/.mcp/rednote/cookies.json` | 11 cookies, all domain `.xhs.life-ai.app` (proxy domain). These are unauthenticated session cookies -- no `web_session` with valid auth. |
| `/root/.mcp/rednote/cookies.json.bak` | 11 cookies from original login (domain `.xiaohongshu.com`). Includes `web_session`. Server has likely revoked these. |

### Spec and docs
| File | Description |
|------|-------------|
| `/root/travel-planner/docs/dev/specs/spec-20260412-141227.md` | Full spec document with problem analysis, what was tried, and recommended fixes. |

---

## 4. Critical Bug: Worker `/api-edith` Routing

**The single most important bug to fix.**

In `worker.js`, `buildUpstreamURL()` is:
```javascript
function buildUpstreamURL(url) {
  return new URL(url.pathname + url.search, UPSTREAM_ORIGIN);
  // UPSTREAM_ORIGIN = 'https://www.xiaohongshu.com'
}
```

When Playwright intercepts `edith.xiaohongshu.com/api/sns/web/v1/login/qrcode/create` and rewrites it to `xhs.life-ai.app/api-edith/api/sns/web/v1/login/qrcode/create`, the Worker forwards it to:
```
https://www.xiaohongshu.com/api-edith/api/sns/web/v1/login/qrcode/create
```
This returns 404 because `www.xiaohongshu.com` has no `/api-edith` path.

**Fix required**:
```javascript
function buildUpstreamURL(url) {
  if (url.pathname.startsWith('/api-edith/') || url.pathname === '/api-edith') {
    const edithPath = url.pathname.replace('/api-edith', '') || '/';
    return new URL(edithPath + url.search, 'https://edith.xiaohongshu.com');
  }
  return new URL(url.pathname + url.search, UPSTREAM_ORIGIN);
}
```

Also need to update `buildUpstreamHeaders()` to set correct `Host` for edith requests:
```javascript
function buildUpstreamHeaders(request, targetHost) {
  // ... existing logic ...
  headers.set('Host', targetHost);  // 'edith.xiaohongshu.com' or 'www.xiaohongshu.com'
  headers.set('Origin', `https://${targetHost}`);
  headers.set('Referer', `https://${targetHost}/`);
  // ...
}
```

**Verified**: `curl https://xhs.life-ai.app/api-edith/api/sns/web/v1/login/qrcode/create` currently returns HTTP 404.

---

## 5. What Was Tried and Failed (Apr 12-14)

### Attempt 1: Direct rednote-mcp login
- `xvfb-run --auto-servernum npx rednote-mcp init 60`
- Result: Error 300012 ("IP存在风险") before page loads
- Reason: Server IP `188.245.32.161` is a known Hetzner datacenter IP

### Attempt 2: Cloudflare Worker reverse proxy
- Deployed Worker at `xhs.life-ai.app`
- Patched rednote-mcp to use proxy URLs
- Result: HTML pages load through proxy, but login QR code fails
- Reason: `/api-edith` routing bug (see Section 4)

### Attempt 3: Playwright route interception (added to authManager.js)
- Added `page.route()` intercepts for `edith.xiaohongshu.com` → `xhs.life-ai.app/api-edith`
- Result: Requests correctly redirected to Worker, but Worker returns 404
- Reason: Same `/api-edith` routing bug

### Attempt 4: Cookie restore from backup
- Copied `.bak` cookies, updated domains to `xhs.life-ai.app`
- Result: "Not logged in" -- server had revoked the session

### Attempt 5: Playwright MCP browser with manual route interception
- Used separate Playwright MCP (not rednote-mcp) to navigate XHS directly
- Result: CORS errors on `send_code` API -- missing `x-s`, `x-t` signing headers
- Reason: XHS requires proprietary request signing that only their JS generates

---

## 6. Current State of Each Component

### Cloudflare Worker (xhs.life-ai.app)
- **Status**: Deployed and running
- **Health**: `GET /__health` → 200 OK
- **HTML proxy**: Working (pages load, CSS/JS rewrites work)
- **Cookie rewrite**: Working (domain `.xiaohongshu.com` → `xhs.life-ai.app`)
- **`/api-edith` routing**: BROKEN (404 -- sends to wrong origin)
- **ALLOWED_IPS**: Not set (open to all)
- **Worker egress IP**: `162.158.111.197` (Cloudflare Frankfurt, visible in `xhs-real-ip` response header)
- **Deploy command**: `cd /root/travel-planner/infra/cloudflare-xhs-proxy && wrangler deploy`

### rednote-mcp
- **Status**: Globally installed at `/usr/lib/node_modules/rednote-mcp/`
- **Version**: 0.2.3
- **Route intercepts**: Added for edith, xhslink, www.xiaohongshu.com, and website-login/error
- **Cookie path**: `~/.mcp/rednote/cookies.json`
- **Run command**: `xvfb-run --auto-servernum npx rednote-mcp init 60`
- **Env vars**: `REDNOTE_HEADLESS=1` for headless mode (default is headed)

### Cookies
- **Current** (`cookies.json`): 11 unauthenticated cookies on `.xhs.life-ai.app`
- **Backup** (`cookies.json.bak`): 11 cookies on `.xiaohongshu.com` (expired/revoked)
- **Key cookie**: `web_session` -- this is the auth token. Currently not present in active cookies with valid auth.

---

## 7. Anti-Fraud Detection Vectors

Even after fixing the `/api-edith` routing, login may still fail due to XHS anti-fraud. Known detection vectors:

| Vector | Status | Risk Level |
|--------|--------|------------|
| **Server IP** (188.245.32.161) | Mitigated by Worker proxy | Low (Worker uses Cloudflare IPs) |
| **Cloudflare Worker egress IP** | Unknown -- may also be flagged | Medium |
| **TLS fingerprint** | Worker uses Cloudflare's TLS stack (looks like CDN, not browser) | Medium |
| **`x-forwarded-for` header** | Worker strips it (LEAK_HEADERS list) | Low |
| **`xhs-real-ip` detection** | XHS origin sees Worker IP in `xhs-real-ip: 162.158.111.197` | Medium |
| **Browser fingerprint** (Canvas, WebGL) | Playwright has detectable headless markers | High |
| **`navigator.platform`** | Reports "Linux x86_64" (datacenter) | Medium |
| **Font enumeration** | Server has minimal fonts installed | Medium |
| **`x-s` / `x-t` signing headers** | XHS proprietary request signing -- only their JS generates these | Critical for API calls |
| **Device ID / session binding** | XHS may bind sessions to device fingerprints | High |

---

## 8. Recommended Fix Sequence

### Phase 1: Fix the Worker `/api-edith` routing (MUST DO FIRST)
1. Edit `/root/travel-planner/infra/cloudflare-xhs-proxy/src/worker.js`
2. Update `buildUpstreamURL()` to route `/api-edith/*` to `edith.xiaohongshu.com`
3. Update `buildUpstreamHeaders()` to set correct `Host` header for edith
4. Deploy: `cd /root/travel-planner/infra/cloudflare-xhs-proxy && wrangler deploy`
5. Verify: `curl -D- "https://xhs.life-ai.app/api-edith/api/sns/web/v1/login/qrcode/create"` should NOT return 404

### Phase 2: Test login flow
1. Clear cookies: `rm /root/.mcp/rednote/cookies.json`
2. Run: `DISPLAY=:99 xvfb-run --auto-servernum node /usr/lib/node_modules/rednote-mcp/dist/cli.js init 120`
3. Check if QR code loads
4. If QR code loads, scan with phone to complete login

### Phase 3: If login still fails (anti-fraud detection)
**Option A: Residential proxy** (most reliable)
- Use a residential SOCKS5/HTTP proxy service (e.g., Bright Data, SmartProxy)
- Configure at the Worker level or in Playwright browser context
- This gives a real residential IP that XHS won't flag

**Option B: Cookie import from local machine**
- Login to XHS from a real browser on a local machine (not the server)
- Export cookies (browser extension or DevTools)
- Convert to Playwright format and save to `~/.mcp/rednote/cookies.json`
- Update cookie domains from `.xiaohongshu.com` to `.xhs.life-ai.app`
- This bypasses login entirely but cookies expire eventually

**Option C: puppeteer-extra-plugin-stealth**
- Replace Playwright with Puppeteer + stealth plugin
- Masks headless browser fingerprints (WebGL, Canvas, navigator, etc.)
- Major refactor of rednote-mcp required

---

## 9. Important Warnings

1. **DO NOT modify TypeScript source** -- only edit `.js` files under `/usr/lib/node_modules/rednote-mcp/dist/`. Changes survive as long as the package is not reinstalled via npm.

2. **rednote-mcp requires Xvfb** -- run as `xvfb-run --auto-servernum` or the browser crashes.

3. **Cookie domain is critical** -- cookies must be on `.xhs.life-ai.app` when using the proxy. The Worker's `rewriteCookie()` handles `Set-Cookie` headers. If loading cookies from backup, manually change domains.

4. **`edith.xiaohongshu.com` is the critical API server** -- it handles:
   - Login: `/api/sns/web/v1/login/qrcode/create`, `/api/sns/web/v1/login/qrcode/check`
   - User info: `/api/sns/web/v2/user/me`
   - Search: `/api/sns/web/v1/search/notes`
   - Note detail: `/api/sns/web/v1/note/detail`

5. **XHS `x-s` and `x-t` headers** -- these are proprietary anti-scraping signatures generated by XHS's client-side JavaScript. They CANNOT be faked externally. The Playwright approach works because the real XHS JS runs in the browser and generates these headers naturally. If the Worker strips or corrupts them, API calls will fail.

6. **Worker has no authentication** -- `ALLOWED_IPS` is commented out in `wrangler.toml`. After confirming functionality, set it to the server IP (`188.245.32.161`) to prevent abuse.

7. **Cloudflare credentials** (for Worker deployment):
   - Account: `yugetang@outlook.com`
   - Scoped API token: `cfut_m6rI2eOfIy6ZAFHf8Mk3SuE4BKo1OxROtVdBU0DXc2fccdbb`

---

## 10. Quick Test Commands

```bash
# Health check
curl -s https://xhs.life-ai.app/__health

# Test /api-edith routing (should NOT be 404 after fix)
curl -s -o /dev/null -w "%{http_code}" "https://xhs.life-ai.app/api-edith/api/sns/web/v1/login/qrcode/create"

# Deploy Worker after editing
cd /root/travel-planner/infra/cloudflare-xhs-proxy && wrangler deploy

# Run rednote-mcp login (headless)
REDNOTE_HEADLESS=1 xvfb-run --auto-servernum node /usr/lib/node_modules/rednote-mcp/dist/cli.js init 120

# Run rednote-mcp login (with virtual display for debugging)
xvfb-run --auto-servernum node /usr/lib/node_modules/rednote-mcp/dist/cli.js init 120

# Check current cookies
python3 -c "import json; [print(f'{c[\"name\"]}: {c[\"domain\"]}') for c in json.load(open('/root/.mcp/rednote/cookies.json'))]"

# Clear cookies for fresh login
rm /root/.mcp/rednote/cookies.json
```
