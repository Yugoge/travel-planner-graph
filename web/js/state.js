/* state.js — central client store + render coordinator
 * Spec: spec-20260508-221237 §5.6 / §5.13 D
 *
 * Responsibilities:
 *   - Hydrate trip via GET /api/trip/<id> on page load
 *   - Hold reactive state {meta, days, transportation, route_cache, ui}
 *   - Re-render candidates + timeline + budget on commit()
 *   - Dispatch mutations to save.js, routing.js, budget.js
 *
 * No framework. Plain ES module. Vanilla DOM.
 */

import { wrappedFetch, setOnlineHandler } from "./offline.js";
import { queueSave, bindBeaconState } from "./save.js";
import { requestRouteForAdjacency } from "./routing.js";
import { recomputeBudget, renderBudget } from "./budget.js";
import { initDesktopDrag } from "./drag.js";
import { initMobile, isMobileViewport } from "./mobile.js";

/* ---------- Constants ---------- */

const NAMED_SLOTS = [
  "breakfast",
  "morning_activity",
  "lunch",
  "afternoon_activity",
  "dinner",
  "evening_activity",
];
const SLOT_LABELS = {
  breakfast: "Breakfast",
  morning_activity: "Morning",
  lunch: "Lunch",
  afternoon_activity: "Afternoon",
  dinner: "Dinner",
  evening_activity: "Evening",
  accommodation: "Accommodation",
};
const SLOT_TITLE_EMOJI = {
  breakfast: "🍽️",
  morning_activity: "🌅",
  lunch: "🍱",
  afternoon_activity: "☀️",
  dinner: "🍽️",
  evening_activity: "🌙",
  accommodation: "🏨",
};
function _timelineSlotLabel(slotId) {
  const emoji = SLOT_TITLE_EMOJI[slotId] || "";
  return emoji ? `${emoji} ${SLOT_LABELS[slotId] || slotId}` : (SLOT_LABELS[slotId] || slotId);
}
const MEAL_SLOTS = new Set(["breakfast", "lunch", "dinner"]);
const ALL_SLOT_KEYS = NAMED_SLOTS.concat(["accommodation"]);

const SKIPPED_REASON_LABEL = {
  "pre-arrival": "pre-arrival",
  "post-departure": "post-departure",
  "in-transit": "in-transit",
  "city-change": "city change",
  "red-eye-spans-prior-day": "red-eye prior day",
  "user-omit": "skipped",
  "buffer-rest": "buffer rest",
};

/* ---------- State ---------- */

export const state = {
  trip_id: null,
  meta: null,
  days: [],
  transportation: { segments: [] },
  route_cache: {},
  ui: {
    active_day: 1,
    editor_session: _generateSessionId(),
    selected_card_option_id: null,
    selected_card_slot_hint: null,
    last_save_ts: null,
    save_state: "saved",
    conflict_409_soft: false,
    offline: false,
    request_seqs: {},
    _computing: {},
  },
};

function _generateSessionId() {
  return (
    "sess-" +
    Date.now().toString(36) +
    "-" +
    Math.random().toString(36).slice(2, 9)
  );
}

/* ---------- Hydration ---------- */

