/* drag.js — desktop HTML5 drag-drop (>=640px viewport)
 * Spec: §5.6 #2 + §5.13 D #1
 *
 * Card -> slot drop. Card carries data-option-id + data-slot-id (its category).
 * Drop targets are .slot-drop nodes whose parent .slot has matching slot-id.
 * Mismatched slot categories are rejected (e.g. cannot drop dinner card on breakfast).
 *
 * S2 refactor: initEditorDrag() is framework-neutral. It accepts callbacks and
 * does NOT import from state.js or mobile.js. Initialized by React useEffect.
 */

let _committedRequest = null;
let _getActiveDayNumber = null;

/**
 * Initialize editor drag-and-drop.
 *
 * @param {Element|null} candidatesRoot - Container holding .card-candidate elements
 * @param {Element|null} dropRoot - Container holding .slot-drop elements
 * @param {function} getActiveDayFn - Returns the current absolute day number
 * @param {function} onDropFn - Called with {slotId, optionId, dayN} on successful drop
 */
export function initEditorDrag(candidatesRoot, dropRoot, getActiveDayFn, onDropFn) {
  _committedRequest = onDropFn;
  _getActiveDayNumber = getActiveDayFn;
  if (candidatesRoot) {
    candidatesRoot.addEventListener("dragstart", _onDragStart);
    candidatesRoot.addEventListener("dragend", _onDragEnd);
  }
  if (dropRoot) {
    dropRoot.addEventListener("dragover", _onDragOver);
    dropRoot.addEventListener("dragleave", _onDragLeave);
    dropRoot.addEventListener("drop", _onDrop);
  }
}

// Legacy entry point preserved for backward compatibility (not used in React path)
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
  return window.innerWidth < 640;
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

  // Resolve slotId: prefer data-slot-id on the .slot-drop element itself (React path),
  // fall back to closest .slot parent (legacy path).
  let slotId = drop.dataset.slotId;
  if (!slotId) {
    const targetSlot = drop.closest(".slot");
    if (!targetSlot) return;
    slotId = targetSlot.dataset.slotId;
  }

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
  const dayN = _getActiveDayNumber ? _getActiveDayNumber() : null;

  // React-path bridge: call window.setEditorSelection if available
  if (typeof window.setEditorSelection === 'function') {
    window.setEditorSelection(slotId, payload.option_id);
  } else if (_committedRequest) {
    _committedRequest({
      slotId,
      optionId: payload.option_id,
      originSlotId: payload.origin_slot_id || null,
      dayN,
    });
  }
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
