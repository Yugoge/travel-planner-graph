/* save.js — debounced /api/save dispatcher
 * Spec: §5.13 D #2 + §5.13 D #5 (409-soft)
 *
 * Coalesces rapid mutations into a single POST per (trip_id, day) per 300ms.
 * Sets state.ui.save_state and state.ui.conflict_409_soft on response.
 */

import { wrappedFetch } from "./offline.js";

const DEBOUNCE_MS = 300;

/* Per-day mutation queue + debounce timer */
const _queues = new Map(); // key: dayN -> {mutations:[], timer:int}

export function queueSave(state, dayN, mutation) {
  if (state.ui.offline) return; // controls are disabled while offline
  let q = _queues.get(dayN);
  if (!q) {
    q = { mutations: [], timer: null };
    _queues.set(dayN, q);
  }
  q.mutations.push(mutation);
  state.ui.save_state = "saving";
  _renderSaveStatus(state);
  if (q.timer) clearTimeout(q.timer);
  q.timer = setTimeout(() => _flush(state, dayN), DEBOUNCE_MS);
}

async function _flush(state, dayN) {
  const q = _queues.get(dayN);
  if (!q || q.mutations.length === 0) return;
  const mutations = q.mutations;
  q.mutations = [];
  q.timer = null;
  const body = {
    trip_id: state.trip_id,
    day: dayN,
    editor_session: state.ui.editor_session,
    mutations,
  };
  try {
    const resp = await wrappedFetch("/api/save", {
      method: "POST",
      body: JSON.stringify(body),
    });
    _onSaveSuccess(state, resp);
  } catch (err) {
    _onSaveError(state, err);
  }
}

function _onSaveSuccess(state, resp) {
  state.ui.last_save_ts = Date.now();
  state.ui.save_state = "saved";
  if (resp && resp.conflict === "409-soft") {
    state.ui.conflict_409_soft = true;
  }
  _renderSaveStatus(state);
  _renderConflictBanner(state);
}

function _onSaveError(state, _err) {
  state.ui.save_state = "error";
  _renderSaveStatus(state);
}

function _renderSaveStatus(state) {
  const el = document.getElementById("save-status");
  if (!el) return;
  el.dataset.state = state.ui.save_state;
  if (state.ui.save_state === "saving") {
    el.textContent = "saving...";
  } else if (state.ui.save_state === "error") {
    el.textContent = "save error";
  } else {
    el.textContent = "saved";
  }
}

function _renderConflictBanner(state) {
  const el = document.getElementById("banner-conflict");
  if (el) el.hidden = !state.ui.conflict_409_soft;
}

/* Force-flush all pending queues (test affordance + page-unload) */
export function flushNow(state) {
  for (const dayN of _queues.keys()) {
    _flush(state, dayN);
  }
}

window.addEventListener("beforeunload", () => {
  for (const [, q] of _queues) {
    if (q.timer) clearTimeout(q.timer);
  }
});