function _parseTripIdFromUrl() {
  const m = /\/trip\/([^\/?#]+)/.exec(location.pathname);
  return m ? decodeURIComponent(m[1]) : null;
}

async function _fetchTrip(trip_id) {
  const data = await wrappedFetch(
    `/api/trip/${encodeURIComponent(trip_id)}`,
    { method: "GET" },
  );
  state.meta = data.meta || null;
  state.days = Array.isArray(data.days) ? data.days : [];
  state.transportation = data.transportation || { segments: [] };
  // route_cache may arrive as {schema_version, entries} (loaders.py) OR flat dict.
  const rc = data.route_cache || {};
  state.route_cache = rc && rc.entries ? rc.entries : rc;
}

export async function init() {
  const trip_id = _parseTripIdFromUrl();
  if (!trip_id) {
    _showFatal("URL must be /trip/<trip_id>");
    return;
  }
  state.trip_id = trip_id;
  try {
    await _fetchTrip(trip_id);
  } catch (err) {
    _showFatal("Failed to load trip: " + err.message);
    return;
  }
  _wireGlobalControls();
  initDesktopDrag(commit, requestSelectMutation);
  initMobile(commit, requestSelectMutation);
  setOnlineHandler(_onOnlineStateChange);
  bindBeaconState(state);
  renderAll();
  recomputeBudget(state, getActiveDayNumber());
}

/* ---------- Renderers ---------- */

export function renderAll() {
  renderHeader();
  renderDaysPanel();
  _populateMobileDaySelect();
  renderCandidates();
  renderTimeline();
  renderBudget(state);
  renderApproveButton();
  renderExportButtons();
}

function renderHeader() {
  _renderTitle();
  _renderSaveStatus();
  _renderConnStatus();
  document.getElementById("banner-conflict").hidden =
    !state.ui.conflict_409_soft;
}

function _renderTitle() {
  const title = document.getElementById("trip-title");
  if (!state.meta) return;
  title.textContent =
    state.meta.trip_name || state.meta.title || state.meta.trip_id || state.trip_id;
}

function _renderSaveStatus() {
  const save = document.getElementById("save-status");
  save.dataset.state = state.ui.save_state;
  if (state.ui.save_state === "saving") {
    save.textContent = "saving...";
    return;
  }
  if (state.ui.save_state === "error") {
    save.textContent = "save error";
    return;
  }
  if (!state.ui.last_save_ts) {
    save.textContent = "saved";
    return;
  }
  const seconds = Math.max(
    0,
    Math.floor((Date.now() - state.ui.last_save_ts) / 1000),
  );
  save.textContent = `saved ${seconds}s ago`;
}

function _renderConnStatus() {
  const conn = document.getElementById("conn-status");
  conn.dataset.state = state.ui.offline ? "offline" : "online";
  conn.textContent = state.ui.offline ? "offline" : "online";
}

function _buildMealsCandidateGroup(day) {
  const MEAL_SLOT_KEYS = ["breakfast", "lunch", "dinner"];
  const group = document.createElement("div");
  group.className = "candidate-group";
  const h = document.createElement("h3");
  h.className = "candidate-group-title";
  h.textContent = "Meals";
  group.appendChild(h);

  // Collect options from all meal slots, de-duped by option_id
  const seen = new Set();
  const mealOptions = [];
  for (const slotId of MEAL_SLOT_KEYS) {
    const slot = _getSlotByKey(day, slotId);
    if (!slot || slot.skipped) continue;
    for (const opt of (slot.options || [])) {
      if (!seen.has(opt.option_id)) {
        seen.add(opt.option_id);
        mealOptions.push({ opt, originSlotId: slotId });
      }
    }
  }

  // Empty state: all meal slots are skipped or have no options
  if (mealOptions.length === 0) {
    const e = document.createElement("p");
    e.className = "candidate-group-empty";
    e.textContent = "(no meal candidates)";
    group.appendChild(e);
    return group;
  }

  // Check selection: option is selected if ANY meal slot has it as selected_option_id
  const anyMealSelectedId = MEAL_SLOT_KEYS.map(k => _getSlotByKey(day, k))
    .filter(Boolean).map(s => s.selected_option_id).find(Boolean) || null;

  for (const { opt, originSlotId } of mealOptions) {
    const tpl = document.getElementById("tpl-candidate-card");
    const node = tpl.content.firstElementChild.cloneNode(true);
    node.dataset.optionId = opt.option_id;
    node.dataset.slotId = "meals-any";
    node.dataset.originSlotId = originSlotId;
    node.dataset.sourceAgent = opt.source_agent || "";
    node.setAttribute("draggable", isMobileViewport() ? "false" : "true");
    _writeCardName(node, opt);
    _writeCardCost(node, opt);
    node.querySelector(".card-location").textContent = opt.location_summary || "";
    node.querySelector(".card-why").textContent = opt.why_fits_user || "";
    _writeCardSource(node, opt);
    _writeCardRationale(node, opt);
    // Selection: any meal slot selected this option
    const isSelected = MEAL_SLOT_KEYS.some(k => {
      const s = _getSlotByKey(day, k);
      return s && s.selected_option_id === opt.option_id;
    });
    if (isSelected) {
      node.classList.add("card-selected");
      node.setAttribute("aria-pressed", "true");
    }
    if (isMobileViewport() && state.ui.selected_card_option_id === opt.option_id) {
      node.classList.add("tap-selected");
    }
    group.appendChild(node);
  }
  return group;
}

function renderCandidates() {
  const container = document.getElementById("candidates-groups");
  container.innerHTML = "";
  const day = _getActiveDay();
  if (!day) return;
  // Unified Meals group replaces separate breakfast/lunch/dinner groups
  container.appendChild(_buildMealsCandidateGroup(day));
  // Non-meal slots use original per-slot group builder
  const NON_MEAL_SLOTS = ALL_SLOT_KEYS.filter(k => !MEAL_SLOTS.has(k));
  for (const slotId of NON_MEAL_SLOTS) {
    container.appendChild(_buildCandidateGroup(day, slotId));
  }
}

function _buildCandidateGroup(day, slotId) {
  const slot = _getSlotByKey(day, slotId);
  const group = document.createElement("div");
  group.className = "candidate-group";
  const h = document.createElement("h3");
  h.className = "candidate-group-title";
  h.textContent = SLOT_LABELS[slotId];
  group.appendChild(h);
  if (!slot || !slot.options || slot.options.length === 0) {
    group.appendChild(_buildEmptyGroupMessage(slot));
    return group;
  }
  for (const opt of slot.options) {
    group.appendChild(_buildCard(opt, slotId, slot));
  }
  return group;
}

function _buildEmptyGroupMessage(slot) {
  const e = document.createElement("p");
  e.className = "candidate-group-empty";
  if (slot && slot.skipped) {
    e.textContent =
      "skipped — " +
      (SKIPPED_REASON_LABEL[slot.skipped_reason] ||
        slot.skipped_reason ||
        "skipped");
  } else {
    e.textContent = "(no candidates)";
  }
  return e;
}

function _buildCard(opt, slotId, slot) {
  const tpl = document.getElementById("tpl-candidate-card");
  const node = tpl.content.firstElementChild.cloneNode(true);
  node.dataset.optionId = opt.option_id;
  node.dataset.slotId = slotId;
  node.dataset.sourceAgent = opt.source_agent || "";
  node.setAttribute("draggable", isMobileViewport() ? "false" : "true");
  _writeCardName(node, opt);
  _writeCardCost(node, opt);
  node.querySelector(".card-location").textContent = opt.location_summary || "";
  node.querySelector(".card-why").textContent = opt.why_fits_user || "";
  _writeCardSource(node, opt);
  _writeCardRationale(node, opt);
  _markCardSelectionState(node, opt, slot);
  return node;
}

function _writeCardName(node, opt) {
  node.querySelector(".card-name").textContent =
    opt.name_local && opt.name_local !== opt.name
      ? `${opt.name} (${opt.name_local})`
      : opt.name || "(unnamed)";
}

function _writeCardCost(node, opt) {
  const costEl = node.querySelector(".card-cost");
  if (opt.cost === null || opt.cost === undefined) {
    costEl.textContent = "cost: unknown";
    costEl.classList.add("unknown");
    return;
  }
  const cur = opt.currency_local || state.meta?.currency_local || "";
  costEl.textContent = `${opt.cost} ${cur}`.trim();
}

function _writeCardSource(node, opt) {
  const src = node.querySelector(".card-source");
  if (opt.source_citation && opt.source_citation.length) {
    src.textContent = "source: " + opt.source_citation.join(", ");
  } else {
    src.remove();
  }
}

function _writeCardRationale(node, opt) {
  const rationale = node.querySelector(".card-rationale");
  const prov = opt.provenance;
  if (prov && prov.selected_by === "auto") {
    rationale.hidden = false;
    rationale.textContent =
      "auto-selected: " + (prov.selected_reason || "fit_score");
  }
}

function _markCardSelectionState(node, opt, slot) {
  if (slot && slot.selected_option_id === opt.option_id) {
    node.classList.add("card-selected");
    node.setAttribute("aria-pressed", "true");
  }
  if (
    isMobileViewport() &&
    state.ui.selected_card_option_id === opt.option_id
  ) {
    node.classList.add("tap-selected");
  }
}

function _formatTs(ts) {
  return ts ? ts.slice(11, 16) : "";
}

function _buildTransportCallout(day) {
  const parts = [];
  if (day.departure_ts) parts.push("Departs " + _formatTs(day.departure_ts));
  if (day.arrival_ts) parts.push("Arrives " + _formatTs(day.arrival_ts));
  if (!parts.length) return null;
  const div = document.createElement("div");
  div.className = "transport-callout";
  div.setAttribute("aria-label", "transportation");
  const label = day.day_type ? (SKIPPED_REASON_LABEL[day.day_type] || day.day_type) : "";
  div.textContent = parts.join(" · ") + (label ? " · " + label : "");
  return div;
}

function _formatDayHeadingDate(isoDate) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate || "");
  if (!m) return "";
  const dt = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC", month: "short", day: "numeric", weekday: "short",
  }).formatToParts(dt);
  const get = (type) => parts.find((p) => p.type === type)?.value;
  return `${get("month")} ${get("day")} (${get("weekday")})`;
}

