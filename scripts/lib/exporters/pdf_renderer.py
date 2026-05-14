"""PDF renderer for M6 (spec-20260508-221237 §5.11 A).

A4 portrait, one day per page, CJK font embedded (WenQuanYi Zen Hei primary,
fc-match fallback, STSong-Light degraded). Trip-level TOC links each day.
Atomic write via common.atomic_write_bytes.

Codex Q1 guidance (consulted 2026-05-14): try TTC subfontIndex=0 first; fall
back through fc-match candidates; last-resort UnicodeCIDFont("STSong-Light").
"""

from __future__ import annotations

import io
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFError, TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .common import (
    Trip,
    arriving_from_prior_day,
    atomic_write_bytes,
    day_total_for_export,
    image_path_for_option,
    iter_day_slots,
    segments_for_day,
    selected_option,
)


_CJK_FONT_NAME = "CJK"
_CJK_REGISTERED = False
_CJK_BACKEND: Optional[str] = None  # "ttf:<path>" | "cid:STSong-Light"

_KNOWN_CJK_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]


def _attempt_register(path: Path, sub: Optional[int]) -> bool:
    global _CJK_BACKEND
    try:
        if sub is None:
            pdfmetrics.registerFont(TTFont(_CJK_FONT_NAME, str(path)))
        else:
            pdfmetrics.registerFont(
                TTFont(_CJK_FONT_NAME, str(path), subfontIndex=sub)
            )
        _CJK_BACKEND = f"ttf:{path}"
        return True
    except (TTFError, Exception):
        return False


def _try_register_ttf(path: str) -> bool:
    p = Path(path)
    if not p.is_file():
        return False
    suffix_lc = p.suffix.lower()
    candidates: list[Optional[int]]
    candidates = [None] if suffix_lc not in {".ttc", ".otc"} else [0, 1]
    for sub in candidates:
        if _attempt_register(p, sub):
            return True
    return False


def _fc_match_candidates() -> list[str]:
    if shutil.which("fc-match") is None:
        return []
    try:
        out = subprocess.check_output(
            ["fc-match", "-f", "%{file}\n", "sans-serif:lang=zh"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode("utf-8", errors="ignore").strip()
    except (subprocess.SubprocessError, OSError):
        return []
    return [line for line in out.splitlines() if line]


def _register_cid_fallback() -> str:
    global _CJK_BACKEND
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    _CJK_BACKEND = "cid:STSong-Light"
    return _CJK_BACKEND


def ensure_cjk_font() -> str:
    """Register CJK font for reportlab; return backend identifier."""
    global _CJK_REGISTERED
    if _CJK_REGISTERED and _CJK_BACKEND:
        return _CJK_BACKEND
    for path in _KNOWN_CJK_PATHS:
        if _try_register_ttf(path):
            _CJK_REGISTERED = True
            return _CJK_BACKEND or "ttf:unknown"
    for path in _fc_match_candidates():
        if _try_register_ttf(path):
            _CJK_REGISTERED = True
            return _CJK_BACKEND or "ttf:unknown"
    try:
        backend = _register_cid_fallback()
        _CJK_REGISTERED = True
        return backend
    except Exception as exc:
        raise RuntimeError(f"no CJK font available: {exc}") from exc


def _font_for_paragraph() -> str:
    backend = _CJK_BACKEND or ""
    if backend.startswith("cid:"):
        return "STSong-Light"
    return _CJK_FONT_NAME


def _style(name: str, parent, font: str, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, parent=parent, fontName=font, **kw)


def _make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    f = _font_for_paragraph()
    return {
        "title": _style("TripTitle", base["Title"], f,
                        fontSize=22, leading=28, spaceAfter=12),
        "h1": _style("DayHeader", base["Heading1"], f,
                     fontSize=18, leading=22, spaceAfter=10,
                     textColor=colors.HexColor("#222222")),
        "h2": _style("SlotHeader", base["Heading2"], f,
                     fontSize=13, leading=17, spaceBefore=8, spaceAfter=4,
                     textColor=colors.HexColor("#444444")),
        "body": _style("Body", base["BodyText"], f, fontSize=10, leading=14),
        "muted": _style("Muted", base["BodyText"], f,
                        fontSize=9, leading=12,
                        textColor=colors.HexColor("#888888")),
        "toc": _style("Toc", base["BodyText"], f,
                      fontSize=11, leading=16, leftIndent=8),
    }


def _format_cost(value) -> str:
    if value is None:
        return "cost: unknown"
    try:
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return "cost: unknown"


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def _placeholder_table(styles: dict) -> Table:
    cell = Paragraph("[image unavailable]", styles["muted"])
    tbl = Table([[cell]], colWidths=[40 * mm], rowHeights=[28 * mm])
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
    ]))
    return tbl


