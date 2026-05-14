/* budget.js — POST /api/budget/recompute + persistent panel render
 * Spec: §5.10 + §5.13 D #3 + Q3g cost:unknown semantics
 *
 * Two-phase model:
 *   Phase 1: local ~100ms — request /api/budget/recompute on every commit.
 *   Phase 2: when /api/route fills in transportation cost later, a follow-up
 *            recompute reflects the new total. The same endpoint covers both.
 */

import { wrappedFetch } from "./offline.js";

const _state = {
  trip_total: null,
  day_total: null,
  breakdown: null,
  currency: "",
  computing: false,
  unknown_count: 0,
};

let _activeReqSeq = 0;

export async function recomputeBudget(state, dayN) {
  if (!state.trip_id) return;
  _activeReqSeq += 1;
  const mySeq = _activeReqSeq;
  _state.computing = true;
  _renderTotalsComputing();
  try {
    const resp = await wrappedFetch("/api/budget/recompute", {
      method: "POST",
      body: JSON.stringify({ trip_id: state.trip_id, day: dayN }),
    });
    if (mySeq < _activeReqSeq) return; // stale
    _ingest(resp, dayN);
  } catch (_err) {
    if (mySeq < _activeReqSeq) return;
    _markUnknown();
  } finally {
    _state.computing = false;
    renderBudget(state);
  }
}

function _ingest(resp, dayN) {
  if (!resp) {
    _markUnknown();
    return;
  }
  _state.trip_total = resp.trip_total;
  _state.currency = resp.currency_local || "";
  const dayRec = (resp.days || []).find((d) => d.day === dayN);
  if (dayRec) {
    _state.day_total = dayRec.day_total;
    _state.breakdown = dayRec.breakdown || null;
    _state.unknown_count = _countUnknowns(dayRec.breakdown);
  } else {
    _state.day_total = null;
    _state.breakdown = null;
    _state.unknown_count = 0;
  }
}

function _countUnknowns(breakdown) {
  if (!breakdown) return 0;
  let total = 0;
  for (const k of Object.keys(breakdown)) {
    const sub = breakdown[k];
    if (sub && typeof sub.unknown_count === "number") {
      total += sub.unknown_count;
    }
  }
  return total;
}

function _markUnknown() {
  _state.trip_total = null;
  _state.day_total = null;
  _state.breakdown = null;
  _state.unknown_count = 0;
}

function _renderTotalsComputing() {
  const tt = document.getElementById("budget-trip-total");
  const dt = document.getElementById("budget-day-total");
  if (tt) {
    tt.textContent = "computing...";
    tt.classList.add("computing");
  }
  if (dt) {
    dt.textContent = "computing...";
    dt.classList.add("computing");
  }
}

export function renderBudget(_state2) {
  _renderTotal("budget-trip-total", _state.trip_total);
  _renderTotal("budget-day-total", _state.day_total);
  _renderBreakdown();
}

function _renderTotal(elId, amount) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.classList.remove("computing", "unknown");
  if (amount === null || amount === undefined) {
    el.textContent = "unknown";
    el.classList.add("unknown");
    return;
  }
  const cur = _state.currency || "";
  el.textContent = `${_formatMoney(amount)} ${cur}`.trim();
}

function _formatMoney(n) {
  if (typeof n !== "number") return String(n);
  return n.toFixed(2);
}

function _renderBreakdown() {
  const container = document.getElementById("budget-breakdown");
  if (!container) return;
  container.innerHTML = "";
  if (!_state.breakdown) {
    if (_state.unknown_count > 0 || _state.day_total === null) {
      const ln = document.createElement("div");
      ln.className = "budget-line unknown";
      ln.textContent = "cost: unknown";
      container.appendChild(ln);
    }
    return;
  }
  for (const key of Object.keys(_state.breakdown)) {
    container.appendChild(_buildBreakdownRow(key, _state.breakdown[key]));
  }
}

function _buildBreakdownRow(category, rec) {
  const row = document.createElement("div");
  row.className = "budget-line";
  const label = document.createElement("span");
  label.className = "budget-label";
  label.textContent = category;
  const value = document.createElement("span");
  value.className = "budget-value";
  if (!rec || rec.amount === null || rec.amount === undefined) {
    value.textContent = "cost: unknown";
    value.classList.add("unknown");
    row.classList.add("unknown");
  } else {
    value.textContent = `${_formatMoney(rec.amount)} ${_state.currency || ""}`.trim();
    if (rec.unknown_count > 0) {
      value.textContent += ` (+${rec.unknown_count} unknown)`;
    }
  }
  row.appendChild(label);
  row.appendChild(value);
  return row;
}