function renderTimeline() {
  const container = document.getElementById("timeline-slots");
  container.innerHTML = "";
  const day = _getActiveDay();
  if (!day) return;
  const heading = document.createElement("h2");
  heading.className = "day-heading";
  const city = _deriveCityName(day);
  const dateStr = _formatDayHeadingDate(day.date);
  heading.textContent = city ? `${dateStr} – ${city}` : dateStr;
  container.appendChild(heading);
  const callout = _buildTransportCallout(day);
  if (callout) container.appendChild(callout);
  for (const slotId of ALL_SLOT_KEYS) {
    const slot = _getSlotByKey(day, slotId);
    container.appendChild(_buildSlotNode(slotId, slot));
  }
}

function _buildSlotNode(slotId, slot) {
  const tpl = document.getElementById("tpl-slot");
  const node = tpl.content.firstElementChild.cloneNode(true);
  node.dataset.slotId = slotId;
  node.querySelector(".slot-title").textContent = _timelineSlotLabel(slotId);
  if (!slot) return _markSlotMissing(node);
  if (slot.skipped) return _markSlotSkipped(node, slot);
  if (slot.late_arrival_placeholder) {
    node.querySelector(".slot-status").textContent = "late arrival";
  }
  const sel = _findSelectedOption(slot);
  if (sel) {
    _writeSlotSelected(node, sel);
  } else if (_isRequiredSlot(slotId)) {
    _markSlotRequiredEmpty(node);
  }
  _maybeRenderRouteGap(node, slotId);
  return node;
}