def _option_image(trip: Trip, option: dict, styles: dict):
    img_path = image_path_for_option(trip.trip_dir, option)
    if img_path is None:
        return _placeholder_table(styles)
    try:
        return Image(str(img_path), width=40 * mm, height=28 * mm)
    except Exception:
        return _placeholder_table(styles)


def _slot_label(slot_id: str) -> str:
    return slot_id.replace("_", " ").title()


def _opt_title_html(opt: dict) -> str:
    name = _xml_escape(str(opt.get("name") or opt.get("name_local") or "(unnamed)"))
    cost_str = _xml_escape(_format_cost(opt.get("cost")))
    title_html = f"<b>{name}</b>"
    name_local = opt.get("name_local")
    if name_local and name_local != opt.get("name"):
        title_html += (
            f" <font color='#666666'>"
            f"({_xml_escape(str(name_local))})</font>"
        )
    return title_html + f" — {cost_str}"


def _opt_meta_paragraphs(opt: dict, styles: dict) -> list:
    parts: list = []
    location = _xml_escape(str(opt.get("location_summary") or ""))
    why = _xml_escape(str(opt.get("why_fits_user") or ""))
    if location:
        parts.append(Paragraph(f"Location: {location}", styles["body"]))
    if why:
        parts.append(Paragraph(f"Why: {why}", styles["muted"]))
    return parts


def _opt_table(img_flow, meta_paragraphs: list) -> Table:
    tbl = Table([[img_flow, meta_paragraphs]], colWidths=[45 * mm, None])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tbl


def _render_skipped(slot: dict, styles: dict) -> list:
    reason = _xml_escape(str(slot.get("skipped_reason") or "skipped"))
    return [Paragraph(f"Skipped — {reason}", styles["muted"])]


def _render_slot(trip: Trip, slot_id: str, slot: dict, styles: dict) -> list:
    flow: list = [Paragraph(_xml_escape(_slot_label(slot_id)), styles["h2"])]
    if slot.get("skipped"):
        return flow + _render_skipped(slot, styles)
    opt = selected_option(slot)
    if opt is None:
        return flow + [Paragraph("No selection yet", styles["muted"])]
    img_flow = _option_image(trip, opt, styles)
    meta_paragraphs = [Paragraph(_opt_title_html(opt), styles["body"])]
    meta_paragraphs.extend(_opt_meta_paragraphs(opt, styles))
    flow.append(_opt_table(img_flow, meta_paragraphs))
    return flow


def _segment_line(seg: dict) -> str:
    from_city = _xml_escape(str(seg.get("from_city") or seg.get("from") or "?"))
    to_city = _xml_escape(str(seg.get("to_city") or seg.get("to") or "?"))
    mode = _xml_escape(str(seg.get("mode") or ""))
    depart = _xml_escape(str(seg.get("depart_ts") or ""))
    arrive = _xml_escape(str(seg.get("arrive_ts") or ""))
    cost = _xml_escape(_format_cost(seg.get("cost")))
    return (
        f"<b>{from_city} → {to_city}</b> ({mode}) — "
        f"depart {depart} → arrive {arrive} — cost {cost}"
    )


def _render_segments(segments: list[dict], styles: dict, header: str) -> list:
    if not segments:
        return []
    flow: list = [Paragraph(header, styles["h2"])]
    for seg in segments:
        flow.append(Paragraph(_segment_line(seg), styles["body"]))
        status = seg.get("status") or "ok"
        if status not in ("ok", "resolved"):
            flow.append(Paragraph(
                f"Route status: {_xml_escape(str(status))} — placeholder shown",
                styles["muted"],
            ))
    return flow


