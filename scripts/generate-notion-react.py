#!/usr/bin/env python3
"""
Notion-style React Travel Plan Generator
Converts skeleton.json + agent outputs → standalone React HTML application
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


class NotionReactGenerator:
    """Generate Notion-style React travel plan from skeleton and agent data"""

    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data" / plan_id

        # Load all data
        self.skeleton = self._load_json("plan-skeleton.json")
        self.attractions = self._load_json("attractions.json")
        self.meals = self._load_json("meals.json")
        self.accommodation = self._load_json("accommodation.json")
        self.entertainment = self._load_json("entertainment.json")
        self.transportation = self._load_json("transportation.json")
        self.timeline = self._load_json("timeline.json")
        self.budget = self._load_json("budget.json")

    def _load_json(self, filename: str) -> dict:
        """Load JSON file from data directory"""
        path = self.data_dir / filename
        if not path.exists():
            print(f"Warning: {filename} not found, using empty dict")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Agent files have structure: { agent, status, data: {...} }
            # Extract actual data from 'data' field if it exists
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
                return data['data']

            return data

    def _get_cover_image(self, location: str, index: int = 0) -> str:
        """Get cover image URL for location"""
        # Map of cities to cover images (fallback to generic travel images)
        covers = {
            "harbin": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=1200&h=400&fit=crop",
            "beijing": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=1200&h=400&fit=crop",
            "shanghai": "https://images.unsplash.com/photo-1537887534808-c02b98e72156?w=1200&h=400&fit=crop",
            "chengdu": "https://images.unsplash.com/photo-1590735213920-68192a487bc2?w=1200&h=400&fit=crop",
            "xi'an": "https://images.unsplash.com/photo-1583259916581-e2cc0d0e0d66?w=1200&h=400&fit=crop",
        }
        key = location.lower()
        for city in covers:
            if city in key:
                return covers[city]

        # Generic fallbacks
        fallbacks = [
            "https://images.unsplash.com/photo-1609766856923-7e0a23024e9c?w=1200&h=400&fit=crop",
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=400&fit=crop",
            "https://images.unsplash.com/photo-1470004914212-05527e49370b?w=1200&h=400&fit=crop",
        ]
        return fallbacks[index % len(fallbacks)]

    def _get_placeholder_image(self, category: str) -> str:
        """Get placeholder image for different categories"""
        placeholders = {
            "meal": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=300&h=200&fit=crop",
            "attraction": "https://images.unsplash.com/photo-1548013146-72479768bada?w=400&h=300&fit=crop",
            "accommodation": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=300&fit=crop",
            "entertainment": "https://images.unsplash.com/photo-1499364615650-ec38552f4f34?w=400&h=300&fit=crop",
        }
        return placeholders.get(category, placeholders["attraction"])

    def _merge_day_data(self, day_skeleton: dict) -> dict:
        """Merge skeleton day with agent data"""
        day_num = day_skeleton.get("day", 1)
        date = day_skeleton.get("date", "")
        location = day_skeleton.get("location", "Unknown")

        merged = {
            "day": day_num,
            "date": date,
            "location": location,
            "cover": self._get_cover_image(location, day_num),
            "user_plans": day_skeleton.get("user_plans", []),
            "meals": {},
            "attractions": [],
            "entertainment": [],
            "accommodation": None,
            "budget": {
                "meals": 0,
                "attractions": 0,
                "entertainment": 0,
                "accommodation": 0,
                "total": 0
            }
        }

        # Merge meals
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if self.meals and "days" in self.meals:
                day_meals = next((d for d in self.meals["days"] if d.get("day") == day_num), {})
                if meal_type in day_meals:
                    meal = day_meals[meal_type]
                    merged["meals"][meal_type] = {
                        "name": meal.get("name", ""),
                        "name_en": meal.get("name_en", ""),
                        "cost": meal.get("cost", 0),
                        "cuisine": meal.get("cuisine", ""),
                        "signature_dishes": meal.get("signature_dishes", ""),
                        "image": meal.get("image", self._get_placeholder_image("meal")),
                        "time": meal.get("time", {"start": "08:00", "end": "09:00"}),
                        "links": meal.get("links", {})
                    }
                    merged["budget"]["meals"] += meal.get("cost", 0)

        # Merge attractions
        if self.attractions and "days" in self.attractions:
            day_attrs = next((d for d in self.attractions["days"] if d.get("day") == day_num), {})
            if "attractions" in day_attrs:
                for attr in day_attrs["attractions"]:
                    merged["attractions"].append({
                        "name": attr.get("name", ""),
                        "name_en": attr.get("name_en", ""),
                        "location": attr.get("location", ""),
                        "type": attr.get("type", ""),
                        "cost": attr.get("cost", 0),
                        "cost_eur": attr.get("cost_eur", 0),
                        "opening_hours": attr.get("opening_hours", ""),
                        "recommended_duration": attr.get("recommended_duration", ""),
                        "image": attr.get("image", self._get_placeholder_image("attraction")),
                        "highlights": attr.get("highlights", []),
                        "time": attr.get("time", {"start": "09:00", "end": "11:00"}),
                        "links": attr.get("links", {})
                    })
                    merged["budget"]["attractions"] += attr.get("cost", 0)

        # Merge entertainment
        if self.entertainment and "days" in self.entertainment:
            day_ent = next((d for d in self.entertainment["days"] if d.get("day") == day_num), {})
            if "entertainment" in day_ent:
                for ent in day_ent["entertainment"]:
                    merged["entertainment"].append({
                        "name": ent.get("name", ""),
                        "name_en": ent.get("name_en", ""),
                        "type": ent.get("type", ""),
                        "cost": ent.get("cost", 0),
                        "duration": ent.get("duration", ""),
                        "note": ent.get("note", ""),
                        "time": ent.get("time", {"start": "19:00", "end": "21:00"}),
                        "links": ent.get("links", {})
                    })
                    merged["budget"]["entertainment"] += ent.get("cost", 0)

        # Merge accommodation
        if self.accommodation and "days" in self.accommodation:
            day_acc = next((d for d in self.accommodation["days"] if d.get("day") == day_num), {})
            if "accommodation" in day_acc:
                acc = day_acc["accommodation"]
                merged["accommodation"] = {
                    "name": acc.get("name", ""),
                    "name_cn": acc.get("name_cn", ""),
                    "type": acc.get("type", "hotel"),
                    "location": acc.get("location", ""),
                    "cost": acc.get("cost", 0),
                    "stars": acc.get("stars", 3),
                    "time": acc.get("time", {"start": "15:00", "end": "16:00"}),
                    "links": acc.get("links", {})
                }
                merged["budget"]["accommodation"] = acc.get("cost", 0)

        # Calculate total budget
        merged["budget"]["total"] = sum([
            merged["budget"]["meals"],
            merged["budget"]["attractions"],
            merged["budget"]["entertainment"],
            merged["budget"]["accommodation"]
        ])

        return merged

    def _group_days_by_location(self, days: list) -> list:
        """Group days by location to create trips"""
        if not days:
            return []

        trips = []
        current_trip = None

        for day in days:
            location = day.get("location", "Unknown")

            if current_trip is None or current_trip["name"] != location:
                # Start new trip
                current_trip = {
                    "name": location,
                    "days_label": "1 day",
                    "cover": day.get("cover", ""),
                    "days": [day]
                }
                trips.append(current_trip)
            else:
                # Continue current trip
                current_trip["days"].append(day)
                current_trip["days_label"] = f"{len(current_trip['days'])} days"

        return trips

    def generate_plan_data(self) -> dict:
        """Generate complete PLAN_DATA structure"""

        # Build trip summary from skeleton's trip_summary section
        skel_summary = self.skeleton.get("trip_summary", {})
        prefs = skel_summary.get("preferences", {})
        if isinstance(prefs, dict):
            # Convert dict preferences to string
            prefs_str = ", ".join([f"{k}: {v}" for k, v in prefs.items()])
        else:
            prefs_str = str(prefs)

        trip_summary = {
            "trip_type": skel_summary.get("trip_type", "itinerary"),
            "description": skel_summary.get("description", "Travel Plan"),
            "base_location": skel_summary.get("base_location", ""),
            "period": skel_summary.get("period", ""),
            "travelers": skel_summary.get("travelers", "1 adult"),
            "budget_per_trip": skel_summary.get("budget_per_trip", "€500"),
            "preferences": prefs_str
        }

        # Merge all days
        merged_days = []
        if "days" in self.skeleton:
            for day_skel in self.skeleton["days"]:
                merged_day = self._merge_day_data(day_skel)
                merged_days.append(merged_day)

        # Group days into trips
        trips = self._group_days_by_location(merged_days)

        return {
            "trip_summary": trip_summary,
            "trips": trips
        }

    def generate_html(self) -> str:
        """Generate complete HTML with embedded React app"""

        plan_data = self.generate_plan_data()
        plan_data_json = json.dumps(plan_data, ensure_ascii=False, indent=2)

        # Read React component template
        react_template = self._read_react_template()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{plan_data['trip_summary']['description']}</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      overflow-x: hidden;
    }}
  </style>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel">
    // Embedded PLAN_DATA
    const PLAN_DATA = {plan_data_json};

    {react_template}

    // Render app
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<NotionTravelApp />);
  </script>
</body>
</html>"""

        return html

    def _read_react_template(self) -> str:
        """Read React component template"""
        # Return the React component code directly
        return """
// ============================================================
// HOOKS
// ============================================================
const { useState, useEffect, useCallback } = React;

const useBreakpoint = () => {
  const [bp, setBp] = useState(() => {
    const w = window.innerWidth;
    return w < 640 ? 'sm' : w < 960 ? 'md' : 'lg';
  });
  useEffect(() => {
    const h = () => { const w = window.innerWidth; setBp(w < 640 ? 'sm' : w < 960 ? 'md' : 'lg'); };
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);
  return bp;
};

// ============================================================
// ATOMS
// ============================================================
const LinkChip = ({ href, type, compact }) => {
  if (!href) return null;
  const cfg = {
    google_maps: { icon: '🌍', label: 'Google Maps', bg: '#edf2fc', color: '#2b63b5' },
    gaode: { icon: '🗺️', label: '高德', bg: '#e9f5ec', color: '#1a7a32' },
    xiaohongshu: { icon: '📕', label: '小红书', bg: '#fce8e6', color: '#c5221f' },
    booking: { icon: '🏨', label: 'Booking', bg: '#e8eaf6', color: '#1a237e' },
    dianping: { icon: '⭐', label: '点评', bg: '#fff3e0', color: '#e65100' }
  }[type] || { icon: '🔗', label: 'Link', bg: '#f5f5f5', color: '#666' };
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" style={{
      display: 'inline-flex', alignItems: 'center', gap: '3px',
      padding: compact ? '2px 5px' : '2px 8px',
      background: cfg.bg, color: cfg.color,
      borderRadius: '3px', fontSize: compact ? '10px' : '11px',
      fontWeight: '500', textDecoration: 'none', transition: 'opacity .12s'
    }}
      onMouseEnter={e => e.currentTarget.style.opacity = '0.7'}
      onMouseLeave={e => e.currentTarget.style.opacity = '1'}
    >{cfg.icon}{compact ? '' : ` ${cfg.label}`}</a>
  );
};

const LinksRow = ({ links, compact }) => {
  if (!links || !Object.keys(links).length) return null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
      {Object.entries(links).map(([t, u]) => <LinkChip key={t} href={u} type={t} compact={compact} />)}
    </div>
  );
};

const PropertyRow = ({ label, children }) => (
  <div style={{ display: 'flex', alignItems: 'baseline', padding: '5px 0', fontSize: '14px', lineHeight: '1.6' }}>
    <span style={{ width: '130px', flexShrink: 0, color: '#9b9a97', fontSize: '13px' }}>{label}</span>
    <span style={{ color: '#37352f' }}>{children}</span>
  </div>
);

const Section = ({ title, icon, children }) => (
  <div style={{ marginBottom: '32px' }}>
    <div style={{
      display: 'flex', alignItems: 'center', gap: '8px',
      fontSize: '15px', fontWeight: '600', color: '#37352f',
      paddingBottom: '6px', marginBottom: '14px',
      borderBottom: '1px solid #edece9'
    }}>
      <span style={{ fontSize: '16px' }}>{icon}</span> {title}
    </div>
    {children}
  </div>
);

const Donut = ({ budget, size = 80 }) => {
  const items = [
    { v: budget.meals || 0, c: '#f0b429' },
    { v: budget.attractions || 0, c: '#4a90d9' },
    { v: budget.entertainment || 0, c: '#9b6dd7' },
    { v: budget.accommodation || 0, c: '#45b26b' }
  ].filter(i => i.v > 0);
  const t = items.reduce((s, i) => s + i.v, 0);
  if (t === 0) return null;
  let cum = 0;
  const p = (r, a) => ({ x: 50 + r * Math.cos((a - 90) * Math.PI / 180), y: 50 + r * Math.sin((a - 90) * Math.PI / 180) });
  const arc = (sa, ea) => { const s = p(44, ea), e = p(44, sa); return `M${s.x},${s.y}A44,44,0,${ea - sa > 180 ? 1 : 0},0,${e.x},${e.y}L50,50Z`; };
  return (
    <svg viewBox="0 0 100 100" style={{ width: size, height: size }}>
      {items.map((it, i) => { const a = (it.v / t) * 360; const d = arc(cum, cum + a); cum += a; return <path key={i} d={d} fill={it.c} />; })}
      <circle cx="50" cy="50" r="24" fill="white" />
    </svg>
  );
};

const PropLine = ({ label, value }) => (
  <div style={{ fontSize: '12px', lineHeight: 1.7 }}>
    <span style={{ color: '#9b9a97' }}>{label}</span>{' '}
    <span style={{ color: '#37352f' }}>{value}</span>
  </div>
);

// ============================================================
// SIDEBAR
// ============================================================
const Sidebar = ({ trips, selTrip, selDay, onSelect, isOpen, onClose, bp }) => {
  const [exp, setExp] = useState({ [trips[0]?.name]: true });
  const mobile = bp === 'sm';
  const W = bp === 'lg' ? 240 : 220;

  return (
    <>
      {mobile && isOpen && <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 199 }} />}
      <div style={{
        width: W, flexShrink: 0, background: '#fbfbfa', borderRight: '1px solid #f0efed',
        padding: '14px 8px', overflowY: 'auto', height: '100vh',
        position: mobile ? 'fixed' : 'sticky', top: 0, left: 0, zIndex: 200,
        transform: mobile && !isOpen ? `translateX(-${W + 10}px)` : 'none',
        transition: 'transform .25s ease',
        boxShadow: mobile && isOpen ? '2px 0 8px rgba(0,0,0,0.06)' : 'none'
      }}>
        <div style={{ padding: '4px 10px 12px', fontSize: '12px', fontWeight: '600', color: '#37352f', display: 'flex', alignItems: 'center', gap: '6px', lineHeight: '1.45' }}>
          <span>📋</span>
          <span style={{ flex: 1 }}>{PLAN_DATA.trip_summary.description}</span>
          {mobile && <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b4b4b4', fontSize: '14px' }}>✕</button>}
        </div>

        {trips.map((trip, ti) => {
          const open = exp[trip.name] !== false;
          const has = trip.days.length > 0;
          return (
            <div key={trip.name}>
              <div
                onClick={() => { setExp(p => ({ ...p, [trip.name]: !p[trip.name] })); if (has) onSelect(ti, 0); if (mobile) onClose(); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '4px',
                  padding: '5px 10px', borderRadius: '5px', cursor: 'pointer',
                  fontSize: '13px', color: '#37352f',
                  background: selTrip === ti ? 'rgba(55,53,47,0.06)' : 'transparent',
                  borderLeft: selTrip === ti ? '2px solid #37352f' : '2px solid transparent',
                  transition: 'all .1s'
                }}
                onMouseEnter={e => { if (selTrip !== ti) e.currentTarget.style.background = 'rgba(55,53,47,0.03)'; }}
                onMouseLeave={e => { if (selTrip !== ti) e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ fontSize: '9px', color: '#b4b4b4', transform: open ? 'rotate(90deg)' : '', transition: 'transform .15s', display: 'inline-block', marginRight: '2px' }}>▶</span>
                <span style={{ fontWeight: '500', flex: 1 }}>{trip.name}</span>
                <span style={{ fontSize: '11px', color: '#b4b4b4' }}>({trip.days_label})</span>
              </div>
              {open && has && (
                <div style={{ marginLeft: '16px' }}>
                  {trip.days.map((d, di) => {
                    const active = selTrip === ti && selDay === di;
                    return (
                      <div key={di}
                        onClick={() => { onSelect(ti, di); if (mobile) onClose(); }}
                        style={{
                          padding: '4px 10px', borderRadius: '5px', cursor: 'pointer',
                          fontSize: '13px', color: '#37352f',
                          background: active ? 'rgba(55,53,47,0.06)' : 'transparent',
                          fontWeight: active ? '500' : '400',
                          borderLeft: active ? '2px solid #37352f' : '2px solid transparent',
                          transition: 'all .1s'
                        }}
                        onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'rgba(55,53,47,0.03)'; }}
                        onMouseLeave={e => { if (!active) e.currentTarget.style.background = active ? 'rgba(55,53,47,0.06)' : 'transparent'; }}
                      >📄 Day {d.day}</div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
};

// ============================================================
// KANBAN VIEW
// ============================================================
const KanbanView = ({ day, tripSummary, showSummary, bp }) => {
  const sm = bp === 'sm';
  const px = sm ? '16px' : bp === 'md' ? '32px' : '48px';

  return (
    <div style={{ maxWidth: '960px' }}>
      <div style={{
        width: '100%',
        height: sm ? '120px' : '200px',
        background: `linear-gradient(to bottom, rgba(0,0,0,0) 50%, rgba(0,0,0,0.03) 100%), url(${day.cover || 'https://images.unsplash.com/photo-1609766856923-7e0a23024e9c?w=1200&h=400&fit=crop'})`,
        backgroundSize: 'cover', backgroundPosition: 'center'
      }} />

      <div style={{ padding: `0 ${px}` }}>
        <div style={{ marginTop: sm ? '-24px' : '-36px', marginBottom: '24px' }}>
          <div style={{ fontSize: sm ? '40px' : '56px', lineHeight: 1, marginBottom: '8px' }}>🗺️</div>

          {showSummary ? (
            <>
              <h1 style={{ fontSize: sm ? '24px' : '36px', fontWeight: '700', color: '#37352f', margin: '0 0 20px', lineHeight: 1.25 }}>
                {tripSummary.description}
              </h1>
              <div style={{
                padding: sm ? '12px' : '16px 20px',
                background: '#fbfbfa', borderRadius: '8px',
                border: '1px solid #f0efed', marginBottom: '32px'
              }}>
                <PropertyRow label="Trip Type">{tripSummary.trip_type}</PropertyRow>
                <PropertyRow label="Base Location">{tripSummary.base_location}</PropertyRow>
                <PropertyRow label="Period">{tripSummary.period}</PropertyRow>
                <PropertyRow label="Travelers">{tripSummary.travelers}</PropertyRow>
                <PropertyRow label="Budget / Trip">{tripSummary.budget_per_trip}</PropertyRow>
                <PropertyRow label="Preferences">{tripSummary.preferences}</PropertyRow>
              </div>
            </>
          ) : (
            <h1 style={{ fontSize: sm ? '24px' : '36px', fontWeight: '700', color: '#37352f', margin: '0 0 24px', lineHeight: 1.25 }}>
              Day {day.day} – {day.location}
            </h1>
          )}

          {showSummary && (
            <h2 style={{ fontSize: sm ? '20px' : '26px', fontWeight: '700', color: '#37352f', margin: '0 0 28px' }}>
              Day {day.day} – {day.location}
            </h2>
          )}
        </div>

        {/* User Plans */}
        {day.user_plans && day.user_plans.length > 0 && (
          <Section title="User Plans" icon="📝">
            <div style={{
              padding: '14px 18px', background: '#fafafa', borderRadius: '6px',
              border: '1px solid #f0efed'
            }}>
              <ul style={{ margin: 0, padding: '0 0 0 18px', fontSize: '14px', lineHeight: 2, color: '#37352f' }}>
                {day.user_plans.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          </Section>
        )}

        {/* Meals */}
        <Section title="Meals" icon="🍽️">
          <div style={{ display: 'grid', gridTemplateColumns: sm ? '1fr' : 'repeat(3, 1fr)', gap: '14px' }}>
            {['breakfast', 'lunch', 'dinner'].map(type => {
              const meal = day.meals[type];
              if (!meal) return null;
              const lb = { breakfast: '🌅 Breakfast', lunch: '☀️ Lunch', dinner: '🌙 Dinner' }[type];
              return (
                <div key={type} style={{
                  background: '#fff', borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                  overflow: 'hidden', transition: 'box-shadow .15s'
                }}
                  onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04)'}
                  onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'}
                >
                  <div style={{ width: '100%', height: sm ? '100px' : '130px', overflow: 'hidden', background: '#f5f3ef' }}>
                    <img src={meal.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={e => { e.target.style.display = 'none'; }} />
                  </div>
                  <div style={{ padding: '12px 14px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '6px' }}>
                      {lb}: {meal.name}
                    </div>
                    {meal.name_en && <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{meal.name_en}</div>}
                    <div style={{ fontSize: '12px', color: '#6b6b6b', lineHeight: 1.7 }}>
                      <div><span style={{ color: '#9b9a97' }}>Cost</span> {meal.cost === 0 ? 'Free' : `${meal.cost} CNY`}</div>
                      {meal.cuisine && <div><span style={{ color: '#9b9a97' }}>Cuisine</span> {meal.cuisine}</div>}
                      {meal.signature_dishes && !sm && <div><span style={{ color: '#9b9a97' }}>Signature</span> {meal.signature_dishes}</div>}
                    </div>
                    <LinksRow links={meal.links} compact={sm} />
                  </div>
                </div>
              );
            })}
          </div>
        </Section>

        {/* Attractions + Right column */}
        <div style={{ display: 'grid', gridTemplateColumns: sm ? '1fr' : '1fr 1fr', gap: '24px' }}>
          {/* Attractions */}
          <Section title="Attractions" icon="📍">
            {day.attractions.map((attr, i) => (
              <div key={i} style={{
                background: '#fff', borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                overflow: 'hidden', marginBottom: '14px', transition: 'box-shadow .15s'
              }}
                onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'}
              >
                {sm ? (
                  <>
                    <div style={{ height: '110px', overflow: 'hidden', background: '#eef4f9' }}>
                      <img src={attr.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                    <div style={{ padding: '12px 14px' }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '4px' }}>{attr.name}</div>
                      {attr.name_en && <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{attr.name_en}</div>}
                      <PropLine label="Cost" value={attr.cost === 0 ? 'Free' : `${attr.cost} CNY${attr.cost_eur ? ` (€${attr.cost_eur})` : ''}`} />
                      <PropLine label="Hours" value={attr.opening_hours} />
                      <PropLine label="Duration" value={attr.recommended_duration} />
                      <LinksRow links={attr.links} compact />
                    </div>
                  </>
                ) : (
                  <div style={{ display: 'flex' }}>
                    <div style={{ width: '140px', flexShrink: 0, overflow: 'hidden', background: '#eef4f9' }}>
                      <img src={attr.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', minHeight: '160px' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                    <div style={{ padding: '14px 16px', flex: 1, lineHeight: 1.7 }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '2px' }}>{attr.name}</div>
                      {attr.name_en && <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '8px' }}>{attr.name_en}</div>}
                      {attr.location && <PropLine label="Location" value={attr.location} />}
                      <PropLine label="Type" value={attr.type} />
                      <PropLine label="Cost" value={attr.cost === 0 ? 'Free' : `${attr.cost} CNY${attr.cost_eur ? ` (€${attr.cost_eur})` : ''}`} />
                      <PropLine label="Hours" value={attr.opening_hours} />
                      <PropLine label="Duration" value={attr.recommended_duration} />
                      {attr.highlights && attr.highlights.length > 0 && (
                        <div style={{ marginTop: '6px' }}>
                          <span style={{ fontSize: '12px', color: '#9b9a97' }}>Highlights</span>
                          <ul style={{ margin: '2px 0 0', paddingLeft: '16px', fontSize: '12px', color: '#37352f', lineHeight: 1.7 }}>
                            {attr.highlights.map((h, j) => <li key={j}>{h}</li>)}
                          </ul>
                        </div>
                      )}
                      <LinksRow links={attr.links} />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </Section>

          {/* Right column */}
          <div>
            {day.entertainment?.length > 0 && (
              <Section title="Entertainment" icon="🎭">
                {day.entertainment.map((ent, i) => (
                  <div key={i} style={{
                    background: '#fff', borderRadius: '8px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                    padding: '14px 16px', marginBottom: '10px'
                  }}>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>{ent.name}</div>
                    {ent.name_en && <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{ent.name_en}</div>}
                    <PropLine label="Type" value={ent.type} />
                    <PropLine label="Cost" value={`${ent.cost} CNY`} />
                    <PropLine label="Duration" value={ent.duration} />
                    {ent.note && (
                      <div style={{ marginTop: '8px', padding: '8px 12px', background: '#fffdf5', borderRadius: '5px', border: '1px solid #f5ecd7', fontSize: '12px', color: '#9a6700' }}>
                        💡 {ent.note}
                      </div>
                    )}
                    <LinksRow links={ent.links} compact={sm} />
                  </div>
                ))}
              </Section>
            )}

            {day.accommodation && (
              <Section title="Accommodation" icon="🏨">
                <div style={{
                  background: '#fff', borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                  padding: '14px 16px'
                }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '4px' }}>{day.accommodation.name}</div>
                  {day.accommodation.name_cn && <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '8px' }}>{day.accommodation.name_cn}</div>}
                  <PropLine label="Type" value={day.accommodation.type} />
                  <PropLine label="Stars" value={<span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(day.accommodation.stars)}</span>} />
                  <PropLine label="Location" value={day.accommodation.location} />
                  <PropLine label="Cost" value={`${day.accommodation.cost} CNY`} />
                  <LinksRow links={day.accommodation.links} compact={sm} />
                </div>
              </Section>
            )}

            <Section title="Budget" icon="💰">
              <div style={{
                background: '#fff', borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                padding: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: sm ? 'center' : 'center', gap: '20px', flexDirection: sm ? 'column' : 'row' }}>
                  <Donut budget={day.budget} size={sm ? 72 : 88} />
                  <div style={{ fontSize: '13px', color: '#6b6b6b', lineHeight: 2, flex: 1, width: '100%' }}>
                    {[
                      { k: 'meals', l: 'Meals', c: '#f0b429' },
                      { k: 'attractions', l: 'Attractions', c: '#4a90d9' },
                      { k: 'entertainment', l: 'Entertainment', c: '#9b6dd7' },
                      { k: 'accommodation', l: 'Accommodation', c: '#45b26b' }
                    ].filter(r => day.budget[r.k] > 0).map(r => (
                      <div key={r.k} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ width: '10px', height: '10px', borderRadius: '3px', background: r.c, flexShrink: 0 }} />
                        <span style={{ flex: 1 }}>{r.l}</span>
                        <span style={{ fontWeight: '600', color: '#37352f' }}>{day.budget[r.k]} CNY</span>
                      </div>
                    ))}
                    <div style={{ borderTop: '1px solid #edece9', marginTop: '8px', paddingTop: '8px', fontWeight: '700', color: '#37352f', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Total</span><span>{day.budget.total} CNY</span>
                    </div>
                  </div>
                </div>
              </div>
            </Section>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// TIMELINE VIEW
// ============================================================
const TimelineView = ({ day, bp }) => {
  const sm = bp === 'sm';
  const px = sm ? '16px' : bp === 'md' ? '32px' : '48px';
  const timeW = sm ? '48px' : '62px';

  const entries = [];
  const add = (item, type, label) => { if (item?.time) entries.push({ ...item, _type: type, _label: label }); };
  add(day.meals.breakfast, 'meal', 'Breakfast');
  add(day.meals.lunch, 'meal', 'Lunch');
  add(day.meals.dinner, 'meal', 'Dinner');
  day.attractions?.forEach(a => add(a, 'attraction', 'Attraction'));
  day.entertainment?.forEach(e => add(e, 'entertainment', 'Entertainment'));
  if (day.accommodation) add(day.accommodation, 'accommodation', 'Check-in');
  entries.sort((a, b) => a.time.start.localeCompare(b.time.start));

  const firstH = entries.length ? parseInt(entries[0].time.start) : 8;
  const lastH = entries.length ? Math.min(parseInt(entries[entries.length - 1].time.start) + 2, 24) : 20;
  const hours = []; for (let h = firstH; h <= lastH; h++) hours.push(h);

  const hH = sm ? 68 : 80;
  const typeStyle = {
    meal: { bg: '#fffdf5', border: '#ebd984', dot: '#f0b429' },
    attraction: { bg: '#f6fafd', border: '#a8cceb', dot: '#4a90d9' },
    entertainment: { bg: '#faf6fd', border: '#c9aee6', dot: '#9b6dd7' },
    accommodation: { bg: '#f5fbf6', border: '#a2d9b1', dot: '#45b26b' }
  };

  const top = (t) => { const [h, m] = t.split(':').map(Number); return (h - firstH) * hH + (m / 60) * hH; };
  const hgt = (s, e) => Math.max(top(e) - top(s), sm ? 56 : 64);

  // Debug: log entries count
  if (entries.length === 0) {
    console.warn('Timeline has no entries for day:', day.day, day.location);
  }

  return (
    <div style={{ maxWidth: '900px' }}>
      <div style={{
        width: '100%', height: sm ? '100px' : '160px',
        background: `url(${day.cover || 'https://images.unsplash.com/photo-1609766856923-7e0a23024e9c?w=1200&h=400&fit=crop'})`,
        backgroundSize: 'cover', backgroundPosition: 'center'
      }} />

      <div style={{ padding: `0 ${px}` }}>
        <div style={{ marginTop: sm ? '-20px' : '-30px', marginBottom: '24px' }}>
          <div style={{ fontSize: sm ? '36px' : '48px', lineHeight: 1, marginBottom: '6px' }}>📍</div>
          <h2 style={{ fontSize: sm ? '22px' : '28px', fontWeight: '700', color: '#37352f', margin: 0 }}>
            Day {day.day} – {day.location}
          </h2>
        </div>

        {entries.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9b9a97' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏰</div>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>No timeline data available</div>
            <div style={{ fontSize: '13px' }}>This day has no scheduled activities with time information</div>
          </div>
        ) : (
          <div style={{ display: 'flex', position: 'relative' }}>
          <div style={{ width: timeW, flexShrink: 0 }}>
            {hours.map(h => (
              <div key={h} style={{ height: hH, fontSize: '12px', color: '#c4c4c0', fontFamily: 'ui-monospace, monospace', paddingTop: '2px' }}>
                {String(h).padStart(2, '0')}:00
              </div>
            ))}
          </div>

          <div style={{ flex: 1, position: 'relative', borderLeft: '1px dashed #e5e4e1', minWidth: 0 }}>
            {hours.map(h => <div key={h} style={{ height: hH, borderBottom: '1px solid #f5f5f3' }} />)}

            {entries.map((entry, i) => {
              const st = typeStyle[entry._type] || typeStyle.attraction;
              const t = top(entry.time.start);
              const h = hgt(entry.time.start, entry.time.end);
              return (
                <div key={i} style={{
                  position: 'absolute', top: t, left: '10px', right: '10px',
                  minHeight: h - 4,
                  background: st.bg, borderLeft: `3px solid ${st.border}`,
                  borderRadius: '6px', padding: sm ? '8px 10px' : '10px 14px',
                  display: 'flex', gap: '10px', alignItems: 'flex-start',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                  zIndex: 2, overflow: 'hidden', transition: 'box-shadow .15s'
                }}
                  onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04)'}
                >
                  <div style={{
                    position: 'absolute', left: '-8px', top: '50%', transform: 'translateY(-50%)',
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: st.dot, border: '2px solid #fff'
                  }} />

                  {entry.image && !sm && (
                    <div style={{ width: '50px', height: '50px', borderRadius: '6px', overflow: 'hidden', flexShrink: 0 }}>
                      <img src={entry.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '11px', color: '#b4b4b4' }}>{entry.time.start} – {entry.time.end}</div>
                    <div style={{
                      fontSize: sm ? '12px' : '14px', fontWeight: '600', color: '#37352f',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
                    }}>
                      {entry._label}: {entry.name}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#9b9a97', flexWrap: 'wrap', marginTop: '2px' }}>
                      {entry.recommended_duration && <span>⏱ {entry.recommended_duration}</span>}
                      {entry.cost !== undefined && (
                        <span style={{
                          padding: '1px 6px', borderRadius: '3px', fontWeight: '600',
                          background: entry.cost === 0 ? '#e9f5ec' : '#f5f5f3',
                          color: entry.cost === 0 ? '#1a7a32' : '#37352f'
                        }}>
                          {entry.cost === 0 ? 'Free' : `¥${entry.cost}`}
                        </span>
                      )}
                      {entry.stars && <span style={{ color: '#e9b200' }}>{'★'.repeat(entry.stars)}</span>}
                    </div>
                    <LinksRow links={entry.links} compact={sm} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

// ============================================================
// APP
// ============================================================
function NotionTravelApp() {
  const [selTrip, setSelTrip] = useState(0);
  const [selDay, setSelDay] = useState(0);
  const [view, setView] = useState('kanban');
  const [sbOpen, setSbOpen] = useState(false);
  const bp = useBreakpoint();
  const sm = bp === 'sm';

  const trip = PLAN_DATA.trips[selTrip];
  const day = trip?.days?.[selDay];

  return (
    <div style={{
      display: 'flex',
      fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, 'Noto Sans SC', sans-serif",
      background: '#ffffff', minHeight: '100vh', color: '#37352f'
    }}>
      <Sidebar
        trips={PLAN_DATA.trips} selTrip={selTrip} selDay={selDay}
        onSelect={(ti, di) => { setSelTrip(ti); setSelDay(di); }}
        isOpen={sbOpen} onClose={() => setSbOpen(false)} bp={bp}
      />

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          borderBottom: '1px solid #f0efed',
          padding: `0 ${sm ? '12px' : '20px'}`,
          display: 'flex', alignItems: 'center',
          position: 'sticky', top: 0, background: 'rgba(255,255,255,0.97)',
          backdropFilter: 'blur(8px)', zIndex: 50, gap: '2px'
        }}>
          {sm && (
            <button onClick={() => setSbOpen(true)} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '17px', padding: '10px 6px 10px 2px', color: '#37352f'
            }}>☰</button>
          )}
          {['kanban', 'timeline'].map(m => (
            <button key={m} onClick={() => setView(m)} style={{
              padding: sm ? '10px 8px' : '11px 16px', background: 'none', border: 'none',
              borderBottom: view === m ? '2px solid #37352f' : '2px solid transparent',
              fontSize: '14px', fontWeight: view === m ? '600' : '400',
              color: view === m ? '#37352f' : '#b4b4b4',
              cursor: 'pointer', transition: 'all .12s', whiteSpace: 'nowrap'
            }}>
              {m === 'kanban' ? 'Kanban View' : 'Timeline View'}
            </button>
          ))}
        </div>

        {day ? (
          view === 'kanban'
            ? <KanbanView day={day} tripSummary={PLAN_DATA.trip_summary} showSummary={selDay === 0 && selTrip === 0} bp={bp} />
            : <TimelineView day={day} bp={bp} />
        ) : (
          <div style={{ padding: `60px ${sm ? '16px' : '48px'}`, color: '#c4c4c0' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>🗺️</div>
            <div style={{ fontWeight: '500', fontSize: '16px', color: '#9b9a97' }}>{trip?.name}</div>
            <div style={{ marginTop: '4px' }}>Itinerary coming soon...</div>
          </div>
        )}
      </div>
    </div>
  );
}
"""

    def generate(self) -> str:
        """Main generation method"""
        print(f"Generating Notion-style React HTML for plan: {self.plan_id}")
        print(f"Data directory: {self.data_dir}")

        # Generate HTML
        html = self.generate_html()

        # Write output
        output_file = self.base_dir / f"travel-plan-notion-{self.plan_id}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ Generated: {output_file}")
        print(f"   File size: {len(html) / 1024:.1f} KB")

        return str(output_file)


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-notion-react.py <plan-id>")
        print("Example: python generate-notion-react.py beijing-exchange-bucket-list-20260202-232405")
        sys.exit(1)

    plan_id = sys.argv[1]

    try:
        generator = NotionReactGenerator(plan_id)
        output_file = generator.generate()

        print("\n" + "="*60)
        print("✅ Notion React HTML generation complete!")
        print(f"📄 Output: {output_file}")
        print(f"🌐 Open in browser: file://{output_file}")
        print("="*60)

    except Exception as e:
        print(f"❌ Error generating Notion React HTML: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