function _markSlotMissing(node) {
  node.dataset.state = "error";
  node.querySelector(".slot-status").textContent = "missing";
  const err = node.querySelector(".slot-error");
  err.hidden = false;
  err.textContent = "Slot missing — schema error";
  node.querySelector(".slot-drop").dataset.droppable = "false";
  return node;
}

function _markSlotSkipped(node, slot) {
  node.dataset.state = "skipped";
  node.querySelector(".slot-status").textContent =
    "skipped — " +
    (SKIPPED_REASON_LABEL[slot.skipped_reason] ||
      slot.skipped_reason ||
      "skipped");
  node.querySelector(".slot-empty").textContent = "(skipped)";
  node.querySelector(".slot-drop").dataset.droppable = "false";
  return node;
}

function _writeSlotSelected(node, sel) {
  node.querySelector(".slot-empty").hidden = true;
  const selEl = node.querySelector(".slot-selected");
  selEl.hidden = false;
  selEl.innerHTML = "";
  const nameDiv = document.createElement("div");
  nameDiv.className = "selected-name";
  nameDiv.textContent = sel.name || "(unnamed)";
  selEl.appendChild(nameDiv);
  const metaDiv = document.createElement("div");
  metaDiv.className = "selected-meta";
  metaDiv.textContent = _formatSelectedMeta(sel);
  selEl.appendChild(metaDiv);
}

