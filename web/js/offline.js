/* offline.js — fetch wrapper, offline banner, edit-disable
 * Spec: §5.13 D #9
 *
 * Wraps fetch(); flips to offline when a fetch fails AND a follow-up retry
 * also fails within 5s. Recovers on first successful fetch. Exposes
 * setOnlineHandler() so state.js learns about transitions.
 */

const OFFLINE_THRESHOLD_MS = 5000;
const RECONNECT_PROBE_MS = 5000;
let _firstFailureAt = null;
let _offlineTimer = null;
let _reconnectTimer = null;
let _isOffline = false;
let _onlineHandler = () => {};

export function setOnlineHandler(fn) {
  _onlineHandler = fn || (() => {});
}

function _flipOffline(next) {
  if (_isOffline === next) return;
  _isOffline = next;
  _onlineHandler(_isOffline);
  if (next) {
    _scheduleReconnectProbe();
  } else if (_reconnectTimer) {
    clearInterval(_reconnectTimer);
    _reconnectTimer = null;
  }
}

function _scheduleReconnectProbe() {
  if (_reconnectTimer) clearInterval(_reconnectTimer);
  _reconnectTimer = setInterval(async () => {
    try {
      const resp = await fetch("/api/trip/__probe__", { method: "GET" });
      // ANY response (even 404) means the server is reachable.
      if (resp.status > 0) {
        _firstFailureAt = null;
        _flipOffline(false);
      }
    } catch (_e) {
      /* still offline; keep probing */
    }
  }, RECONNECT_PROBE_MS);
}

async function _doFetch(url, opts) {
  const headers = Object.assign(
    { "Content-Type": "application/json" },
    opts && opts.headers ? opts.headers : {},
  );
  const resp = await fetch(url, Object.assign({}, opts, { headers }));
  if (!resp.ok && resp.status >= 500) {
    throw new Error(`server ${resp.status}`);
  }
  // 4xx returned to caller; parse JSON.
  let payload = null;
  const ct = resp.headers.get("Content-Type") || "";
  if (ct.includes("application/json")) {
    payload = await resp.json();
  } else {
    payload = await resp.text();
  }
  if (!resp.ok) {
    const err = new Error(
      `HTTP ${resp.status} ${resp.statusText}: ${JSON.stringify(payload).slice(0, 200)}`,
    );
    err.status = resp.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}

export async function wrappedFetch(url, opts) {
  try {
    const result = await _doFetch(url, opts);
    _firstFailureAt = null;
    _flipOffline(false);
    return result;
  } catch (err) {
    _trackFailure();
    throw err;
  }
}

function _trackFailure() {
  if (_firstFailureAt === null) {
    _firstFailureAt = Date.now();
    return;
  }
  if (Date.now() - _firstFailureAt >= OFFLINE_THRESHOLD_MS) {
    _flipOffline(true);
  }
}

export function isOffline() {
  return _isOffline;
}
