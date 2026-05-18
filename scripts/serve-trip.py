#!/usr/bin/env python3
"""scripts/serve-trip.py -- M4a local trip-editor backend.

Spec: spec-20260508-221237 §5.13 D + M2-contract.md §9.

Usage:
  python3 scripts/serve-trip.py [--host 127.0.0.1] [--port 8765] [--trip <id>]

Default bind is 127.0.0.1 (per Q3e local-only no-auth); --host accepts an
override but a 0.0.0.0 / external bind is gated behind --allow-external for
operator confirmation. The 5 API endpoints are:

  POST /api/route                   lazy intra-city gaode dispatch
  POST /api/budget/recompute        pure aggregation
  POST /api/save                    autosave + 409-soft concurrency
  GET  /api/trip/<trip_id>          full hydration
  POST /api/export/{pdf,ical}       M6 exporter subprocess

Static surfaces:
  GET /trip/<trip_id>               serves web/index.html (SPA-style URL)
  GET /web/<asset>                  serves web/{css,js,...} (M4b output)
  GET /                             redirects to /trip/<trip_id> if --trip set
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import threading
from collections import defaultdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Add scripts/ to path so we can import lib.* modules
_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from lib.server import (  # noqa: E402
    TripStore,
    handle_route,
    handle_budget,
    handle_save,
    handle_export,
    hydrate_trip,
)
from lib.trip_contract.errors import StateMachineError  # noqa: E402
from lib.render_html_builders import generate_editor_html  # noqa: E402

# ---------------------------------------------------------------------------
# Load InteractiveHTMLGenerator from hyphenated filename via importlib
# ---------------------------------------------------------------------------
_gen_spec = importlib.util.spec_from_file_location(
    "generate_html_interactive",
    Path(__file__).parent / "generate-html-interactive.py",
)
_gen_mod = importlib.util.module_from_spec(_gen_spec)
_gen_spec.loader.exec_module(_gen_mod)
InteractiveHTMLGenerator = _gen_mod.InteractiveHTMLGenerator

# ---------------------------------------------------------------------------
# Per-trip HTML cache (S1: in-memory, invalidated on save)
# ---------------------------------------------------------------------------
_html_cache: dict[str, str] = {}
_html_cache_locks: dict[str, threading.Lock] = {}
_html_cache_meta_lock = threading.Lock()


def _get_trip_lock(trip_id: str) -> threading.Lock:
    with _html_cache_meta_lock:
        if trip_id not in _html_cache_locks:
            _html_cache_locks[trip_id] = threading.Lock()
        return _html_cache_locks[trip_id]


def _generate_html_for_trip(trip_id: str) -> str:
    """Instantiate generator and render editor HTML for trip_id."""
    gen = InteractiveHTMLGenerator(trip_id)
    return generate_editor_html(gen, trip_id)


def _get_or_generate_html(trip_id: str) -> str:
    """Return cached editor HTML, generating it on first miss.

    The per-trip lock is held for the entire generate+write cycle to prevent
    a concurrent _invalidate_html_cache call from causing a stale-write race
    (Finding 9).
    """
    trip_lock = _get_trip_lock(trip_id)
    with trip_lock:
        if trip_id in _html_cache:
            return _html_cache[trip_id]
        html = _generate_html_for_trip(trip_id)
        _html_cache[trip_id] = html
        return html


def _invalidate_html_cache(trip_id: str) -> None:
    """Remove cached HTML for trip_id so the next request regenerates it."""
    trip_lock = _get_trip_lock(trip_id)
    with trip_lock:
        _html_cache.pop(trip_id, None)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _read_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def _send_json(
    handler: BaseHTTPRequestHandler, status: int, body: dict | list
) -> None:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(encoded)


def _send_file(
    handler: BaseHTTPRequestHandler, path: Path, content_type: str
) -> None:
    data = path.read_bytes()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _send_404(handler: BaseHTTPRequestHandler, message: str) -> None:
    _send_json(handler, HTTPStatus.NOT_FOUND, {"error": "not-found", "detail": message})


_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
}


def _content_type_for(path: Path) -> str:
    return _CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")


class TripServerHandler(BaseHTTPRequestHandler):
    """Per-connection handler.

    The TripStore + project_dir are bound on the class by the server factory.
    """

    store: TripStore
    project_dir: Path
    web_dir: Path

    # Quiet down BaseHTTPRequestHandler's noisy stderr access log
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(f"[serve-trip] {self.address_string()} {format % args}\n")

    # ---- routing -----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler convention)
        path = urlparse(self.path).path
        try:
            self._dispatch_get(path)
        except Exception as e:  # noqa: BLE001
            _send_json(
                self, HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal", "detail": str(e)},
            )

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            self._dispatch_post(path)
        except Exception as e:  # noqa: BLE001
            _send_json(
                self, HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal", "detail": str(e)},
            )

    # ---- dispatch ----------------------------------------------------------

    def _dispatch_get(self, path: str) -> None:
        if path.startswith("/api/trip/"):
            return self._handle_get_trip(path[len("/api/trip/"):])
        if path.startswith("/trip/"):
            trip_id = path[len("/trip/"):]
            return self._serve_trip_editor(trip_id)
        if path.startswith("/web/"):
            return self._serve_static(path[len("/web/"):])
        if path == "/" or path == "":
            return self._serve_index()
        _send_404(self, f"no route for GET {path}")

    def _dispatch_post(self, path: str) -> None:
        if path == "/api/route":
            return self._handle_post_route()
        if path == "/api/budget/recompute":
            return self._handle_post_budget()
        if path == "/api/save":
            return self._handle_post_save()
        if path.startswith("/api/export/"):
            return self._handle_post_export(path[len("/api/export/"):])
        _send_404(self, f"no route for POST {path}")

    # ---- GET handlers ------------------------------------------------------

    def _handle_get_trip(self, trip_id: str) -> None:
        try:
            payload = hydrate_trip(self.store, trip_id)
        except FileNotFoundError:
            _send_404(self, f"trip not found: {trip_id}")
            return
        except ValueError as e:
            _send_json(self, HTTPStatus.BAD_REQUEST, {"error": str(e)})
            return
        _send_json(self, HTTPStatus.OK, payload)

    def _serve_trip_editor(self, trip_id: str) -> None:
        """Serve the React-based editor HTML for /trip/<trip_id>.

        Uses in-memory cache (S1): generated once per trip per server session,
        invalidated when /api/save commits a change for that trip.
        """
        if not trip_id:
            _send_404(self, "trip_id missing from URL")
            return
        try:
            html = _get_or_generate_html(trip_id)
        except FileNotFoundError:
            _send_404(self, f"trip not found: {trip_id}")
            return
        except Exception as e:  # noqa: BLE001
            _send_json(
                self, HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "html_generation_failed", "detail": str(e)},
            )
            return
        encoded = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_index(self) -> None:
        index = self.web_dir / "index.html"
        if not index.exists():
            _send_404(self, "web/index.html not yet installed (M4b pending)")
            return
        _send_file(self, index, _content_type_for(index))

    def _serve_static(self, asset_rel: str) -> None:
        if ".." in asset_rel.split("/"):
            _send_404(self, "invalid asset path")
            return
        full = self.web_dir / asset_rel
        if not full.exists() or not full.is_file():
            _send_404(self, f"asset not found: {asset_rel}")
            return
        _send_file(self, full, _content_type_for(full))

    # ---- POST handlers -----------------------------------------------------

    def _handle_post_route(self) -> None:
        body = _read_body(self)
        resp = handle_route(self.store, body, self.project_dir)
        _send_json(self, HTTPStatus.OK, resp)

    def _handle_post_budget(self) -> None:
        body = _read_body(self)
        resp = handle_budget(self.store, body)
        _send_json(self, HTTPStatus.OK, resp)

    def _handle_post_save(self) -> None:
        body = _read_body(self)
        try:
            resp = handle_save(self.store, body)
        except StateMachineError as e:
            _send_json(self, HTTPStatus.CONFLICT, {"error": "state_machine", "detail": str(e)})
            return
        # Invalidate cached editor HTML so the next page load reflects the save
        trip_id = body.get("trip_id", "")
        if trip_id:
            _invalidate_html_cache(trip_id)
        _send_json(self, HTTPStatus.OK, resp)

    def _handle_post_export(self, kind: str) -> None:
        body = _read_body(self)
        resp = handle_export(self.store, kind, body, self.project_dir)
        _send_json(self, HTTPStatus.OK, resp)


def _build_handler_class(
    store: TripStore, project_dir: Path
) -> type[TripServerHandler]:
    web_dir = project_dir / "web"

    class _Bound(TripServerHandler):
        pass

    _Bound.store = store
    _Bound.project_dir = project_dir
    _Bound.web_dir = web_dir
    return _Bound


def _enforce_local_bind(host: str, allow_external: bool) -> None:
    """Enforce 127.0.0.1 default per Q3e local-only no-auth.

    If the user passes a non-loopback host without --allow-external, we exit
    with a hard error. This is the code-level enforcement required by AC #1.
    """
    if _is_loopback(host):
        return
    if not allow_external:
        sys.stderr.write(
            f"refusing to bind non-loopback host {host!r} without --allow-external; "
            "local-only no-auth per spec Q3e\n"
        )
        sys.exit(2)


def _is_loopback(host: str) -> bool:
    return host in ("127.0.0.1", "localhost", "::1")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="M4a local trip-editor backend")
    p.add_argument("--host", default=DEFAULT_HOST, help="bind host (default 127.0.0.1)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help="bind port (default 8765)")
    p.add_argument("--trip", default=None, help="trip_id to focus on (informational only)")
    p.add_argument("--data-root", default=None, help="override data/ root (testing)")
    p.add_argument(
        "--allow-external", action="store_true",
        help="permit non-loopback bind (default refused per Q3e)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    _enforce_local_bind(args.host, args.allow_external)
    project_dir = _PROJECT_DIR
    data_root = Path(args.data_root) if args.data_root else project_dir / "data"
    store = TripStore(data_root)
    handler_cls = _build_handler_class(store, project_dir)
    server = ThreadingHTTPServer((args.host, args.port), handler_cls)
    sys.stderr.write(
        f"[serve-trip] listening on http://{args.host}:{args.port}/ "
        f"(data_root={data_root})\n"
    )
    if args.trip:
        sys.stderr.write(
            f"[serve-trip] trip URL: http://{args.host}:{args.port}/trip/{args.trip}\n"
        )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("[serve-trip] shutdown\n")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