function _formatSelectedMeta(sel) {
  const parts = [];
  if (sel.location_summary) parts.push(sel.location_summary);
  if (sel.cost === null || sel.cost === undefined) {
    parts.push("cost: unknown");
  } else {
    const cur = sel.currency_local || state.meta?.currency_local || "";
    parts.push(`${sel.cost} ${cur}`.trim());
  }
  return parts.join(" · ");
}

function _markSlotRequiredEmpty(node) {
  node.dataset.state = "error";
  const err = node.querySelector(".slot-error");
  err.hidden = false;
  err.textContent = "Selection required";
}

function _maybeRenderRouteGap(node, slotId) {
  const routeState = _routeStateForSlotGap(slotId);
  if (!routeState) return;
  const routeEl = node.querySelector(".slot-route-gap");
  routeEl.hidden = false;
  routeEl.dataset.routeState = routeState.state;
  routeEl.querySelector(".route-text").textContent = routeState.text;
  const retry = routeEl.querySelector(".route-retry");
  if (routeState.state === "unknown") {
    retry.hidden = false;
    retry.addEventListener("click", () =>
      requestRouteForAdjacency(state, getActiveDayNumber(), slotId),
    );
  }
}

function _isRequiredSlot(slotId) {
  if (slotId === "accommodation") return true;
  return MEAL_SLOTS.has(slotId);
}

function _routeStateForSlotGap(slotId) {
  const day = _getActiveDay();
  if (!day) return null;
  const idx = NAMED_SLOTS.indexOf(slotId);
  if (idx < 0 || idx === NAMED_SLOTS.length - 1) return null;
  const slot = _getSlotByKey(day, slotId);
  const next = _getSlotByKey(day, NAMED_SLOTS[idx + 1]);
  if (!slot || !next || slot.skipped || next.skipped) return null;
  if (!slot.selected_option_id || !next.selected_option_id) return null;
  const key = `${slot.selected_option_id}:${next.selected_option_id}:walk`;
  if (state.ui._computing[key]) {
    return { state: "computing", text: "computing route..." };
  }
  const cached = state.route_cache[key];
  if (cached && cached.status === "unresolved") {
    return { state: "unknown", text: "route unknown" };
  }
  if (cached && cached.duration_min !== undefined) {
    return { state: "ok", text: `${cached.duration_min} min` };
  }
  return null;
}

function renderApproveButton() {
  const btn = document.getElementById("approve-day-btn");
  if (!btn) return;
  const day = _getActiveDay();
  if (!day) {
    btn.disabled = true;
    return;
  }
  const allFilled = _allRequiredSlotsFilled(day);
  const stageOk = day.stage === "draft-options" || day.stage === "user-review";
  btn.disabled = !(allFilled && stageOk);
  btn.onclick = _onApproveDay;
}

function _allRequiredSlotsFilled(day) {
  for (const slotId of ALL_SLOT_KEYS) {
    const slot = _getSlotByKey(day, slotId);
    if (!slot) return false;
    if (slot.skipped) continue;
    if (!slot.selected_option_id) return false;
  }
  return true;
}

function _onApproveDay() {
  const dayN = getActiveDayNumber();
  // Backend mutation handler key is "stage" with `to_stage` per save.py:69.
  queueSave(state, dayN, {
    type: "stage",
    to_stage: "user-selected",
  });
  // Optimistic local update so renderApproveButton() disables immediately.
  const day = _getDay(dayN);
  if (day) day.stage = "user-selected";
  renderAll();
}

