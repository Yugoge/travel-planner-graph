/* drag.js — desktop HTML5 drag-drop (>=640px viewport)
 * Spec: §5.6 #2 + §5.13 D #1
 *
 * Card -> slot drop. Card carries data-option-id + data-slot-id (its category).
 * Drop targets are .slot-drop nodes whose parent .slot has matching slot-id.
 * Mismatched slot categories are rejected (e.g. cannot drop dinner card on breakfast).
 */

import { getActiveDayNumber } from "./state.js";
import { isMobileViewport } from "./mobile.js";

let _committedRequest = null;

export function initDesktopDrag(_commit, requestSelectMutation) {
  _committedRequest = requestSelectMutation;
  _bindCandidatesDelegated();
  _bindTimelineDelegated();
}

function _bindCandidatesDelegated() {
  const root = document.getElementById("candidates-groups");
  if (!root) return;
  root.addEventListener("dragstart", _onDragStart);
  root.addEventListener("dragend", _onDragEnd);
}

function _bindTimelineDelegated() {
  const root = document.getElementById("timeline-slots");
  if (!root) return;
  root.addEventListener("dragover", _onDragOver);
  root.addEventListener("dragleave", _onDragLeave);
  root.addEventListener("drop", _onDrop);
}

function _isMobile() {
  return isMobileViewport();
}

function _onDragStart(ev) {
  if (_isMobile()) return;
  const card = _closestCard(ev.target);
  if (!card) return;
  ev.dataTransfer.effectAllowed = "move";
  ev.dataTransfer.setData(
    "application/x-trip-option",
    JSON.stringify({
      option_id: card.dataset.optionId,
      slot_id: card.dataset.slotId,
      origin_slot_id: card.dataset.originSlotId || null,
    }),
  );
  // Fallback for cross-browser dataTransfer empty payload behavior
  ev.dataTransfer.setData("text/plain", card.dataset.optionId || "");
  card.setAttribute("aria-grabbed", "true");
}

function _onDragEnd(ev) {
  const card = _closestCard(ev.target);
  if (card) card.removeAttribute("aria-grabbed");
}

function _closestCard(node) {
  if (!node || !node.closest) return null;
  return node.closest(".card-candidate");
}

function _closestDrop(node) {
  if (!node || !node.closest) return null;
  return node.closest(".slot-drop");
}

function _onDragOver(ev) {
  const drop = _closestDrop(ev.target);
  if (!drop) return;
  if (drop.dataset.droppable === "false") return;
  ev.preventDefault();
  ev.dataTransfer.dropEffect = "move";
  drop.dataset.dropActive = "true";
}

function _onDragLeave(ev) {
  const drop = _closestDrop(ev.target);
  if (drop) delete drop.dataset.dropActive;
}

function _parsePayload(ev) {
  try {
    const raw = ev.dataTransfer.getData("application/x-trip-option");
    if (raw) return JSON.parse(raw);
  } catch (_e) {
    /* fallthrough */
  }
  const id = ev.dataTransfer.getData("text/plain");
  return id ? { option_id: id, slot_id: null } : null;
}

function _onDrop(ev) {
  const drop = _closestDrop(ev.target);
  if (!drop) return;
  ev.preventDefault();
  delete drop.dataset.dropActive;
  const targetSlot = drop.closest(".slot");
  if (!targetSlot) return;
  const slotId = targetSlot.dataset.slotId;
  const payload = _parsePayload(ev);
  if (!payload || !payload.option_id) return;
  if (
    payload.slot_id &&
    payload.slot_id !== slotId &&
    !_isCompatible(payload.slot_id, slotId)
  ) {
    _showRejectFeedback(drop);
    return;
  }
  _committedRequest({
    slotId,
    optionId: payload.option_id,
    originSlotId: payload.origin_slot_id || null,
    dayN: getActiveDayNumber(),
  });
}

const MEAL_SLOT_IDS = new Set(["breakfast", "lunch", "dinner"]);

function _isCompatible(srcSlot, targetSlot) {
  const srcIsMeal = srcSlot === "meals-any" || MEAL_SLOT_IDS.has(srcSlot);
  const targetIsMeal = MEAL_SLOT_IDS.has(targetSlot);
  if (srcIsMeal || targetIsMeal) return srcIsMeal && targetIsMeal;
  return srcSlot === targetSlot;
}

function _showRejectFeedback(drop) {
  drop.dataset.dropReject = "true";
  setTimeout(() => delete drop.dataset.dropReject, 400);
}
