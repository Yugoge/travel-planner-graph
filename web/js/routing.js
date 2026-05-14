/* routing.js — POST /api/route with monotonic request_seq + stale-drop
 * Spec: §5.9 + §5.13 D #6
 *
 * Each (from_option_id, to_option_id, mode) tuple keeps a monotonic seq.
 * Responses with seq < latest_seen_seq are discarded (avoids stale paint).
 */

import { wrappedFetch } from "./offline.js";
import { renderAll, getActiveDayNumber, state as appState } from "./state.js";
import { recomputeBudget } from "./budget.js";

const NAMED_SLOTS = [
  "breakfast",
  "morning_activity",
  "lunch",
  "afternoon_activity",
  "dinner",
  "evening_activity",
];

let _seqCounter = 0;
const _latestSeen = new Map();

function _pairKey(fromOptId, toOptId, mode) {
  return `${fromOptId}:${toOptId}:${mode}`;
}

function _nextSlotKey(slotId) {
  const idx = NAMED_SLOTS.indexOf(slotId);
  if (idx < 0 || idx === NAMED_SLOTS.length - 1) return null;
  return NAMED_SLOTS[idx + 1];
}

function _getDay(state, dayN) {
  return state.days.find((d) => d.day === dayN || d.day_number === dayN);
}

function _getSlot(day, slotId) {
  if (!day) return null;
  if (slotId === "accommodation") return day.accommodation || null;
  if (day.slots && typeof day.slots === "object" && !Array.isArray(day.slots)) {
    return day.slots[slotId] || null;
  }
  if (Array.isArray(day.slots)) {
    return day.slots.find((s) => s.slot_id === slotId) || null;
  }
  return day[slotId] || null;
}

function _resolvePair(state, dayN, slotId) {
  const day = _getDay(state, dayN);
  if (!day) return null;
  const nextSlotId = _nextSlotKey(slotId);
  if (!nextSlotId) return null;
  const fromSlot = _getSlot(day, slotId);
  const toSlot = _getSlot(day, nextSlotId);
  if (!fromSlot || !toSlot) return null;
  if (fromSlot.skipped || toSlot.skipped) return null;
  if (!fromSlot.selected_option_id || !toSlot.selected_option_id) return null;
  return {
    fromOptId: fromSlot.selected_option_id,
    toOptId: toSlot.selected_option_id,
    mode: "walk",
  };
}

async function _postRoute(state, dayN, pair, mySeq) {
  return wrappedFetch("/api/route", {
    method: "POST",
    body: JSON.stringify({
      trip_id: state.trip_id,
      day: dayN,
      from_option_id: pair.fromOptId,
      to_option_id: pair.toOptId,
      mode: pair.mode,
      request_seq: mySeq,
    }),
  });
}

export async function requestRouteForAdjacency(state, dayN, slotId) {
  const pair = _resolvePair(state, dayN, slotId);
  if (!pair) return;
  const key = _pairKey(pair.fromOptId, pair.toOptId, pair.mode);
  _seqCounter += 1;
  const mySeq = _seqCounter;
  state.ui._computing[key] = true;
  renderAll();
  try {
    const resp = await _postRoute(state, dayN, pair, mySeq);
    _handleRouteResponse(state, key, mySeq, resp);
  } catch (_err) {
    _markUnknown(state, key, mySeq);
  } finally {
    delete state.ui._computing[key];
    renderAll();
  }
}

function _handleRouteResponse(state, key, mySeq, resp) {
  const seenSeq = _latestSeen.get(key) || 0;
  if (mySeq < seenSeq) return;
  _latestSeen.set(key, mySeq);
  if (resp && resp.status === "ok" && resp.segment) {
    state.route_cache[key] = {
      duration_min: resp.segment.duration_min,
      distance_km: resp.segment.distance_km,
      polyline: resp.segment.polyline || null,
      status: "ok",
    };
    return;
  }
  state.route_cache[key] = { status: "unresolved" };
}

function _markUnknown(state, key, mySeq) {
  const seenSeq = _latestSeen.get(key) || 0;
  if (mySeq < seenSeq) return;
  _latestSeen.set(key, mySeq);
  state.route_cache[key] = { status: "unresolved" };
}