function renderExportButtons() {
  const anyError = _anyValidationError();
  const allReady = state.days.every((d) =>
    ["user-selected", "timeline", "transportation", "finalized"].includes(
      d.stage,
    ),
  );
  const enabled = !anyError && allReady && !state.ui.offline;
  document.getElementById("export-pdf").disabled = !enabled;
  document.getElementById("export-ical").disabled = !enabled;
}

function _anyValidationError() {
  for (const day of state.days) {
    if (!_allRequiredSlotsFilled(day)) return true;
  }
  return false;
}

/* ---------- Mutation entry-point ---------- */

const MEAL_SLOT_KEYS_ARR = ["breakfast", "lunch", "dinner"];

export function requestSelectMutation({ slotId, optionId, originSlotId, dayN }) {
  const day = _getDay(dayN);
  if (!day) return;
  const slot = _getSlotByKey(day, slotId);
  if (!slot) return;
  // Cross-meal client-side option copy: if target slot lacks the option, add it (idempotent)
  if (optionId && MEAL_SLOTS.has(slotId)) {
    const alreadyInTarget = (slot.options || []).some(o => o.option_id === optionId);
    if (!alreadyInTarget) {
      const srcOpt = MEAL_SLOT_KEYS_ARR
        .map(k => _getSlotByKey(day, k))
        .filter(Boolean)
        .flatMap(s => s.options || [])
        .find(o => o.option_id === optionId);
      if (srcOpt) {
        if (!slot.options) slot.options = [];
        slot.options.push({ ...srcOpt });
      }
    }
  }
  slot.selected_option_id = optionId;
  commit({
    type: "select",
    slot: slotId,
    option_id: optionId,
    origin_slot_id: originSlotId || null,
  }, dayN);
  _scheduleRouteOnSelectionChange(dayN, slotId);
}

export function commit(mutation, dayN) {
  queueSave(state, dayN, mutation);
  renderAll();
  recomputeBudget(state, dayN);
}

function _scheduleRouteOnSelectionChange(dayN, slotId) {
  const idx = NAMED_SLOTS.indexOf(slotId);
  if (idx < 0) return;
  if (idx > 0) requestRouteForAdjacency(state, dayN, NAMED_SLOTS[idx - 1]);
  if (idx < NAMED_SLOTS.length - 1) {
    requestRouteForAdjacency(state, dayN, slotId);
  }
}

/* ---------- Helpers exposed to other modules ---------- */

export function getActiveDayNumber() {
  return state.ui.active_day;
}

export function setActiveDay(dayN) {
  state.ui.active_day = dayN;
  renderAll();
  recomputeBudget(state, dayN);
}

export function getDay(dayN) {
  return _getDay(dayN);
}

export function getSlot(day, slotId) {
  return _getSlotByKey(day, slotId);
}

function _getDay(dayN) {
  return (
    state.days.find((d) => d.day === dayN || d.day_number === dayN) ||
    state.days[dayN - 1] ||
    null
  );
}

function _getActiveDay() {
  return _getDay(state.ui.active_day);
}