def _render_accommodation(trip: Trip, day: dict, styles: dict) -> list:
    accom = day.get("accommodation")
    if not accom:
        return []
    return _render_slot(trip, "accommodation", accom, styles)


def _toc_header(trip: Trip, styles: dict) -> list:
    meta = trip.meta
    title = meta.get("title") or trip.trip_id
    if meta.get("title_local"):
        title = f"{title} — {meta['title_local']}"
    return [
        Paragraph("Itinerary", styles["title"]),
        Paragraph(_xml_escape(str(title)), styles["h1"]),
        Paragraph(
            f"Trip ID: {_xml_escape(trip.trip_id)} | "
            f"Days: {len(trip.days)} | "
            f"Currency: {_xml_escape(str(meta.get('currency_local') or 'CNY'))}",
            styles["muted"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Contents", styles["h2"]),
    ]


def _toc(trip: Trip, styles: dict) -> list:
    flow: list = _toc_header(trip, styles)
    for i, day in enumerate(trip.days, start=1):
        date = day.get("date") or ""
        city = day.get("city_name") or day.get("city_id") or ""
        anchor = f"day{i}"
        flow.append(Paragraph(
            f"<a href='#{anchor}' color='blue'>"
            f"Day {i} — {_xml_escape(str(date))} "
            f"— {_xml_escape(str(city))}</a>",
            styles["toc"],
        ))
    flow.append(PageBreak())
    return flow


def _day_header(day_n: int, day: dict, styles: dict) -> Paragraph:
    date = _xml_escape(str(day.get("date") or ""))
    city = _xml_escape(str(day.get("city_name") or day.get("city_id") or ""))
    day_type = _xml_escape(str(day.get("day_type") or "normal"))
    return Paragraph(
        f"<a name='day{day_n}'/>Day {day_n} — {date} — {city} "
        f"<font size='10' color='#888888'>[{day_type}]</font>",
        styles["h1"],
    )


def _day_total_paragraph(day_n: int, total: float, unknown: int, styles: dict) -> Paragraph:
    line = f"<b>Day {day_n} total:</b> {total:.0f}"
    if unknown:
        line += (
            f" <font color='#aa6600'>"
            f"(+ {unknown} unknown cost item(s))</font>"
        )
    return Paragraph(line, styles["body"])


def _render_day(trip: Trip, day_index: int, day: dict, styles: dict) -> list:
    day_n = day_index + 1
    flow: list = [_day_header(day_n, day, styles)]
    flow.extend(_render_segments(
        arriving_from_prior_day(trip, day_n),
        styles, "Arriving from prior day",
    ))
    for slot_id, slot in iter_day_slots(day):
        flow.extend(_render_slot(trip, slot_id, slot, styles))
    flow.extend(_render_accommodation(trip, day, styles))
    own_segs = segments_for_day(trip, day_n)
    flow.extend(_render_segments(own_segs, styles, "Inter-city transit (this day)"))
    total, unknown = day_total_for_export(day, own_segs)
    flow.append(Spacer(1, 4 * mm))
    flow.append(_day_total_paragraph(day_n, total, unknown, styles))
    if day_index < len(trip.days) - 1:
        flow.append(PageBreak())
    return flow


def render_pdf_bytes(trip: Trip) -> bytes:
    """Render the trip as a PDF byte buffer (does NOT write to disk)."""
    ensure_cjk_font()
    styles = _make_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=str(trip.meta.get("title") or trip.trip_id),
    )
    story: list = []
    story.extend(_toc(trip, styles))
    for i, day in enumerate(trip.days):
        story.extend(_render_day(trip, i, day, styles))
    doc.build(story)
    return buf.getvalue()


def export_pdf(trip: Trip, output_path: Optional[Path] = None) -> Path:
    """Write the trip PDF to data/<trip>/exports/<trip>.pdf (atomic)."""
    if output_path is None:
        output_path = trip.trip_dir / "exports" / f"{trip.trip_id}.pdf"
    data = render_pdf_bytes(trip)
    atomic_write_bytes(output_path, data)
    return output_path
