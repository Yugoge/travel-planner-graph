/* mobile.js — <640px tab-collapse + tap-to-select + tap-to-place
 * Spec: §5.13 D #8 (mobile parity, identical mutation)
 *
 * On <640px viewport:
 *   - Tabs at top let the user switch which pane is visible (candidates|timeline|budget).
 *   - Tapping a candidate card highlights it AND highlights compatible drop slots.
 *   - Tapping a highlighted slot commits the same select mutation as desktop drag.
 *
 * Note: window.matchMedia is recomputed on resize so a single page session works
 * across orientation changes.
 */

import { state, getActiveDayNumber } from "./state.js";

const MOBILE_BREAKPOINT_PX = 640;
let _mediaQuery = null;
let _commit = null;
let _requestSelectMutation = null;

const MEAL_SLOT_IDS = new Set(["breakfast", "lunch", "dinner"]);

function _isCompatible(srcSlot, targetSlot) {
  const srcIsMeal = srcSlot === "meals-any" || MEAL_SLOT_IDS.has(srcSlot);
  const targetIsMeal = MEAL_SLOT_IDS.has(targetSlot);
  if (srcIsMeal || targetIsMeal) return srcIsMeal && targetIsMeal;
  return srcSlot === targetSlot;
}

export function isMobileViewport() {
  if (!_mediaQuery) {
    _mediaQuery = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT_PX - 1}px)`);
  }
  return _mediaQuery.matches;
}

export function initMobile(commit, requestSelectMutation) {
  _commit = commit;
  _requestSelectMutation = requestSelectMutation;
  _wireTabs();
  _wireCardTap();
  _wireSlotTap();
  _applyMobileLayout();
  window.addEventListener("resize", _applyMobileLayout);
}

function _wireTabs() {
  const tabs = document.querySelectorAll("#mobile-tabs .tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => _activateTab(tab.dataset.pane));
  });
}

function _activateTab(pane) {
  document.querySelectorAll("#mobile-tabs .tab").forEach((t) => {
    t.setAttribute("aria-pressed", t.dataset.pane === pane ? "true" : "false");
  });
  for (const p of ["candidates", "timeline", "budget"]) {
    const el = document.getElementById(`pane-${p}`);
    if (el) el.dataset.mobileHidden = p === pane ? "false" : "true";
  }
}

function _wireCardTap() {
  const root = document.getElementById("candidates-groups");
  if (!root) return;
  root.addEventListener("click", _onCardClick);
}

function _onCardClick(ev) {
  if (!isMobileViewport()) return;
  const card = ev.target.closest && ev.target.closest(".card-candidate");
  if (!card) return;
  const optionId = card.dataset.optionId;
  const slotId = card.dataset.slotId;
  if (state.ui.selected_card_option_id === optionId) {
    _clearSelection();
  } else {
    state.ui.selected_card_option_id = optionId;
    state.ui.selected_card_slot_hint = slotId;
    state.ui.selected_card_origin_slot_id = card.dataset.originSlotId || null;
    _markTapTargets(slotId);
  }
  _refreshCardClasses();
}

function _wireSlotTap() {
  const root = document.getElementById("timeline-slots");
  if (!root) return;
  root.addEventListener("click", _onSlotClick);
}

function _onSlotClick(ev) {
  if (!isMobileViewport()) return;
  if (!state.ui.selected_card_option_id) return;
  const dropEl = ev.target.closest && ev.target.closest(".slot-drop");
  if (!dropEl) return;
  if (dropEl.dataset.tapTarget !== "true") return;
  const slotEl = dropEl.closest(".slot");
  if (!slotEl) return;
  const slotId = slotEl.dataset.slotId;
  _requestSelectMutation({
    slotId,
    optionId: state.ui.selected_card_option_id,
    originSlotId: state.ui.selected_card_origin_slot_id || null,
    dayN: getActiveDayNumber(),
  });
  _clearSelection();
}

function _clearSelection() {
  state.ui.selected_card_option_id = null;
  state.ui.selected_card_slot_hint = null;
  state.ui.selected_card_origin_slot_id = null;
  document.querySelectorAll(".slot-drop[data-tap-target='true']").forEach((el) =>
    delete el.dataset.tapTarget,
  );
}

function _markTapTargets(slotIdHint) {
  document.querySelectorAll(".slot").forEach((s) => {
    const drop = s.querySelector(".slot-drop");
    if (!drop) return;
    if (drop.dataset.droppable === "false") return;
    const isTarget = _isCompatible(slotIdHint, s.dataset.slotId);
    drop.dataset.tapTarget = isTarget ? "true" : "false";
    if (drop.dataset.tapTarget === "false") delete drop.dataset.tapTarget;
  });
}

function _refreshCardClasses() {
  document.querySelectorAll(".card-candidate").forEach((card) => {
    if (card.dataset.optionId === state.ui.selected_card_option_id) {
      card.classList.add("tap-selected");
    } else {
      card.classList.remove("tap-selected");
    }
  });
}

let _mobileLayoutApplied = false;

function _applyMobileLayout() {
  const mobile = isMobileViewport();
  const tabs = document.getElementById("mobile-tabs");
  if (tabs) tabs.hidden = !mobile;
  if (mobile) {
    // ALWAYS collapse other panes on first mobile activation. The HTML scaffold
    // ships with a tab pre-marked aria-pressed=true but no data-mobile-hidden
    // on the panes, so without this call all three panes stack visibly.
    if (!_mobileLayoutApplied) {
      _activateTab("candidates");
      _mobileLayoutApplied = true;
    }
  } else {
    _mobileLayoutApplied = false;
    for (const p of ["candidates", "timeline", "budget"]) {
      const el = document.getElementById(`pane-${p}`);
      if (el) delete el.dataset.mobileHidden;
    }
  }
}
