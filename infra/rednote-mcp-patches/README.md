# rednote-mcp Patches

Patches for `rednote-mcp@0.2.3` to route all XHS (Xiaohongshu) traffic through the `xhs.life-ai.app` reverse proxy. This is required because the server cannot reach `xiaohongshu.com` directly.

## What the patches do

### authManager.patch
- Routes `edith.xiaohongshu.com` API calls through `xhs.life-ai.app/api-edith`
- Routes `www.xiaohongshu.com` and `xhslink.com` through `xhs.life-ai.app`
- Blocks `/website-login/error` redirects
- Duplicates cookies to `.xiaohongshu.com` domain so API calls are authenticated
- Supports `REDNOTE_HEADLESS=1` env var for headless browser mode
- Changes login navigation to use proxy URL

### rednoteTools.patch
- Same proxy routing and cookie duplication for the tool browser context
- Hides cookie banner overlays via injected CSS
- Uses `page.evaluate()` for `.close-circle` clicks (more reliable than direct click)
- Updates URL regex to also match `xhs.life-ai.app` links
- Adds short wait after search navigation for stability

## How to apply

```bash
# 1. Install the base package
npm install -g rednote-mcp@0.2.3

# 2. Apply patches
./apply.sh
```

## Backup files

The `*.patched` files are complete copies of the modified files. If `patch` fails (e.g., version mismatch), you can copy them directly:

```bash
cp authManager.js.patched /usr/lib/node_modules/rednote-mcp/dist/auth/authManager.js
cp rednoteTools.js.patched /usr/lib/node_modules/rednote-mcp/dist/tools/rednoteTools.js
```
