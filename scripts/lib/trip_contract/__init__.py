"""M2 Trip Contract Library (spec-20260508-221237).

Public API re-exported here. Submodules: constants, errors, loaders,
state_machine, day_type, transport, legacy, validators, api_contract.
See docs/dev/specs/spec-20260508-221237/M2-contract.md for the full contract.
"""

from .constants import (
    SCHEMA_VERSION,
    STAGES,
    STAGE_INDEX,
    DAY_TYPES,
    NAMED_SLOTS,
    ACCOMMODATION_SLOT,
    SKIP_THRESHOLDS,
    VALID_SKIP_REASONS,
    CITY_ROLES,
    LEGACY_SHAPE_KEYS,
)
from .errors import ValidationError, TripContractError
from .loaders import (
    TripBundle,
    load_trip,
    load_meta,
    load_day,
    load_transportation,
    load_route_cache,
)
from .state_machine import (
    validate_state_transition,
    blocking_stage,
    furthest_stage,
    all_days_at_least,
)
from .day_type import expected_skips_for_day, is_slot_skipped, get_day_type
from .transport import pick_owning_day
from .legacy import detect_legacy_shape
from .validators import validate_day_v2, validate_meta_v2, validate_trip_v2
from .api_contract import (
    RouteRequest,
    RouteResponse,
    BudgetRequest,
    BudgetResponse,
    SaveMutation,
    SaveRequest,
    SaveResponse,
    TripResponse,
    ExportRequest,
    ExportResponse,
)

__all__ = [
    "SCHEMA_VERSION",
    "STAGES",
    "STAGE_INDEX",
    "DAY_TYPES",
    "NAMED_SLOTS",
    "ACCOMMODATION_SLOT",
    "SKIP_THRESHOLDS",
    "VALID_SKIP_REASONS",
    "CITY_ROLES",
    "LEGACY_SHAPE_KEYS",
    "ValidationError",
    "TripContractError",
    "TripBundle",
    "load_trip",
    "load_meta",
    "load_day",
    "load_transportation",
    "load_route_cache",
    "validate_state_transition",
    "blocking_stage",
    "furthest_stage",
    "all_days_at_least",
    "expected_skips_for_day",
    "is_slot_skipped",
    "get_day_type",
    "pick_owning_day",
    "detect_legacy_shape",
    "validate_day_v2",
    "validate_meta_v2",
    "validate_trip_v2",
    "RouteRequest",
    "RouteResponse",
    "BudgetRequest",
    "BudgetResponse",
    "SaveMutation",
    "SaveRequest",
    "SaveResponse",
    "TripResponse",
    "ExportRequest",
    "ExportResponse",
]