function _getSlotByKey(day, slotId) {
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

function _findSelectedOption(slot) {
  if (!slot || !slot.selected_option_id) return null;
  return (
    (slot.options || []).find((o) => o.option_id === slot.selected_option_id) ||
    null
  );
}

/* ---------- Day-picker + global UI wiring ---------- */

function _deriveCityName(day) {
  const acc = day.accommodation;
  if (acc && acc.selected_option_id) {
    const opt = (acc.options || []).find(o => o.option_id === acc.selected_option_id);
    if (opt?.city_context?.city_name) return opt.city_context.city_name;
  }
  return day.city_name || "";
}

function renderDaysPanel() {
  const list = document.getElementById("days-list");
  if (!list) return;
  list.innerHTML = "";
  for (const day of state.days) {
    const dayN = day.day || day.day_number;
    const cityName = _deriveCityName(day);
    const row = document.createElement("button");
    row.className = "day-row" + (dayN === state.ui.active_day ? " day-row--active" : "");
    row.dataset.dayN = String(dayN);
    row.setAttribute("aria-label", cityName ? `Day ${dayN} · ${cityName}` : `Day ${dayN}`);
    const label = document.createElement("span");
    label.className = "day-row-label day-title";
    label.textContent = `Day ${dayN}`;
    row.appendChild(label);
    if (cityName) {
      const sep = document.createElement("span");
      sep.className = "day-row-sep";
      sep.setAttribute("aria-hidden", "true");
      sep.textContent = " · ";
      const city = document.createElement("span");
      city.className = "day-row-city";
      city.textContent = cityName;
      row.appendChild(sep);
      row.appendChild(city);
    }
    row.addEventListener("click", () => setActiveDay(dayN));
    list.appendChild(row);
  }
}

function _populateMobileDaySelect() {
  const sel = document.getElementById("mobile-day-select");
  if (!sel) return;
  sel.innerHTML = "";
  for (const day of state.days) {
    const dayN = day.day || day.day_number;
    const cityName = _deriveCityName(day);
    const opt = document.createElement("option");
    opt.value = String(dayN);
    opt.textContent = cityName ? `Day ${dayN} · ${cityName}` : `Day ${dayN}`;
    opt.selected = dayN === state.ui.active_day;
    sel.appendChild(opt);
  }
  sel.onchange = () => { setActiveDay(parseInt(sel.value, 10)); };
}

function _wireGlobalControls() {
  _wireBannerCloses();
  _wireMiddleTabs();
  document
    .getElementById("export-pdf")
    .addEventListener("click", () => _onExport("pdf"));
  document
    .getElementById("export-ical")
    .addEventListener("click", () => _onExport("ical"));
  setInterval(renderHeader, 15000);
}

function _wireMiddleTabs() {
  document.querySelectorAll(".middle-tab").forEach(btn => {
    btn.addEventListener("click", () => _activateMiddleTab(btn.dataset.tab));
  });
  // Default: Timeline tab active on load
  _activateMiddleTab("timeline");
}

function _activateMiddleTab(tab) {
  document.querySelectorAll(".middle-tab").forEach(b => {
    b.classList.toggle("tab-btn--active", b.dataset.tab === tab);
    b.setAttribute("aria-selected", b.dataset.tab === tab ? "true" : "false");
  });
  const dashEl = document.getElementById("tab-dashboard");
  const timeEl = document.getElementById("tab-timeline");
  if (dashEl) dashEl.hidden = (tab !== "dashboard");
  if (timeEl) timeEl.hidden = (tab !== "timeline");
  if (tab === "dashboard") renderBudget(state);
}

function _wireBannerCloses() {
  const closeBtn = document
    .getElementById("banner-conflict")
    .querySelector(".banner-close");
  closeBtn.addEventListener("click", () => {
    state.ui.conflict_409_soft = false;
    renderHeader();
  });
}

async function _onExport(kind) {
  try {
    const data = await wrappedFetch(`/api/export/${kind}`, {
      method: "POST",
      body: JSON.stringify({ trip_id: state.trip_id }),
    });
    if (data && data.file_path) {
      const save = document.getElementById("save-status");
      save.textContent = `exported ${kind}: ${data.file_path}`;
    }
  } catch (err) {
    const save = document.getElementById("save-status");
    save.dataset.state = "error";
    save.textContent = `export ${kind} failed`;
  }
}

function _onOnlineStateChange(isOffline) {
  state.ui.offline = isOffline;
  document.body.dataset.editing = isOffline ? "disabled" : "active";
  document.getElementById("banner-offline").hidden = !isOffline;
  renderHeader();
  renderExportButtons();
}

function _showFatal(msg) {
  const title = document.getElementById("trip-title");
  if (title) title.textContent = msg;
  document.body.dataset.editing = "disabled";
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => init());
} else {
  init();
}
