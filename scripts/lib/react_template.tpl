// ============================================================
// HOOKS
// ============================================================
const { useState, useEffect, useCallback, useMemo } = React;

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

// Mobile detection helper (reused by RedNoteLink, MapLink, etc.)
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

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

const Donut = ({ budget, size = 80, onBudgetClick, day }) => {
  const items = [
    { v: budget.meals || 0, c: '#f0b429', k: 'meals' },
    { v: budget.attractions || 0, c: '#4a90d9', k: 'attractions' },
    { v: budget.entertainment || 0, c: '#9b6dd7', k: 'entertainment' },
    { v: budget.accommodation || 0, c: '#45b26b', k: 'accommodation' },
    { v: budget.shopping || 0, c: '#e07c5a', k: 'shopping' },
    { v: budget.cafe || 0, c: '#D4A574', k: 'cafe' },
    { v: budget.transportation || 0, c: '#0ea5e9', k: 'transportation' }
  ].filter(i => i.v > 0);
  const t = items.reduce((s, i) => s + i.v, 0);
  if (t === 0) return (
    <svg width={size} height={size} viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="15.915" fill="none" stroke="#e5e4e1" strokeWidth="2.5" />
      <text x="18" y="18" textAnchor="middle" dy=".35em" fontSize="6" fill="#9b9a97">{CURRENCY_SYMBOL}0</text>
    </svg>
  );
  let cum = 0;
  const p = (r, a) => ({ x: 50 + r * Math.cos((a - 90) * Math.PI / 180), y: 50 + r * Math.sin((a - 90) * Math.PI / 180) });
  const arc = (sa, ea) => { const s = p(44, ea), e = p(44, sa); return `M${s.x},${s.y}A44,44,0,${ea - sa > 180 ? 1 : 0},0,${e.x},${e.y}L50,50Z`; };
  return (
    <svg viewBox="0 0 100 100" style={{ width: size, height: size }}>
      {items.length === 1 ? (
        <circle cx="50" cy="50" r="44" fill={items[0].c} style={{ cursor: onBudgetClick ? 'pointer' : 'default' }} onClick={() => onBudgetClick && onBudgetClick(items[0].k, day)} />
      ) : (
        items.map((it, i) => { const a = (it.v / t) * 360; const d = arc(cum, cum + a); cum += a; return <path key={i} d={d} fill={it.c} style={{ cursor: onBudgetClick ? 'pointer' : 'default' }} onClick={() => onBudgetClick && onBudgetClick(it.k, day)} />; })
      )}
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
const Sidebar = ({ trips, selTrip, selDay, onSelect, isOpen, onClose, bp, lang }) => {
  const [exp, setExp] = useState({ [trips[0]?.name]: true });
  const mobile = bp === 'sm';
  const W = bp === 'lg' ? 240 : 220;

  return (
    <>
      {mobile && isOpen && <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 199 }} />}
      <div style={{
        width: W, flexShrink: 0, background: '#fbfbfa', borderRight: '1px solid #f0efed',
        padding: '14px 8px', overflowY: 'auto', height: mobile ? '100%' : '100vh',
        position: mobile ? 'fixed' : 'sticky', top: 0, left: 0, bottom: mobile ? 0 : 'auto', zIndex: 200,
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
                <span style={{ fontWeight: '500', flex: 1 }}>{(lang === 'local' && trip.name_local) ? trip.name_local : trip.name}</span>
                <span style={{ fontSize: '11px', color: '#b4b4b4' }}>({trip.days_count != null ? ((trip.days_count === 1 ? L('days_count_1', lang) : L('days_count', lang)).replace('{n}', trip.days_count)) : trip.days_label})</span>
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
                      >📄 {dayLabelSidebar(d, lang)}</div>
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
// ITEM DETAIL SIDEBAR
// ============================================================
const ItemDetailSidebar = ({ item, type, onClose, bp, lang, mapProvider }) => {
  if (!item) return null;
  const sm = bp === 'sm';
  const W = sm ? '85%' : '400px';

  return (
    <>
      <div onClick={onClose} style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 299
      }} />
      <div style={{
        position: 'fixed', right: 0, top: 0, bottom: 0,
        width: W, background: '#fff',
        boxShadow: '-2px 0 8px rgba(0,0,0,0.08)',
        overflowY: 'auto', zIndex: 300,
        animation: 'slideIn 0.25s ease',
        padding: '24px'
      }}>
        <style>{`@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ fontSize: '20px' }}>
            {{ meal: '🍽️', attraction: '📍', entertainment: '🎭', shopping: '🛍️', accommodation: '🏨', transportation: item.icon || '🚄' }[type] || '📄'}
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: '20px', color: '#b4b4b4', padding: '4px 8px'
          }}>✕</button>
        </div>

        {item.image && (
          <div style={{
            width: '100%', height: '200px', borderRadius: '8px',
            overflow: 'hidden', marginBottom: '20px', background: '#f5f3ef'
          }}>
            <img src={item.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              onError={e => e.target.style.display = 'none'} />
          </div>
        )}

        <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#37352f', margin: '0 0 4px' }}>
          {type === 'transportation' ? (<>
            {item.icon} {lang === 'local' && item.from_local ? item.from_local : item.from_base} → {lang === 'local' && item.to_local ? item.to_local : item.to_base}
          </>) : (<>
            {getDisplayName(item, lang)}
            <RedNoteLink name={item.name_local || item.name_base} />
          </>)}
        </h2>

        <div style={{ borderTop: '1px solid #f0efed', paddingTop: '16px' }}>
          {item.time && type !== 'transportation' && (
            <PropertyRow label={L('time', lang)}>
              {item.time.start} – {item.time.end}
            </PropertyRow>
          )}
          {/* Category-specific field ordering */}
          {type === 'accommodation' ? (<>
            {item.check_in && <PropertyRow label={L('checkin', lang)}>{item.check_in}</PropertyRow>}
            {item.check_out && <PropertyRow label={L('checkout', lang)}>{item.check_out}</PropertyRow>}
            {(item.cost !== undefined && (item.cost > 0 || item.cost_type_base === 'prepaid')) && <PropertyRow label={L('cost', lang)}>{fmtCost(item.cost, item.cost_type_base, lang)}</PropertyRow>}
            {getDisplayField(item, 'type', lang) && <PropertyRow label={L('type', lang)}>{getDisplayField(item, 'type', lang)}</PropertyRow>}
            {item.stars > 0 && <PropertyRow label={L('stars', lang)}><span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(item.stars)}</span></PropertyRow>}
            {(item.location_base || item.location_local) && <PropertyRow label={L('location', lang)}><MapLink item={item} lang={lang} mapProvider={mapProvider} /></PropertyRow>}
          </>) : type === 'transportation' ? (<>
            {item.time && <PropertyRow label={L('time', lang)}>{item.time.start} – {item.time.end}</PropertyRow>}
            {item.cost != null && (item.cost > 0 || item.cost_type_base === 'prepaid') && <PropertyRow label={L('cost', lang)}>{fmtCost(item.cost, item.cost_type_base, lang)}</PropertyRow>}
            <PropertyRow label={L('type', lang)}>{getDisplayField(item, 'type', lang)}</PropertyRow>
            {getDisplayField(item, 'company', lang) && <PropertyRow label={L('company', lang)}>{getDisplayField(item, 'company', lang)}</PropertyRow>}
            {item.route_number && <PropertyRow label={L('route_number', lang)}>{item.route_number}</PropertyRow>}
            {getDisplayField(item, 'status', lang) && (
              <PropertyRow label={L('status', lang)}>
                <span style={{
                  padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: '600',
                  background: item.status_base?.includes('URGENT') ? '#fff4e6' : item.status_base?.includes('VERIFIED') ? '#e9f5ec' : '#edf2fc',
                  color: item.status_base?.includes('URGENT') ? '#d97706' : item.status_base?.includes('VERIFIED') ? '#1a7a32' : '#2b63b5'
                }}>
                  {getDisplayField(item, 'status', lang)}
                </span>
              </PropertyRow>
            )}
            {item.departure_point_base && <PropertyRow label={L('route', lang)}>{lang === 'local' && item.departure_point_local ? item.departure_point_local : item.departure_point_base} → {lang === 'local' && item.arrival_point_local ? item.arrival_point_local : item.arrival_point_base}</PropertyRow>}
            {item.booking_required && (
              <div style={{ marginTop: '6px' }}>
                <span style={{ fontSize: '11px', padding: '2px 8px', background: '#fff3e0', border: '1px solid #ffcc80', borderRadius: '4px', color: '#e65100', fontWeight: '600' }}>
                  {L('booking_required', lang)}
                </span>
              </div>
            )}
          </>) : (<>
            {item.check_in && <PropertyRow label={L('checkin', lang)}>{item.check_in}</PropertyRow>}
            {item.check_out && <PropertyRow label={L('checkout', lang)}>{item.check_out}</PropertyRow>}
            {(item.cost !== undefined && (item.cost > 0 || item.cost_type_base === 'prepaid')) && <PropertyRow label={L('cost', lang)}>{fmtCost(item.cost, item.cost_type_base, lang)}</PropertyRow>}
            {getDisplayField(item, 'cuisine', lang) && <PropertyRow label={L('cuisine', lang)}>{getDisplayField(item, 'cuisine', lang)}</PropertyRow>}
            {getDisplayField(item, 'signature_dishes', lang) && <PropertyRow label={L('signature', lang)}>{getDisplayField(item, 'signature_dishes', lang)}</PropertyRow>}
            {getDisplayField(item, 'type', lang) && <PropertyRow label={L('type', lang)}>{getDisplayField(item, 'type', lang)}</PropertyRow>}
            {item.opening_hours && <PropertyRow label={L('opening_hours', lang)}>{item.opening_hours}</PropertyRow>}
            {(item.location_base || item.location_local) && <PropertyRow label={L('location', lang)}><MapLink item={item} lang={lang} mapProvider={mapProvider} /></PropertyRow>}
            {item.optional && <PropertyRow label={L('optional', lang)}><span style={{ padding: '2px 8px', background: '#f5f5f3', borderRadius: '4px', fontSize: '12px', color: '#9b9a97', fontWeight: '600' }}>{L('optional', lang)}</span></PropertyRow>}
            {item.stars > 0 && <PropertyRow label={L('stars', lang)}><span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(item.stars)}</span></PropertyRow>}
          </>)}
          {((lang === 'local' && item.amenities_local && item.amenities_local.length > 0) ? item.amenities_local : (item.amenities_base && item.amenities_base.length > 0 ? item.amenities_base : null)) && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>{L('amenities', lang)}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {(lang === 'local' && item.amenities_local && item.amenities_local.length > 0 ? item.amenities_local : item.amenities_base).map((a, i) => (
                  <span key={i} style={{ fontSize: '12px', padding: '3px 8px', background: '#f5f5f3', borderRadius: '4px', color: '#6b6b6b' }}>{a}</span>
                ))}
              </div>
            </div>
          )}
          {(lang === 'local' && item.note_local ? item.note_local : item.note_base) && (
            <div style={{
              marginTop: '16px', padding: '12px 16px',
              background: '#fffdf5', borderRadius: '6px',
              border: '1px solid #f5ecd7', fontSize: '13px', color: '#9a6700'
            }}>
              💡 {lang === 'local' && item.note_local ? item.note_local : item.note_base}
            </div>
          )}
          {(lang === 'local' && item.notes_local ? item.notes_local : item.notes_base) && (
            <div style={{
              marginTop: '16px', padding: '12px 16px',
              background: '#f5f9fc', borderRadius: '6px',
              border: '1px solid #d9e8f5', fontSize: '13px', color: '#37352f', lineHeight: 1.6
            }}>
              {lang === 'local' && item.notes_local ? item.notes_local : item.notes_base}
            </div>
          )}
          {item.links && Object.keys(item.links).length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>
                {L('links', lang)}
              </div>
              <LinksRow links={item.links} />
            </div>
          )}
        </div>
      </div>
    </>
  );
};

// ============================================================
// BUDGET DETAIL SIDEBAR
// ============================================================
const BudgetDetailSidebar = ({ category, items, total, onClose, bp, lang }) => {
  if (!category) return null;
  const sm = bp === 'sm';
  const W = sm ? '85%' : '400px';

  const categoryConfig = {
    meals: { icon: '🍽️', label: L('meals', lang), color: '#f0b429' },
    attractions: { icon: '📍', label: L('attractions', lang), color: '#4a90d9' },
    entertainment: { icon: '🎭', label: L('entertainment', lang), color: '#9b6dd7' },
    accommodation: { icon: '🏨', label: L('accommodation', lang), color: '#45b26b' },
    shopping: { icon: '🛍️', label: L('shopping', lang), color: '#e07c5a' },
    cafe: { icon: '\u2615', label: L('cafe', lang), color: '#D4A574' },
    transportation: { icon: '🚄', label: L('transport', lang), color: '#0ea5e9' }
  };
  const cfg = categoryConfig[category] || { icon: '💰', label: L('budget', lang), color: '#37352f' };

  return (
    <>
      <div onClick={onClose} style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 299
      }} />
      <div style={{
        position: 'fixed', right: 0, top: 0, bottom: 0,
        width: W, background: '#fff',
        boxShadow: '-2px 0 8px rgba(0,0,0,0.08)',
        overflowY: 'auto', zIndex: 300,
        animation: 'slideIn 0.25s ease',
        padding: '24px'
      }}>
        <style>{`@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ fontSize: '24px' }}>{cfg.icon}</div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#37352f', margin: 0 }}>
              {cfg.label}
            </h2>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: '20px', color: '#b4b4b4', padding: '4px 8px'
          }}>✕</button>
        </div>

        {items && items.length > 0 ? (
          <div>
            {items.map((item, i) => (
              <div key={i} style={{
                padding: '14px 16px',
                background: '#fbfbfa',
                borderRadius: '6px',
                border: '1px solid #f0efed',
                marginBottom: '10px'
              }}>
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '4px' }}>
                  {lang === 'local' && item.name_local ? item.name_local : (item.name_base || '')}
                </div>
                {lang !== 'local' && item.name_local && (
                  <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{item.name_local}</div>
                )}
                {lang === 'local' && item.name_base && item.name_base !== item.name_local && (
                  <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{item.name_base}</div>
                )}
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: '14px', marginTop: '8px'
                }}>
                  <span style={{ color: '#9b9a97' }}>{L('cost', lang)}</span>
                  <span style={{ fontWeight: '600', color: cfg.color }}>
                    {fmtCost(item.cost, undefined, lang)}
                  </span>
                </div>
              </div>
            ))}

            <div style={{
              marginTop: '20px', paddingTop: '16px',
              borderTop: '2px solid #edece9'
            }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                fontSize: '16px', fontWeight: '700', color: '#37352f'
              }}>
                <span>{L('total', lang)}</span>
                <span style={{ color: cfg.color }}>{CURRENCY_SYMBOL}{total.toFixed(0)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9b9a97' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>{cfg.icon}</div>
            <div style={{ fontSize: '14px' }}>{L('no_items', lang)}</div>
          </div>
        )}
      </div>
    </>
  );
};

// ============================================================
// KANBAN VIEW
// ============================================================
// Root cause fix (commit 8f2bddd): Helper to get display name based on language preference
const getDisplayName = (item, lang) => {
  if (!item) return '';
  if (lang === 'base') {
    return item.name_base || '';
  }
  return item.name_local || item.name_base || '';
};

// All costs are in display currency (from config). Use CURRENCY_SYMBOL.
const fmtCost = (c, costType, lng) => {
  if (costType === 'prepaid') return L('prepaid', lng);
  const n = Number(c);
  if (!n || n === 0) return L('free', lng);
  return Number.isInteger(n) ? `${CURRENCY_SYMBOL}${n}` : `${CURRENCY_SYMBOL}${n.toFixed(1)}`;
};

// Fix issues #4,7,12: Language-aware location display
const getDisplayLocation = (item, lang) => {
  if (!item) return '';
  if (lang === 'base') return item.location_base || '';
  return item.location_local || item.location_base || '';
};

// Bilingual field helper: returns local variant when lang='local' and data exists
const getDisplayField = (item, field, lang) => {
  if (!item) return '';
  if (lang === 'local' && item[field + '_local']) return item[field + '_local'];
  return item[field + '_base'] || '';
};

// Data-driven bilingual labels — reads from PLAN_DATA.trip_summary.ui_labels
const L = (key, lng) => {
  const labels = PLAN_DATA.trip_summary.ui_labels || {};
  if (lng === 'local' && labels.local && labels.local[key]) {
    return labels.local[key];
  }
  if (labels.base && labels.base[key]) {
    return labels.base[key];
  }
  return key; // ultimate fallback: the key itself
};

// Format a YYYY-MM-DD date string into localized display
// Base lang: "Feb 15 (Sat)", Local lang: "2月15日 (六)"
const formatRealDate = (dateStr, lng) => {
  const m = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const d = new Date(parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]));
  if (isNaN(d.getTime())) return null;
  const labels = PLAN_DATA.trip_summary.ui_labels || {};
  if (lng === 'local' && labels.local && labels.local.day_format) {
    // Local lang format: "2月15日 (六)"
    const localMonths = ['1','2','3','4','5','6','7','8','9','10','11','12'];
    const localDays = labels.local.weekdays_short || ['日','一','二','三','四','五','六'];
    return `${localMonths[d.getMonth()]}月${d.getDate()}日 (${localDays[d.getDay()]})`;
  }
  // Base lang format: "Feb 15 (Sat)"
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  return `${months[d.getMonth()]} ${d.getDate()} (${days[d.getDay()]})`;
};

// Day label helper — handles format differences between languages
// For itinerary trips with real dates (YYYY-MM-DD): "Feb 15 (Sat) – Chongqing"
// For bucket-list / no real date: "Day 3 – Chongqing"
// Accepts day object or (dayNum, location, lng) for backward compat
const dayLabel = (dayNumOrObj, locationOrLng, lngOpt) => {
  // Support both: dayLabel(day, lang) and dayLabel(dayNum, location, lng)
  let dayNum, date, location, lng;
  if (typeof dayNumOrObj === 'object' && dayNumOrObj !== null) {
    // Called as dayLabel(dayObj, lang)
    const day = dayNumOrObj;
    dayNum = day.day;
    date = day.date || '';
    lng = locationOrLng;
    location = (lng === 'local' && day.location_local) ? day.location_local : day.location_base;
  } else {
    // Legacy: dayLabel(dayNum, location, lng)
    dayNum = dayNumOrObj;
    date = '';
    location = locationOrLng;
    lng = lngOpt;
  }
  // If day has a real date (YYYY-MM-DD), use formatted date instead of "Day N"
  const realDate = date ? formatRealDate(date, lng) : null;
  let prefix;
  if (realDate) {
    prefix = realDate;
  } else {
    const labels = PLAN_DATA.trip_summary.ui_labels || {};
    const fmt = (lng === 'local' && labels.local && labels.local.day_format)
      || (labels.base && labels.base.day_format) || 'Day {n}';
    prefix = fmt.replace('{n}', dayNum);
  }
  return prefix + (location ? ' – ' + location : '');
};

// Day label for sidebar nav (shows date only, no city name)
// Accepts day object or dayNum for backward compat
const dayLabelSidebar = (dayNumOrObj, lng) => {
  let dayNum, date;
  if (typeof dayNumOrObj === 'object' && dayNumOrObj !== null) {
    const day = dayNumOrObj;
    dayNum = day.day;
    date = day.date || '';
  } else {
    dayNum = dayNumOrObj;
    date = '';
  }
  // Use real date if available
  const realDate = date ? formatRealDate(date, lng) : null;
  return realDate ? realDate : `Day ${dayNum}`;
};

// Day label for sidebar nav (no location) - deprecated in favor of dayLabelSidebar
// Accepts day object or dayNum for backward compat
const dayLabelShort = (dayNumOrObj, lng) => {
  let dayNum, date;
  if (typeof dayNumOrObj === 'object' && dayNumOrObj !== null) {
    dayNum = dayNumOrObj.day;
    date = dayNumOrObj.date || '';
  } else {
    dayNum = dayNumOrObj;
    date = '';
  }
  const realDate = date ? formatRealDate(date, lng) : null;
  if (realDate) return realDate;
  const labels = PLAN_DATA.trip_summary.ui_labels || {};
  const fmt = (lng === 'local' && labels.local && labels.local.day_format)
    || (labels.base && labels.base.day_format) || 'Day {n}';
  return fmt.replace('{n}', dayNum);
};

// Meal type emoji (kept separate from label text — emoji is decoration, not translation)
const mealEmoji = { breakfast: '🌅', lunch: '☀️', dinner: '🌙' };

// Google Maps logo (from Simple Icons)
const GoogleMapsLogo = ({ size = 14 }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} style={{ display: 'block', flexShrink: 0 }}>
    <path fill="#4285F4" d="M19.527 4.799c1.212 2.608.937 5.678-.405 8.173-1.101 2.047-2.744 3.74-4.098 5.614-.619.858-1.244 1.75-1.669 2.727-.141.325-.263.658-.383.992-.121.333-.224.673-.34 1.008-.109.314-.236.684-.627.687h-.007c-.466-.001-.579-.53-.695-.887-.284-.874-.581-1.713-1.019-2.525-.51-.944-1.145-1.817-1.79-2.671L19.527 4.799zM8.545 7.705l-3.959 4.707c.724 1.54 1.821 2.863 2.871 4.18.247.31.494.622.737.936l4.984-5.925-.029.01c-1.741.601-3.691-.291-4.392-1.987a3.377 3.377 0 0 1-.209-.716c-.063-.437-.077-.761-.004-1.198l.001-.007zM5.492 3.149l-.003.004c-1.947 2.466-2.281 5.88-1.117 8.77l4.785-5.689-.058-.05-3.607-3.035zM14.661.436l-3.838 4.563a.295.295 0 0 1 .027-.01c1.6-.551 3.403.15 4.22 1.626.176.319.323.683.377 1.045.068.446.085.773.012 1.22l-.003.016 3.836-4.561A8.382 8.382 0 0 0 14.67.439l-.009-.003zM9.466 5.868L14.162.285l-.047-.012A8.31 8.31 0 0 0 11.986 0a8.439 8.439 0 0 0-6.169 2.766l-.016.018 3.665 3.084z"/>
  </svg>
);

// Gaode Maps (高德地图/AMap) logo - blue location pin with "A" based on brand color #0085fe
const GaodeLogo = ({ size = 14 }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} style={{ display: 'block', flexShrink: 0 }}>
    <path fill="#0085fe" d="M12 0C7.31 0 3.5 3.81 3.5 8.5C3.5 14.88 12 24 12 24s8.5-9.12 8.5-15.5C20.5 3.81 16.69 0 12 0z"/>
    <text x="12" y="12" textAnchor="middle" fill="white" fontSize="10" fontWeight="bold" fontFamily="Arial,sans-serif" dy=".35em">A</text>
  </svg>
);

// Gaode Maps native app deeplink handler for mobile
// Tries native scheme directly, falls back to H5 after 1.5s timeout
const openGaodeNative = (gaodeScheme, gaodeH5) => {
  const start = Date.now();
  const onVisChange = () => {
    // If page became hidden within 3s of click, app probably opened
    if (document.hidden) {
      document.removeEventListener('visibilitychange', onVisChange);
      clearTimeout(fallbackTimer);
    }
  };
  document.addEventListener('visibilitychange', onVisChange);
  // Try native scheme directly
  window.location.href = gaodeScheme;
  // Fallback to H5 if app didn't open
  const fallbackTimer = setTimeout(() => {
    document.removeEventListener('visibilitychange', onVisChange);
    if (!document.hidden && Date.now() - start < 3000) {
      window.location.href = gaodeH5;
    }
  }, 1500);
};

// Map link component with provider toggle support (Google Maps / Gaode Maps)
const MapLink = ({ item, lang, mapProvider = 'gaode' }) => {
  const loc = getDisplayLocation(item, lang);
  if (!loc) return null;
  const coords = item.coordinates;
  let googleHref, gaodeH5, gaodeScheme;
  if (coords && (coords.latitude || coords.lat)) {
    const lat = coords.latitude || coords.lat;
    const lng = coords.longitude || coords.lng;
    googleHref = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
    gaodeH5 = `https://uri.amap.com/marker?position=${lng},${lat}&name=${encodeURIComponent(loc)}&callnative=0`;
    const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    gaodeScheme = isIOS
      ? `iosamap://viewMap?sourceApplication=travel&poiname=${encodeURIComponent(loc)}&lat=${lat}&lon=${lng}&dev=0`
      : `androidamap://viewMap?sourceApplication=travel&poiname=${encodeURIComponent(loc)}&lat=${lat}&lon=${lng}&dev=0`;
  } else {
    googleHref = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc)}`;
    gaodeH5 = `https://uri.amap.com/search?keyword=${encodeURIComponent(loc)}&callnative=0`;
    const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    gaodeScheme = isIOS
      ? `iosamap://poi?sourceApplication=travel&keywords=${encodeURIComponent(loc)}`
      : `androidamap://poi?sourceApplication=travel&keywords=${encodeURIComponent(loc)}`;
  }
  const isGaode = mapProvider === 'gaode';
  const Logo = isGaode ? GaodeLogo : GoogleMapsLogo;
  const title = isGaode ? 'Open in 高德地图' : 'Open in Google Maps';
  const color = isGaode ? '#0085fe' : '#4285F4';
  const handleClick = (e) => {
    e.stopPropagation();
    if (isGaode && isMobile) {
      e.preventDefault();
      openGaodeNative(gaodeScheme, gaodeH5);
    }
  };
  const href = isGaode ? gaodeH5 : googleHref;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
      <a href={href} target="_blank" rel="noopener noreferrer"
        style={{ color: color, textDecoration: 'none', borderBottom: `1px dashed ${color}` }}
        title={title}
        onClick={handleClick}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
          <Logo size={14} />
          {loc}
        </span>
      </a>
    </span>
  );
};

// Fix issue #8: RedNote (小红书) search link component with official logo
// Official SVG source: https://static.cdnlogo.com/logos/r/77/rednote-xiaohongshu.svg
const XhsLogo = ({ size = 14 }) => (
  <svg viewBox="0 0 377.97 376.53" width={size} height={size} style={{ display: 'block', flexShrink: 0 }}>
    <path fill="#ff2842" d="M43.86,1.11C21.81,5.7,3.59,22.91,1.34,46.07c-2.33,23.92,0,49.25,0,73.3v149.53c0,27.5-6.94,64.79,10.75,87.96,19.11,25.02,53.98,19.06,81.6,19.06h214.03c8.48,0,18.08,1.24,26.39-.49,22.05-4.59,40.26-21.8,42.51-44.96,2.33-23.92,0-49.25,0-73.3V107.64c0-27.5,6.94-64.79-10.75-87.96C346.76-5.34,311.89.62,284.27.62H70.24c-8.48,0-18.08-1.24-26.39.49M177.26,134.02l-10.26,27.85h17.59l-14.66,35.18,13.19,1.47c-1.45,3.93-3.4,11.34-6.35,14.42-2.17,2.26-5.48,1.71-8.31,1.71-6.39,0-19.3,2.65-22.72-4.4-1.57-3.23.68-7.31,1.95-10.26,2.66-6.17,6.19-12.48,7.57-19.06-3.19,0-7.22.63-10.26-.49-11.4-4.19,1.28-22.52,3.91-28.83,1.85-4.43,4.04-14.05,8.06-16.86,5.65-3.94,14.24-1.21,20.28-.73M61.45,226.38c4.03,0,10.02,1.2,12.46-2.93,2.59-4.39.73-14.06.73-19.06v-48.38c0-4.53-2.29-18.38,1.71-21.26,3.29-2.37,17.1-1.87,18.57,2.2,2.4,6.66.24,17.83.24,24.92v46.91c0,8.04,1.39,17.39-1.95,24.92-3.19,7.18-18.04,13.59-25.41,8.06-3.24-2.43-5.55-11.6-6.35-15.39M284.27,134.02v7.33c5.47,0,12.33-1.12,17.59.49,17.56,5.36,16.13,22.61,16.13,37.63,2.93,0,5.93-.23,8.8.49,16.85,4.21,14.66,21.06,14.66,34.69,0,7.27,1.36,15.86-3.42,21.99-5.27,6.75-13.9,5.86-21.5,5.86-2.36,0-6.25.75-8.31-.73-3.85-2.77-5.54-11-6.35-15.39,4.82,0,13.51,1.65,17.35-1.95,4.52-4.25,2.67-20.86-2.69-23.7-2.84-1.5-7.16-.73-10.26-.73h-21.99v42.51h-20.52v-42.51h-20.52v-20.52h20.52v-17.59h-13.19v-20.52h13.19v-7.33h20.52M237.36,141.35v20.52h-11.73v61.57h19.06v19.06h-67.43l7.82-18.32,18.57-.73v-61.57h-11.73v-20.52h45.44M320.92,161.88c0-4.17-.76-9.17.49-13.19,4.9-15.82,28.76-3.07,16.86,10.02-1.35,1.49-3.73,2.22-5.62,2.69-3.75.94-7.89.49-11.73.49M61.45,161.88l-6.11,54.24-10.02,17.59-8.8-23.46,4.4-48.38h20.52M128.88,161.88l4.4,48.38-8.8,21.99h-2.93c-7.87-12.46-8.87-25.31-10.26-39.58-.99-10.14-2.93-20.58-2.93-30.78h20.52M284.27,161.88v17.59h13.19v-17.59h-13.19M174.32,223.45l-7.33,19.06h-32.25l7.82-19.79,11.24.24,20.52.49Z"/>
  </svg>
);
const RedNoteLink = ({ name }) => {
  if (!name) return null;
  const webUrl = `https://www.xiaohongshu.com/search_result/?keyword=${encodeURIComponent(name)}&source=web_explore_feed`;
  const deepUrl = `xhsdiscover://search/result?keyword=${encodeURIComponent(name)}`;
  const href = isMobile ? deepUrl : webUrl;
  return (
    <a href={href} target={isMobile ? '_self' : '_blank'} rel="noopener noreferrer"
      style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', marginLeft: '6px', padding: '2px 6px', background: '#fff0f0', borderRadius: '4px', textDecoration: 'none', fontSize: '11px', color: '#ff2442', border: '1px solid #ffe0e0', transition: 'all .12s', verticalAlign: 'middle' }}
      title="Search on 小红书"
      onClick={e => e.stopPropagation()}
      onMouseEnter={e => { e.currentTarget.style.background = '#ffe0e0'; }}
      onMouseLeave={e => { e.currentTarget.style.background = '#fff0f0'; }}>
      <XhsLogo size={14} />
      <span style={{ fontWeight: '600' }}>小红书</span>
    </a>
  );
};

const ExpandableNotes = ({ text, textLocal, lang, maxLines = 2 }) => {
  const [expanded, setExpanded] = useState(false);
  const displayText = lang === 'local' && textLocal ? textLocal : text;
  if (!displayText) return null;
  return (
    <div style={{ marginTop: '6px', fontSize: '12px', color: '#6b6b6b', background: '#fafaf8', padding: '8px 10px', borderRadius: '6px', border: '1px solid #f0efed' }}>
      <div style={{
        overflow: expanded ? 'visible' : 'hidden',
        display: expanded ? 'block' : '-webkit-box',
        WebkitLineClamp: expanded ? 'unset' : maxLines,
        WebkitBoxOrient: 'vertical',
        lineHeight: 1.6,
        whiteSpace: 'pre-wrap'
      }}>
        {displayText}
      </div>
      <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        style={{ background: 'none', border: 'none', color: '#4a90d9', fontSize: '11px', cursor: 'pointer', padding: '4px 0 0', fontWeight: '500' }}>
        {expanded ? L('show_less', lang) : L('show_more', lang)}
      </button>
    </div>
  );
};

const KanbanView = ({ day, tripSummary, showSummary, bp, lang, mapProvider, onItemClick, onBudgetClick, editorDay, liveDayTotal, saveMutations, setEditorSelections, editorSelections, pendingSelection, setPendingSelection, routeCache, fetchRoute }) => {
  const sm = bp === 'sm';
  const px = sm ? '16px' : bp === 'md' ? '32px' : '48px';

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={{
        width: '100%',
        height: sm ? '120px' : '200px',
        background: day.cover ? `linear-gradient(to bottom, rgba(0,0,0,0) 50%, rgba(0,0,0,0.03) 100%), url(${day.cover})` : '#f5f5f5',
        backgroundSize: 'cover', backgroundPosition: 'center'
      }} />

      <div style={{ padding: `0 ${px}` }}>
        <div style={{ marginTop: sm ? '-24px' : '-36px', marginBottom: '24px' }}>
          <div style={{ fontSize: sm ? '40px' : '56px', lineHeight: 1, marginBottom: '8px' }}>🗺️</div>

          {showSummary ? (
            <>
              <h1 style={{ fontSize: sm ? '24px' : '36px', fontWeight: '700', color: '#37352f', margin: '0 0 20px', lineHeight: 1.25 }}>
                {lang === 'local' && tripSummary.description_local ? tripSummary.description_local : tripSummary.description}
              </h1>
              <div style={{
                padding: sm ? '12px' : '16px 20px',
                background: '#fbfbfa', borderRadius: '8px',
                border: '1px solid #f0efed', marginBottom: '32px'
              }}>
                <PropertyRow label={L('trip_type', lang)}>{lang === 'local' && tripSummary.trip_type_local ? tripSummary.trip_type_local : tripSummary.trip_type}</PropertyRow>
                {tripSummary.base_location && <PropertyRow label={L('base_location', lang)}>{tripSummary.base_location}</PropertyRow>}
                <PropertyRow label={L('period', lang)}>{lang === 'local' && tripSummary.period_local ? tripSummary.period_local : tripSummary.period}</PropertyRow>
                <PropertyRow label={L('travelers', lang)}>{lang === 'local' && tripSummary.travelers_local ? tripSummary.travelers_local : tripSummary.travelers}</PropertyRow>
                <PropertyRow label={L('budget_trip', lang)}>{tripSummary.budget_per_trip}</PropertyRow>
                {/* Preferences hidden per user request */}
              </div>
            </>
          ) : (
            <>
            <h1 style={{ fontSize: sm ? '24px' : '36px', fontWeight: '700', color: '#37352f', margin: '0 0 4px', lineHeight: 1.25 }}>
              {dayLabel(day, lang)}
            </h1>
            </>
          )}

          {showSummary && (
            <h2 style={{ fontSize: sm ? '20px' : '26px', fontWeight: '700', color: '#37352f', margin: '0 0 28px' }}>
              {dayLabel(day, lang)}
            </h2>
          )}

          {/* Route gap summary (AC12/AC23): show travel times between consecutive filled slots */}
          {routeCache && (() => {
            const entries = Object.entries(routeCache);
            if (!entries.length) return null;
            return (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px', marginBottom: '4px' }}>
                {entries.map(([pairKey, data]) => (
                  <span key={pairKey} style={{ fontSize: '11px', color: data.status === 'ok' ? '#6b6b6b' : '#e07c5a', background: '#f5f5f3', borderRadius: '4px', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {data.status === 'ok' ? ('~' + (data.segment && data.segment.duration_min) + ' min') : 'route unknown'}
                    {(data.status === 'unknown' || data.status === 'error') && fetchRoute && (
                      <button onClick={() => { const [a, b] = pairKey.split(':'); fetchRoute(a, b, pairKey); }} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '10px', color: '#4a90d9', padding: 0 }}>retry</button>
                    )}
                  </span>
                ))}
              </div>
            );
          })()}
        </div>

        {/* User Plans */}
        {day.user_plans && day.user_plans.length > 0 && (
          <Section title={L('user_plans', lang)} icon="📝">
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

        {/* ========== HORIZONTAL SCROLL CARD ROWS ========== */}
        {(() => {
          const cardW = sm ? 240 : 280;
          const cardH = sm ? 300 : 320;
          const imgH = sm ? 120 : 140;
          const categoryColors = { meals: '#e67e22', attractions: '#3498db', entertainment: '#9b59b6', shopping: '#e74c3c', cafe: '#D4A574', accommodation: '#27ae60', transportation: '#0ea5e9' };

          const scrollContainerStyle = {
            display: 'flex', flexWrap: 'nowrap', gap: '12px',
            overflowX: 'auto', overflowY: 'hidden',
            scrollBehavior: 'smooth', WebkitOverflowScrolling: 'touch',
            scrollSnapType: 'x proximity',
            paddingBottom: '8px',
            scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,0,0,0.15) transparent'
          };

          const cardStyle = (catColor, isPrimary, isOptional) => ({
            width: cardW + 'px', minWidth: cardW + 'px', height: cardH + 'px',
            flexShrink: 0, scrollSnapAlign: 'start',
            background: '#fff', borderRadius: '8px',
            border: isOptional ? '1.5px dashed ' + catColor + '80' : 'none',
            boxShadow: isOptional ? '0 1px 3px rgba(0,0,0,0.04)' : (isPrimary ? '0 1px 3px rgba(0,0,0,0.06), 0 0 0 1.5px ' + catColor + '33' : '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'),
            overflow: 'hidden', transition: 'box-shadow .15s, transform .15s', cursor: 'pointer',
            display: 'flex', flexDirection: 'column'
          });

          const hoverOn = (e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1), 0 0 0 1px rgba(74,144,217,0.2)'; e.currentTarget.style.transform = 'translateY(-2px)'; };
          const hoverOff = (e, catColor, isPrimary, isOptional) => { e.currentTarget.style.boxShadow = isOptional ? '0 1px 3px rgba(0,0,0,0.04)' : (isPrimary ? '0 1px 3px rgba(0,0,0,0.06), 0 0 0 1.5px ' + catColor + '33' : '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'); e.currentTarget.style.transform = 'translateY(0)'; };

          const categoryRowStyle = { position: 'relative' };
          const fadeStyle = {
            content: "''", position: 'absolute', right: 0, bottom: '8px',
            width: '40px', height: (cardH) + 'px',
            background: 'linear-gradient(to right, transparent, rgba(255,255,255,0.9))',
            pointerEvents: 'none', zIndex: 1
          };

          return (
            <>
              {/* Meals */}
              <Section title={L('meals', lang)} icon="🍽️">
                <div style={categoryRowStyle}>
                  <div style={scrollContainerStyle} className="category-scroll-container">
                    {['breakfast', 'lunch', 'dinner'].flatMap(type => {
                      const meal = day.meals[type];
                      if (!meal) return [];
                      const emoji = mealEmoji[type] || '';
                      const label = L(type, lang);
                      const out = [{...meal, _type: type, _emoji: emoji, _label: label, _isPrimary: true, _oi: 0}];
                      // Bug-1: meal alternatives surface as additional non-primary cards
                      const alts = (day.meal_alternatives && day.meal_alternatives[type]) || [];
                      alts.forEach((alt, ai) => out.push({...alt, _type: type, _emoji: emoji, _label: label, _isPrimary: false, _oi: ai + 1}));
                      return out;
                    }).map((opt, gi) => {
                      const catColor = categoryColors.meals;
                      const isSelected = opt.selected;
                      return (
                        <div key={gi} style={{...cardStyle(catColor, opt._isPrimary), position: 'relative',
                          ...(isSelected ? { boxShadow: '0 0 0 2px #45b26b, 0 1px 3px rgba(0,0,0,0.06)' } : {})}}
                          data-slot-card={opt._isPrimary ? 'primary' : 'alternative'}
                          data-slot-id={opt._type}
                          data-option-id={opt.option_id || undefined}
                          draggable={isSelected}
                          onDragStart={isSelected ? (e) => { currentDragSlotId = opt._type; e.dataTransfer.setData('text/plain', JSON.stringify({ optionId: opt.option_id, slotId: opt._type, sourceSlotId: opt._type, direction: 'board' })); e.dataTransfer.effectAllowed = 'move'; } : undefined}
                          onDragEnd={isSelected ? () => { currentDragSlotId = null; } : undefined}
                          onClick={() => onItemClick && onItemClick(opt, 'meal')}
                          onMouseEnter={hoverOn}
                          onMouseLeave={e => hoverOff(e, catColor, opt._isPrimary)}
                        >
                          <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                            {opt.image && <img src={opt.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                              onError={e => { e.target.style.display = 'none'; }} />}
                          </div>
                          <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                            <div style={{ fontSize: '10px', fontWeight: '700', color: opt._isPrimary ? catColor : '#9b9a97', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                              <span>{opt._emoji} {opt._label}</span>
                              {opt.option_label && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97' }}>{(L('option', lang) || 'Option') + ' ' + opt.option_label}</span>}
                            </div>
                            <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                              {getDisplayName(opt, lang)}
                              <RedNoteLink name={opt.name_local || opt.name_base} />
                            </div>
                            <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                              {opt.time && opt.time.start !== '00:00' && <div>{opt.time.start} – {opt.time.end}{opt.cost > 0 ? ' · ' + fmtCost(opt.cost, undefined, lang) : (opt.cost_display ? ' · ' + opt.cost_display : '')}</div>}
                              {!opt.time && opt.cost > 0 && <div>{fmtCost(opt.cost, undefined, lang)}</div>}
                              {!opt.time && !(opt.cost > 0) && opt.cost_display && <div>{opt.cost_display}</div>}
                              {getDisplayField(opt, 'cuisine', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(opt, 'cuisine', lang)}</div>}
                              {(opt.location_base || opt.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={opt} lang={lang} mapProvider={mapProvider} /></div>}
                            </div>
                            <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                              {lang === 'local' && opt.notes_local ? opt.notes_local : opt.notes_base}
                            </div>
                          </div>
                          {/* AC22: slot visual state badge for meal slots (missing/skipped/late-arrival/required-empty) */}
                          {editorDay && opt._isPrimary && (() => {
                            const slotKey = day.day + ':' + opt._type;
                            const edSlot = editorDay.slots && editorDay.slots[opt._type];
                            const isRequired = ['breakfast','lunch','dinner'].includes(opt._type);
                            // Missing: slot key absent from editorDay.slots entirely
                            if (!edSlot && isRequired) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#fff0e6', border: '1px solid #f0b870', borderRadius: '4px', fontSize: '10px', color: '#c07000', padding: '1px 5px' }}>missing</div>;
                            if (!edSlot) return null;
                            const resolvedId = Object.prototype.hasOwnProperty.call(editorSelections || {}, slotKey) ? (editorSelections || {})[slotKey] : edSlot.selected_option_id;
                            if (edSlot.skipped) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', fontSize: '10px', color: '#9b9a97', padding: '1px 5px' }}>{edSlot.skipped_reason || 'skipped'}</div>;
                            if (edSlot.late_arrival_placeholder) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#e8f4fd', border: '1px solid #a8d4f0', borderRadius: '4px', fontSize: '10px', color: '#2b63b5', padding: '1px 5px' }}>late arrival</div>;
                            if (isRequired && !resolvedId) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#fff4f4', border: '1px solid #f0b3b3', borderRadius: '4px', fontSize: '10px', color: '#e07c5a', padding: '1px 5px' }}>required</div>;
                            return null;
                          })()}
                          {(() => {
                            const edSlot = editorDay && editorDay.slots && editorDay.slots[opt._type];
                            const isGated = !edSlot || edSlot.skipped || edSlot.late_arrival_placeholder;
                            return <div className="slot-drop" data-slot-id={opt._type} data-droppable={isGated ? 'false' : 'true'} aria-hidden="true" style={{ position: 'absolute', inset: 0, background: 'transparent', transition: 'background 0.12s' }}
                            onDragOver={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); return; } e.preventDefault(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (currentDragSlotId && !_isCompatible(currentDragSlotId, toSlotId)) { e.dataTransfer.dropEffect = 'none'; return; } e.dataTransfer.dropEffect = 'move'; e.currentTarget.setAttribute('data-drop-active', ''); }}
                            onDragLeave={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); }}
                            onDrop={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); e.currentTarget.removeAttribute('data-drop-active'); return; } e.preventDefault(); e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); try { const payload = JSON.parse(e.dataTransfer.getData('text/plain')); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); const fromSlotId = payload.slotId || payload.originSlotId; if (fromSlotId && !_isCompatible(fromSlotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (payload.direction === 'board' && payload.sourceSlotId && saveMutations) { const dayNum = day && day.day; setEditorSelections && setEditorSelections(prev => ({ ...prev, [dayNum + ':' + payload.sourceSlotId]: null, [dayNum + ':' + toSlotId]: payload.optionId })); saveMutations(dayNum, [{ type: 'select', slot: payload.sourceSlotId, option_id: null }, { type: 'select', slot: toSlotId, option_id: payload.optionId, origin_slot_id: payload.sourceSlotId }]); } else if (window.setEditorSelection) window.setEditorSelection(toSlotId, payload.optionId, payload.originSlotId || null); } catch (_) {} }}
                            onClick={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') return; if (!pendingSelection) return; e.preventDefault(); e.stopPropagation(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (!_isCompatible(pendingSelection.slotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (window.applyEditorSelection) window.applyEditorSelection(pendingSelection.optionId, toSlotId, pendingSelection.originSlotId); }}
                          />;
                          })()}
                        </div>
                      );
                    })}
                  </div>
                  <div style={fadeStyle} />
                </div>
              </Section>

              {/* Cafe */}
              {day.cafe && day.cafe.length > 0 && (() => {
                const cafeSlotMap = {};
                if (editorDay && editorDay.slots) {
                  ['morning_activity', 'afternoon_activity', 'evening_activity'].forEach(slotKey => {
                    const slot = editorDay.slots[slotKey];
                    if (!slot || !slot.options) return;
                    slot.options.forEach(opt => {
                      if (opt.name) cafeSlotMap[opt.name] = slotKey;
                      if (opt.name_local) cafeSlotMap[opt.name_local] = slotKey;
                    });
                  });
                }
                return (
                <Section title={L('cafe', lang)} icon="\u2615">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.cafe.map((c, i) => {
                        const catColor = categoryColors.cafe;
                        const cafeSlotId = cafeSlotMap[c.name_base] || cafeSlotMap[c.name_local] || null;
                        const isSelected = c.selected;
                        return (
                          <div key={i} style={{...cardStyle(catColor, false, c.optional), position: 'relative',
                            ...(isSelected ? { boxShadow: '0 0 0 2px #45b26b, 0 1px 3px rgba(0,0,0,0.06)' } : {})}}
                            data-slot-card={isSelected ? 'primary' : 'alternative'}
                            data-slot-id={cafeSlotId || undefined}
                            data-option-id={c.option_id || undefined}
                            draggable={isSelected && !!cafeSlotId}
                            onDragStart={isSelected && cafeSlotId ? (e) => { currentDragSlotId = cafeSlotId; e.dataTransfer.setData('text/plain', JSON.stringify({ optionId: c.option_id, slotId: cafeSlotId, sourceSlotId: cafeSlotId, direction: 'board' })); e.dataTransfer.effectAllowed = 'move'; } : undefined}
                            onDragEnd={isSelected && cafeSlotId ? () => { currentDragSlotId = null; } : undefined}
                            onClick={() => onItemClick && onItemClick(c, 'cafe')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, c.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#faf6f0', flexShrink: 0 }}>
                              {c.image && <img src={c.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>\u2615 {L('cafe', lang)}</span>
                                {c.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(c, lang)}
                                <RedNoteLink name={c.name_local || c.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {c.time && c.time.start !== '00:00' && <div>{c.time.start} \u2013 {c.time.end}{c.cost > 0 ? ' \u00b7 ' + fmtCost(c.cost, undefined, lang) : (c.cost_display ? ' \u00b7 ' + c.cost_display : '')}</div>}
                                {!c.time && c.cost > 0 && <div>{fmtCost(c.cost, undefined, lang)}</div>}
                                {!c.time && !(c.cost > 0) && c.cost_display && <div>{c.cost_display}</div>}
                                {getDisplayField(c, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(c, 'type', lang)}</div>}
                                {getDisplayField(c, 'cuisine', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(c, 'cuisine', lang)}</div>}
                                {(c.location_base || c.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={c} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && c.notes_local ? c.notes_local : c.notes_base}
                              </div>
                            </div>
                            {/* AC22: visual state badges for cafe activity slot */}
                            {cafeSlotId && editorDay && (() => {
                              const edSlot = editorDay.slots && editorDay.slots[cafeSlotId];
                              if (!edSlot) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#fff0e6', border: '1px solid #f0b870', borderRadius: '4px', fontSize: '10px', color: '#c07000', padding: '1px 5px' }}>missing</div>;
                              if (edSlot.skipped) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', fontSize: '10px', color: '#9b9a97', padding: '1px 5px' }}>{edSlot.skipped_reason || 'skipped'}</div>;
                              if (edSlot.late_arrival_placeholder) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#e8f4fd', border: '1px solid #a8d4f0', borderRadius: '4px', fontSize: '10px', color: '#2b63b5', padding: '1px 5px' }}>late arrival</div>;
                              return null;
                            })()}
                            {cafeSlotId && (() => {
                              const edSlot = editorDay && editorDay.slots && editorDay.slots[cafeSlotId];
                              const isGated = !edSlot || edSlot.skipped || edSlot.late_arrival_placeholder;
                              return <div className="slot-drop" data-slot-id={cafeSlotId} data-droppable={isGated ? 'false' : 'true'} aria-hidden="true" style={{ position: 'absolute', inset: 0, background: 'transparent', transition: 'background 0.12s' }}
                              onDragOver={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); return; } e.preventDefault(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (currentDragSlotId && !_isCompatible(currentDragSlotId, toSlotId)) { e.dataTransfer.dropEffect = 'none'; return; } e.dataTransfer.dropEffect = 'move'; e.currentTarget.setAttribute('data-drop-active', ''); }}
                              onDragLeave={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); }}
                              onDrop={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); e.currentTarget.removeAttribute('data-drop-active'); return; } e.preventDefault(); e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); try { const payload = JSON.parse(e.dataTransfer.getData('text/plain')); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); const fromSlotId = payload.slotId || payload.originSlotId; if (fromSlotId && !_isCompatible(fromSlotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (payload.direction === 'board' && payload.sourceSlotId && saveMutations) { const dayNum = day && day.day; setEditorSelections && setEditorSelections(prev => ({ ...prev, [dayNum + ':' + payload.sourceSlotId]: null, [dayNum + ':' + toSlotId]: payload.optionId })); saveMutations(dayNum, [{ type: 'select', slot: payload.sourceSlotId, option_id: null }, { type: 'select', slot: toSlotId, option_id: payload.optionId, origin_slot_id: payload.sourceSlotId }]); } else if (window.setEditorSelection) window.setEditorSelection(toSlotId, payload.optionId, payload.originSlotId || null); } catch (_) {} }}
                              onClick={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') return; if (!pendingSelection) return; e.preventDefault(); e.stopPropagation(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (!_isCompatible(pendingSelection.slotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (window.applyEditorSelection) window.applyEditorSelection(pendingSelection.optionId, toSlotId, pendingSelection.originSlotId); }}
                            />;
                            })()}
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
                );
              })()}

              {/* Attractions */}
              {day.attractions && day.attractions.length > 0 && (() => {
                // Build name->slotId map from editorDay activity slots
                const activitySlotMap = {};
                if (editorDay && editorDay.slots) {
                  ['morning_activity', 'afternoon_activity', 'evening_activity'].forEach(slotKey => {
                    const slot = editorDay.slots[slotKey];
                    if (!slot || !slot.options) return;
                    slot.options.forEach(opt => {
                      if (opt.name) activitySlotMap[opt.name] = slotKey;
                      if (opt.name_local) activitySlotMap[opt.name_local] = slotKey;
                    });
                  });
                }
                return (
                <Section title={L('attractions', lang)} icon="📍">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.attractions.map((attr, i) => {
                        const catColor = categoryColors.attractions;
                        const actSlotId = activitySlotMap[attr.name_base] || activitySlotMap[attr.name_local] || null;
                        const isSelected = attr.selected;
                        return (
                          <div key={i} style={{...cardStyle(catColor, false, attr.optional), position: 'relative',
                            ...(isSelected ? { boxShadow: '0 0 0 2px #45b26b, 0 1px 3px rgba(0,0,0,0.06)' } : {})}}
                            draggable={isSelected && !!actSlotId}
                            onDragStart={isSelected && actSlotId ? (e) => { currentDragSlotId = actSlotId; e.dataTransfer.setData('text/plain', JSON.stringify({ optionId: attr.option_id, slotId: actSlotId, sourceSlotId: actSlotId, direction: 'board' })); e.dataTransfer.effectAllowed = 'move'; } : undefined}
                            onDragEnd={isSelected && actSlotId ? () => { currentDragSlotId = null; } : undefined}
                            onClick={() => onItemClick && onItemClick(attr, 'attraction')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, attr.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#eef4f9', flexShrink: 0 }}>
                              {attr.image && <img src={attr.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>📍 {L('attractions', lang)}</span>
                                {attr.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(attr, lang)}
                                <RedNoteLink name={attr.name_local || attr.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {attr.time && <div>{attr.time.start} – {attr.time.end}{attr.cost > 0 ? ' · ' + fmtCost(attr.cost, undefined, lang) : ''}</div>}
                                {!attr.time && attr.cost > 0 && <div>{fmtCost(attr.cost, undefined, lang)}</div>}
                                {getDisplayField(attr, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(attr, 'type', lang)}</div>}
                                {(attr.location_base || attr.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={attr} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && attr.notes_local ? attr.notes_local : attr.notes_base}
                              </div>
                            </div>
                            {/* AC22: visual state badges for attraction activity slot */}
                            {actSlotId && editorDay && (() => {
                              const edSlot = editorDay.slots && editorDay.slots[actSlotId];
                              if (!edSlot) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#fff0e6', border: '1px solid #f0b870', borderRadius: '4px', fontSize: '10px', color: '#c07000', padding: '1px 5px' }}>missing</div>;
                              if (edSlot.skipped) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', fontSize: '10px', color: '#9b9a97', padding: '1px 5px' }}>{edSlot.skipped_reason || 'skipped'}</div>;
                              if (edSlot.late_arrival_placeholder) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#e8f4fd', border: '1px solid #a8d4f0', borderRadius: '4px', fontSize: '10px', color: '#2b63b5', padding: '1px 5px' }}>late arrival</div>;
                              return null;
                            })()}
                            {actSlotId && (() => {
                              const edSlot = editorDay && editorDay.slots && editorDay.slots[actSlotId];
                              const isGated = !edSlot || edSlot.skipped || edSlot.late_arrival_placeholder;
                              return <div className="slot-drop" data-slot-id={actSlotId} data-droppable={isGated ? 'false' : 'true'} aria-hidden="true" style={{ position: 'absolute', inset: 0, background: 'transparent', transition: 'background 0.12s' }}
                              onDragOver={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); return; } e.preventDefault(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (currentDragSlotId && !_isCompatible(currentDragSlotId, toSlotId)) { e.dataTransfer.dropEffect = 'none'; return; } e.dataTransfer.dropEffect = 'move'; e.currentTarget.setAttribute('data-drop-active', ''); }}
                              onDragLeave={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); }}
                              onDrop={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); e.currentTarget.removeAttribute('data-drop-active'); return; } e.preventDefault(); e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); try { const payload = JSON.parse(e.dataTransfer.getData('text/plain')); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); const fromSlotId = payload.slotId || payload.originSlotId; if (fromSlotId && !_isCompatible(fromSlotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (payload.direction === 'board' && payload.sourceSlotId && saveMutations) { const dayNum = day && day.day; setEditorSelections && setEditorSelections(prev => ({ ...prev, [dayNum + ':' + payload.sourceSlotId]: null, [dayNum + ':' + toSlotId]: payload.optionId })); saveMutations(dayNum, [{ type: 'select', slot: payload.sourceSlotId, option_id: null }, { type: 'select', slot: toSlotId, option_id: payload.optionId, origin_slot_id: payload.sourceSlotId }]); } else if (window.setEditorSelection) window.setEditorSelection(toSlotId, payload.optionId, payload.originSlotId || null); } catch (_) {} }}
                              onClick={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') return; if (!pendingSelection) return; e.preventDefault(); e.stopPropagation(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (!_isCompatible(pendingSelection.slotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (window.applyEditorSelection) window.applyEditorSelection(pendingSelection.optionId, toSlotId, pendingSelection.originSlotId); }}
                            />;
                            })()}
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
                );
              })()}

              {/* Entertainment */}
              {day.entertainment?.length > 0 && (() => {
                const entSlotMap = {};
                if (editorDay && editorDay.slots) {
                  ['morning_activity', 'afternoon_activity', 'evening_activity'].forEach(slotKey => {
                    const slot = editorDay.slots[slotKey];
                    if (!slot || !slot.options) return;
                    slot.options.forEach(opt => {
                      if (opt.name) entSlotMap[opt.name] = slotKey;
                      if (opt.name_local) entSlotMap[opt.name_local] = slotKey;
                    });
                  });
                }
                return (
                <Section title={L('entertainment', lang)} icon="🎭">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.entertainment.map((ent, i) => {
                        const catColor = categoryColors.entertainment;
                        const entSlotId = entSlotMap[ent.name_base] || entSlotMap[ent.name_local] || null;
                        const isSelected = ent.selected;
                        return (
                          <div key={i} style={{...cardStyle(catColor, false, ent.optional), position: 'relative',
                            ...(isSelected ? { boxShadow: '0 0 0 2px #45b26b, 0 1px 3px rgba(0,0,0,0.06)' } : {})}}
                            draggable={isSelected && !!entSlotId}
                            onDragStart={isSelected && entSlotId ? (e) => { currentDragSlotId = entSlotId; e.dataTransfer.setData('text/plain', JSON.stringify({ optionId: ent.option_id, slotId: entSlotId, sourceSlotId: entSlotId, direction: 'board' })); e.dataTransfer.effectAllowed = 'move'; } : undefined}
                            onDragEnd={isSelected && entSlotId ? () => { currentDragSlotId = null; } : undefined}
                            onClick={() => onItemClick && onItemClick(ent, 'entertainment')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, ent.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                              {ent.image && <img src={ent.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>🎭 {L('entertainment', lang)}</span>
                                {ent.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(ent, lang)}
                                <RedNoteLink name={ent.name_local || ent.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {ent.time && <div>{ent.time.start} – {ent.time.end}{ent.cost > 0 ? ' · ' + fmtCost(ent.cost, undefined, lang) : ''}</div>}
                                {!ent.time && ent.cost > 0 && <div>{fmtCost(ent.cost, undefined, lang)}</div>}
                                {getDisplayField(ent, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(ent, 'type', lang)}</div>}
                                {(ent.location_base || ent.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={ent} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && ent.notes_local ? ent.notes_local : (lang === 'local' && ent.note_local ? ent.note_local : ent.note_base)}
                              </div>
                            </div>
                            {/* AC22: visual state badges for entertainment activity slot */}
                            {entSlotId && editorDay && (() => {
                              const edSlot = editorDay.slots && editorDay.slots[entSlotId];
                              if (!edSlot) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#fff0e6', border: '1px solid #f0b870', borderRadius: '4px', fontSize: '10px', color: '#c07000', padding: '1px 5px' }}>missing</div>;
                              if (edSlot.skipped) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', fontSize: '10px', color: '#9b9a97', padding: '1px 5px' }}>{edSlot.skipped_reason || 'skipped'}</div>;
                              if (edSlot.late_arrival_placeholder) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#e8f4fd', border: '1px solid #a8d4f0', borderRadius: '4px', fontSize: '10px', color: '#2b63b5', padding: '1px 5px' }}>late arrival</div>;
                              return null;
                            })()}
                            {entSlotId && (() => {
                              const edSlot = editorDay && editorDay.slots && editorDay.slots[entSlotId];
                              const isGated = !edSlot || edSlot.skipped || edSlot.late_arrival_placeholder;
                              return <div className="slot-drop" data-slot-id={entSlotId} data-droppable={isGated ? 'false' : 'true'} aria-hidden="true" style={{ position: 'absolute', inset: 0, background: 'transparent', transition: 'background 0.12s' }}
                              onDragOver={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); return; } e.preventDefault(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (currentDragSlotId && !_isCompatible(currentDragSlotId, toSlotId)) { e.dataTransfer.dropEffect = 'none'; return; } e.dataTransfer.dropEffect = 'move'; e.currentTarget.setAttribute('data-drop-active', ''); }}
                              onDragLeave={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); }}
                              onDrop={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); e.currentTarget.removeAttribute('data-drop-active'); return; } e.preventDefault(); e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); try { const payload = JSON.parse(e.dataTransfer.getData('text/plain')); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); const fromSlotId = payload.slotId || payload.originSlotId; if (fromSlotId && !_isCompatible(fromSlotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (payload.direction === 'board' && payload.sourceSlotId && saveMutations) { const dayNum = day && day.day; setEditorSelections && setEditorSelections(prev => ({ ...prev, [dayNum + ':' + payload.sourceSlotId]: null, [dayNum + ':' + toSlotId]: payload.optionId })); saveMutations(dayNum, [{ type: 'select', slot: payload.sourceSlotId, option_id: null }, { type: 'select', slot: toSlotId, option_id: payload.optionId, origin_slot_id: payload.sourceSlotId }]); } else if (window.setEditorSelection) window.setEditorSelection(toSlotId, payload.optionId, payload.originSlotId || null); } catch (_) {} }}
                              onClick={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') return; if (!pendingSelection) return; e.preventDefault(); e.stopPropagation(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (!_isCompatible(pendingSelection.slotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } _flashSuccess(toSlotId); if (window.applyEditorSelection) window.applyEditorSelection(pendingSelection.optionId, toSlotId, pendingSelection.originSlotId); }}
                            />;
                            })()}
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
                );
              })()}

              {/* Shopping */}
              {day.shopping && day.shopping.length > 0 && (
                <Section title={L('shopping', lang)} icon="🛍️">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.shopping.map((shop, i) => {
                        const catColor = categoryColors.shopping;
                        return (
                          <div key={i} style={cardStyle(catColor, false, shop.optional)}
                            onClick={() => onItemClick && onItemClick(shop, 'shopping')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, shop.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                              {shop.image && <img src={shop.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>🛍️ {L('shopping', lang)}</span>
                                {shop.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(shop, lang)}
                                <RedNoteLink name={shop.name_local || shop.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {shop.time && <div>{shop.time.start} – {shop.time.end}{shop.cost > 0 ? ' · ' + fmtCost(shop.cost, undefined, lang) : ''}</div>}
                                {!shop.time && shop.cost > 0 && <div>{fmtCost(shop.cost, undefined, lang)}</div>}
                                {getDisplayField(shop, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(shop, 'type', lang)}</div>}
                                {(shop.location_base || shop.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={shop} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && shop.notes_local ? shop.notes_local : shop.notes_base}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
              )}

              {/* Bug-3: Unscheduled / Optional section for items lacking a timeline time slot */}
              {day.unscheduled_optionals && day.unscheduled_optionals.length > 0 && (
                <Section title="Unscheduled / Optional" icon="🗓️">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.unscheduled_optionals.map((it, i) => (
                        <div key={i} style={cardStyle('#9b9a97', false, true)}
                          onClick={() => onItemClick && onItemClick(it, it._category)}
                        >
                          <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                            <div style={{ fontSize: '10px', fontWeight: '700', color: '#9b9a97', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px' }}>
                              {it._category} · Optional
                            </div>
                            <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {getDisplayName(it, lang)}
                            </div>
                            <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                              {lang === 'local' && it.notes_local ? it.notes_local : it.notes_base}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
              )}

              {/* Accommodation */}
              {day.accommodation && (
                <Section title={L('accommodation', lang)} icon="🏨">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {(day.accommodation ? [day.accommodation] : []).map((acc, i) => {
                        const catColor = categoryColors.accommodation;
                        return (
                          <div key={i} style={{...cardStyle(catColor, false), position: 'relative'}}
                            onClick={() => onItemClick && onItemClick(acc, 'accommodation')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                              {acc.image && <img src={acc.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', flexShrink: 0 }}>
                                🏨 {L('accommodation', lang)}
                                {acc.stars > 0 && <span style={{ color: '#e9b200', marginLeft: '4px', letterSpacing: '1px' }}>{'★'.repeat(acc.stars)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(acc, lang)}
                                <RedNoteLink name={acc.name_local || acc.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {acc.check_in && <div>{L('checkin', lang)}: {acc.check_in}{acc.check_out ? ' · ' + L('checkout', lang) + ': ' + acc.check_out : ''}</div>}
                                {acc.cost > 0 && <div>{fmtCost(acc.cost, undefined, lang)}</div>}
                                {getDisplayField(acc, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(acc, 'type', lang)}</div>}
                                {(acc.location_base || acc.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={acc} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && acc.notes_local ? acc.notes_local : acc.notes_base}
                              </div>
                            </div>
                            {/* AC22: accommodation slot visual state badges */}
                            {editorDay && (() => {
                              const edAcc = editorDay.accommodation;
                              const accKey = day.day + ':accommodation';
                              const selectedAccId = Object.prototype.hasOwnProperty.call(editorSelections || {}, accKey) ? (editorSelections || {})[accKey] : (edAcc && edAcc.selected_option_id);
                              if (!edAcc) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#fff0e6', border: '1px solid #f0b870', borderRadius: '4px', fontSize: '10px', color: '#c07000', padding: '1px 5px' }}>missing</div>;
                              if (edAcc.skipped) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', fontSize: '10px', color: '#9b9a97', padding: '1px 5px' }}>{edAcc.skipped_reason || 'skipped'}</div>;
                              if (edAcc && edAcc.late_arrival_placeholder) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#e8f4fd', border: '1px solid #a8d4f0', borderRadius: '4px', fontSize: '10px', color: '#2b63b5', padding: '1px 5px' }}>late arrival</div>;
                              if (!selectedAccId) return <div style={{ position: 'absolute', top: '6px', left: '6px', pointerEvents: 'none', zIndex: 3, background: '#fff4f4', border: '1px solid #f0b3b3', borderRadius: '4px', fontSize: '10px', color: '#e07c5a', padding: '1px 5px' }}>required</div>;
                              return null;
                            })()}
                            {(() => {
                              const edAcc = editorDay && editorDay.accommodation;
                              const isGated = !edAcc || edAcc.late_arrival_placeholder || edAcc.skipped;
                              return <div className="slot-drop" data-slot-id="accommodation" data-droppable={isGated ? 'false' : 'true'} aria-hidden="true" style={{ position: 'absolute', inset: 0, background: 'transparent', transition: 'background 0.12s' }}
                                onDragOver={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); return; } e.preventDefault(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (currentDragSlotId && !_isCompatible(currentDragSlotId, toSlotId)) { e.dataTransfer.dropEffect = 'none'; return; } e.dataTransfer.dropEffect = 'move'; e.currentTarget.setAttribute('data-drop-active', ''); }}
                                onDragLeave={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); }}
                                onDrop={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') { e.preventDefault(); e.currentTarget.removeAttribute('data-drop-active'); return; } e.preventDefault(); e.currentTarget.style.background = 'rgba(0,0,0,0)'; e.currentTarget.removeAttribute('data-drop-active'); try { const payload = JSON.parse(e.dataTransfer.getData('text/plain')); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); const fromSlotId = payload.slotId || payload.originSlotId; if (fromSlotId && !_isCompatible(fromSlotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } if (window.setEditorSelection) window.setEditorSelection(toSlotId, payload.optionId, payload.originSlotId || null); } catch (_) {} }}
                                onClick={(e) => { if (e.currentTarget.getAttribute('data-droppable') === 'false') return; if (!pendingSelection) return; e.preventDefault(); e.stopPropagation(); const toSlotId = e.currentTarget.getAttribute('data-slot-id'); if (!_isCompatible(pendingSelection.slotId, toSlotId)) { const el = e.currentTarget; el.setAttribute('data-drop-reject', ''); setTimeout(() => el.removeAttribute('data-drop-reject'), 400); return; } if (window.applyEditorSelection) window.applyEditorSelection(pendingSelection.optionId, toSlotId, pendingSelection.originSlotId); }}
                              />;
                            })()}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </Section>
              )}

              {/* Transportation */}
              {(day.transportation || (day.intra_routes && day.intra_routes.length > 0)) && (
                <Section title={L('transportation', lang)} icon={(day.transportation && day.transportation.icon) || '✈️'}>
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {[...(day.transportation ? [day.transportation] : []), ...(day.intra_routes || [])].map((tr, i) => {
                        const catColor = categoryColors.transportation;
                        return (
                          <div key={i} style={{...cardStyle(catColor, false), height: 'auto', minHeight: sm ? '160px' : '180px'}}
                            onClick={() => onItemClick && onItemClick(tr, 'transportation')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false)}
                          >
                            <div style={{ padding: '12px 14px', flex: 1 }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
                                {tr.icon} {L('transportation', lang)}
                              </div>
                              <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                {lang === 'local' && tr.from_local ? tr.from_local : tr.from_base}
                                {' → '}
                                {lang === 'local' && tr.to_local ? tr.to_local : tr.to_base}
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.7 }}>
                                {tr.time && <div>{tr.time.start} – {tr.time.end}</div>}
                                {(tr.cost > 0 || tr.cost_type_base === 'prepaid') && <div>{fmtCost(tr.cost, tr.cost_type_base, lang)}</div>}
                                {getDisplayField(tr, 'type', lang) && <div>{getDisplayField(tr, 'type', lang)}</div>}
                                {getDisplayField(tr, 'company', lang) && <div>{getDisplayField(tr, 'company', lang)}</div>}
                                {tr.route_number && <div>{tr.route_number}</div>}
                              </div>
                              {getDisplayField(tr, 'status', lang) && (
                                <div style={{ marginTop: '4px' }}>
                                  <span style={{
                                    padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '600',
                                    background: tr.status_base?.includes('URGENT') ? '#fff4e6' : tr.status_base?.includes('VERIFIED') ? '#e9f5ec' : '#edf2fc',
                                    color: tr.status_base?.includes('URGENT') ? '#d97706' : tr.status_base?.includes('VERIFIED') ? '#1a7a32' : '#2b63b5'
                                  }}>
                                    {getDisplayField(tr, 'status', lang)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </Section>
              )}

              {/* Budget */}
              <Section title={L('budget', lang)} icon="💰">
                <div style={{
                  background: '#fff', borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                  padding: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: sm ? 'center' : 'center', gap: '20px', flexDirection: sm ? 'column' : 'row' }}>
                    <Donut budget={day.budget} size={sm ? 72 : 88} onBudgetClick={onBudgetClick} day={day} />
                    <div style={{ fontSize: '13px', color: '#6b6b6b', lineHeight: 2, flex: 1, width: '100%' }}>
                      {[
                        { k: 'meals', l: L('meals', lang), c: '#f0b429' },
                        { k: 'attractions', l: L('attractions', lang), c: '#4a90d9' },
                        { k: 'entertainment', l: L('entertainment', lang), c: '#9b6dd7' },
                        { k: 'accommodation', l: L('accommodation', lang), c: '#45b26b' },
                        { k: 'shopping', l: L('shopping', lang), c: '#e07c5a' },
                        { k: 'cafe', l: L('cafe', lang), c: '#D4A574' },
                        { k: 'transportation', l: L('transport', lang), c: '#0ea5e9' }
                      ].filter(r => day.budget[r.k] > 0).map(r => (
                        <div key={r.k} style={{
                          display: 'flex', alignItems: 'center', gap: '8px',
                          cursor: 'pointer', padding: '4px 6px', margin: '0 -6px',
                          borderRadius: '4px', transition: 'background .12s'
                        }}
                          onClick={() => onBudgetClick && onBudgetClick(r.k, day)}
                          onMouseEnter={e => e.currentTarget.style.background = 'rgba(55,53,47,0.04)'}
                          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                        >
                          <span style={{ width: '10px', height: '10px', borderRadius: '3px', background: r.c, flexShrink: 0 }} />
                          <span style={{ flex: 1 }}>{r.l}</span>
                          <span style={{ fontWeight: '600', color: '#37352f' }}>{fmtCost(day.budget[r.k], undefined, lang)}</span>
                        </div>
                      ))}
                      <div style={{ borderTop: '1px solid #edece9', marginTop: '8px', paddingTop: '8px', fontWeight: '700', color: '#37352f', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{L('total', lang)}</span><span>{CURRENCY_SYMBOL}{Number(liveDayTotal?.[day.day] ?? day.budget.total).toFixed(0)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Section>
            </>
          );
        })()}

      </div>
    </div>
  );
};

// ============================================================
// TIMELINE OVERLAP DETECTION UTILITIES
// ============================================================

/**
 * Convert "HH:MM" to minutes since midnight for comparison
 */
const timeToMinutes = (timeStr) => {
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
};

/**
 * Check if two events overlap in time
 */
const eventsOverlap = (event1, event2) => {
  const start1 = timeToMinutes(event1.time.start);
  const end1 = timeToMinutes(event1.time.end);
  const start2 = timeToMinutes(event2.time.start);
  const end2 = timeToMinutes(event2.time.end);
  // Events overlap if one starts before the other ends
  return start1 < end2 && start2 < end1;
};

/**
 * Compute column layout for all events (Google Calendar style)
 * Uses greedy column assignment algorithm
 */
const computeColumnLayout = (entries) => {
  const entriesWithMinutes = entries.map(e => ({
    ...e,
    _startMin: timeToMinutes(e.time.start),
    _endMin: timeToMinutes(e.time.end)
  }));

  // Check if two events overlap using cached minutes
  const overlaps = (e1, e2) => {
    return (e1._startMin < e2._endMin) && (e2._startMin < e1._endMin);
  };

  // Greedy column assignment
  const result = [];
  for (let i = 0; i < entriesWithMinutes.length; i++) {
    const entry = entriesWithMinutes[i];
    const conflictingEntries = result.filter(e => overlaps(e, entry));
    const occupiedCols = new Set(conflictingEntries.map(e => e._column));

    let column = 0;
    while (occupiedCols.has(column)) column++;

    entry._column = column;
    result.push(entry);
  }

  // Calculate maxColumns for each conflict group
  for (let i = 0; i < result.length; i++) {
    const entry = result[i];
    const conflictingEntries = result.filter(e => overlaps(e, entry));
    const maxCol = Math.max(entry._column, ...conflictingEntries.map(e => e._column));
    entry._maxColumns = maxCol + 1;
  }

  return result;
};

// ============================================================
// TIMELINE VIEW
// ============================================================
const TimelineView = ({ day, bp, lang, mapProvider, onItemClick, editorDay, editorSelections, pendingSelection, setPendingSelection, saveMutations, setEditorSelections, routeCache, fetchRoute }) => {
  // Fix #6: Add z-index state for click handling of overlapping items
  const [topItemIndex, setTopItemIndex] = useState(null);
  const sm = bp === 'sm';
  const px = sm ? '16px' : bp === 'md' ? '32px' : '48px';
  const timeW = sm ? '48px' : '62px';

  const entries = [];
  const add = (item, type, label) => {
    // Only add if item has valid time with start and end
    // Filter out degenerate times: 00:00-00:00 (N/A items) and same start/end
    if (item?.time?.start && item?.time?.end
        && item.time.start !== '00:00'
        && item.time.end !== '00:00'
        && timeToMinutes(item.time.start) !== timeToMinutes(item.time.end)) {
      const e = { ...item, _type: type, _label: label };
      entries.push(e);
      return e;
    }
  };
  // Add transportation if exists (Fix Issue #8, #9: bilingual label respects lang toggle)
  if (day.transportation) {
    const tFrom = lang === 'local' && day.transportation.from_local ? day.transportation.from_local : day.transportation.from_base;
    const tTo = lang === 'local' && day.transportation.to_local ? day.transportation.to_local : day.transportation.to_base;
    add(day.transportation, 'transportation', `${tFrom} → ${tTo}`);
  }
  day.intra_routes?.forEach(r => {
    const label = (lang === 'local' && r.name_local) ? r.name_local : (r.name_base || r.route_number || '');
    add(r, 'transportation', label);
  });
  ['breakfast', 'brunch', 'lunch', 'dinner'].forEach(mealType => {
    const catKey = 'cat_' + mealType;
    const primary = day.meals?.[mealType];
    if (primary) {
      add(primary, 'meal', L(catKey, lang));
    }
  });
  day.attractions?.forEach(a => add(a, 'attraction', L('cat_attraction', lang)));
  day.entertainment?.forEach(e => add(e, 'entertainment', L('cat_entertainment', lang)));
  // Root cause fix: shopping items were missing from timeline - add them here
  day.shopping?.forEach(s => add(s, 'shopping', L('cat_shopping', lang)));
  day.cafe?.forEach(c => add(c, 'cafe', L('cat_cafe', lang)));
  // Fix issue #6: Add travel segments from timeline (includes return-to-hotel segment)
  day.travel_segments?.forEach(t => {
    const label = lang === 'local' && t.name_local ? t.name_local : (t.name_base || '');
    add(t, 'travel', label);
  });
  // Accommodation check-in: start after last activity/travel segment ends
  if (day.accommodation) {
    const accEntry = add(day.accommodation, 'accommodation', L('cat_checkin', lang));
    if (accEntry) {
      let latestEnd = 0;
      entries.forEach(e => {
        if (e._type !== 'accommodation') {
          const m = timeToMinutes(e.time.end);
          if (m > latestEnd) latestEnd = m;
        }
      });
      if (latestEnd > 0 && latestEnd >= timeToMinutes(accEntry.time.start)) {
        const startH = String(Math.floor(latestEnd / 60)).padStart(2, '0');
        const startM = String(latestEnd % 60).padStart(2, '0');
        const endMins = latestEnd + 30;
        const endH = String(Math.floor(endMins / 60)).padStart(2, '0');
        const endM = String(endMins % 60).padStart(2, '0');
        accEntry.time = { ...accEntry.time, start: startH + ':' + startM, end: endH + ':' + endM };
      }
    }
  }

  // Sort by start time
  entries.sort((a, b) => { const cmp = a.time.start.localeCompare(b.time.start); if (cmp !== 0) return cmp; const order = {transportation:0, travel:1, meal:2, attraction:3, cafe:4, entertainment:5, shopping:6, accommodation:7}; return (order[a._type] ?? 99) - (order[b._type] ?? 99); });

  // Deduplicate: for optional entertainment/shopping items sharing the same time slot
  // as another entry, keep only the first (primary) one in timeline view
  const seen = new Set();
  const deduped1 = entries.filter(e => {
    const slot = e.time.start + '-' + e.time.end;
    const name = e.name_base || e.title || e._label || '';
    const key = slot + ':' + e._type + ':' + name;
    if (e.optional && seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  // Cross-category dedup: same name_local on same day keeps highest-priority category only
  const typePriority = {transportation:0, meal:1, attraction:2, shopping:3, entertainment:4, accommodation:5, travel:6};
  const seenNames = {};
  const deduped = deduped1.filter(e => {
    const name = e.name_local || e.name_base || e.title || e._label || '';
    if (!name) return true;
    const prev = seenNames[name];
    if (!prev) { seenNames[name] = e; return true; }
    const prevP = typePriority[prev._type] ?? 99;
    const curP = typePriority[e._type] ?? 99;
    if (curP < prevP) { seenNames[name] = e; return true; }
    return false;
  });

  // Compute column layout for overlapping events
  const entriesWithLayout = computeColumnLayout(deduped);

  const firstH = entriesWithLayout.length ? (parseInt(entriesWithLayout[0].time.start) || 8) : 8;
  const lastH = entriesWithLayout.length
    ? Math.min(Math.max(...entriesWithLayout.map(e => parseInt(e.time.end) || (parseInt(e.time.start) + 1) || 9)), 24)
    : 20;
  const hours = []; for (let h = firstH; h <= lastH; h++) hours.push(h);

  const hH = sm ? 68 : 80;
  const typeStyle = {
    transportation: { bg: '#f0f9ff', border: '#7dd3fc', dot: '#0ea5e9' },
    meal: { bg: '#fffdf5', border: '#ebd984', dot: '#f0b429' },
    attraction: { bg: '#f6fafd', border: '#a8cceb', dot: '#4a90d9' },
    entertainment: { bg: '#faf6fd', border: '#c9aee6', dot: '#9b6dd7' },
    accommodation: { bg: '#f5fbf6', border: '#a2d9b1', dot: '#45b26b' },
    shopping: { bg: '#fff7f5', border: '#f0b29a', dot: '#e07c5a' },
    travel: { bg: '#f8f8f8', border: '#d0d0d0', dot: '#999' }
  };

  const top = (t) => { const [h, m] = t.split(':').map(Number); return Math.max(0, (h - firstH) * hH + (m / 60) * hH); };
  const rawHgt = (s, e) => top(e) - top(s);

  // Apple Calendar style: 10-minute minimum height for clickability
  // Activities < 10 min get fixed 24px height (clickable), >= 10 min scale proportionally
  const hgt = (s, e) => {
    const raw = rawHgt(s, e);
    const durationMin = (raw / hH) * 60;  // Convert to minutes

    // < 10 minutes: fixed minimum clickable height
    if (durationMin < 10) {
      return 24;  // Minimum clickable height (≈ 2 small text lines)
    }

    // >= 10 minutes: proportional height, but not smaller than 24px
    return Math.max(raw, 24);
  };

  // Apple Calendar style: Font scaling calculation
  const calculateFontScale = (height) => {
    const fullSizeThreshold = 52;  // Height for full two-row display

    if (height >= fullSizeThreshold) {
      return 1.0;  // 100% standard font
    }

    // Linear scaling: smooth transition from 52px to 24px
    const minHeight = 24;
    const scale = (height - 8) / (fullSizeThreshold - 8);  // 8px for padding

    // Minimum scale 0.57 (14px * 0.57 ≈ 8px, still readable)
    return Math.max(scale, 0.57);
  };

  // Debug: log entries count
  if (entriesWithLayout.length === 0) {
    console.warn('Timeline has no entries for day:', day.day, day.location_base);
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{
        width: '100%', height: sm ? '100px' : '160px',
        background: day.cover ? `url(${day.cover})` : '#f5f5f5',
        backgroundSize: 'cover', backgroundPosition: 'center'
      }} />

      <div style={{ padding: `0 ${px}` }}>
        <div style={{ marginTop: sm ? '-20px' : '-30px', marginBottom: '24px' }}>
          <div style={{ fontSize: sm ? '36px' : '48px', lineHeight: 1, marginBottom: '6px' }}>📍</div>
          <h2 style={{ fontSize: sm ? '22px' : '28px', fontWeight: '700', color: '#37352f', margin: 0 }}>
            {dayLabel(day, lang)}
          </h2>
        </div>

        {entriesWithLayout.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9b9a97' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏰</div>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>{L('no_timeline', lang)}</div>
            <div style={{ fontSize: '13px' }}>{L('no_timeline_sub', lang)}</div>
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

          <div style={{
            flex: 1,
            position: 'relative',
            borderLeft: '1px dashed #e5e4e1',
            minWidth: 0
          }}>
            {hours.map(h => <div key={h} style={{ height: hH, borderBottom: '1px solid #f5f5f3' }} />)}

            {entriesWithLayout.map((entry, i) => {
              const st = typeStyle[entry._type] || typeStyle.attraction;
              const t = top(entry.time.start);
              const entryH = hgt(entry.time.start, entry.time.end);

              // Column-based positioning for overlapping events
              const hasColumns = entry._maxColumns > 1;
              const colWidth = hasColumns ? (100 / entry._maxColumns) : 100;
              const colLeft = hasColumns ? (entry._column * colWidth) : 0;

              // Apple Calendar style: Calculate adaptive font scaling
              const fontScale = calculateFontScale(entryH);
              const baseTitleSize = sm ? 12 : 14;
              const baseTimeSize = 11;
              const baseDetailSize = 11;

              const titleFontSize = `${baseTitleSize * fontScale}px`;
              const timeFontSize = `${baseTimeSize * fontScale}px`;
              const detailFontSize = `${baseDetailSize * fontScale}px`;

              // Content display thresholds (based on scaled font)
              const showTitle = entryH >= 14;   // At least one line of title (14px * 0.57 ≈ 8px)
              const showTime = entryH >= 24;    // At least title + time (two lines)
              const showDetails = entryH >= 52; // Full height for details

              // Fix #6: Use dynamic z-index based on click state
              const isTop = topItemIndex === i;
              const zIdx = isTop ? 10 : 2;
              // Determine if this timeline entry corresponds to an editable slot
              const TIMELINE_SLOT_MAP = { meal: null, attraction: null, entertainment: null, accommodation: 'accommodation' };
              // For meal/activity entries, resolve the slot id from editorDay slot options
              let timelineSlotId = null;
              let timelineMatchedOptionId = null;
              if (entry._type === 'accommodation') {
                timelineSlotId = 'accommodation';
                // For accommodation, match against editorDay.accommodation.options
                if (editorDay && editorDay.accommodation && editorDay.accommodation.options) {
                  const accMatch = editorDay.accommodation.options.find(o => o.name === (entry.name_base || entry.name) || o.name_local === entry.name_local);
                  if (accMatch) timelineMatchedOptionId = accMatch.option_id;
                }
              } else if (editorDay && editorDay.slots) {
                // Try to match by name against slot options
                const actSlots = ['morning_activity', 'afternoon_activity', 'evening_activity'];
                const mealSlots = ['breakfast', 'lunch', 'dinner'];
                const checkSlots = entry._type === 'meal' ? mealSlots : actSlots;
                for (const slotId of checkSlots) {
                  const slot = editorDay.slots[slotId];
                  if (!slot || !slot.options) continue;
                  const match = slot.options.find(o => o.name === (entry.name_base || entry.name) || o.name_local === entry.name_local);
                  if (match) { timelineSlotId = slotId; timelineMatchedOptionId = match.option_id; break; }
                }
              }
              // Resolve selected option id for this slot (for draggable)
              const timelineSlotKey = timelineSlotId && day.day ? (day.day + ':' + timelineSlotId) : null;
              const timelineSlotEditorData = timelineSlotId && timelineSlotId !== 'accommodation' && editorDay && editorDay.slots && editorDay.slots[timelineSlotId];
              const timelineSelectedId = timelineSlotKey ? (
                timelineSlotId === 'accommodation'
                  ? (editorSelections && Object.prototype.hasOwnProperty.call(editorSelections, timelineSlotKey) ? editorSelections[timelineSlotKey] : (editorDay && editorDay.accommodation && editorDay.accommodation.selected_option_id))
                  : (editorSelections && Object.prototype.hasOwnProperty.call(editorSelections, timelineSlotKey) ? editorSelections[timelineSlotKey] : (timelineSlotEditorData && timelineSlotEditorData.selected_option_id))
              ) : null;
              // timelineIsSelected: only true if the specific matched option is the selected one
              const timelineIsSelected = !!(timelineMatchedOptionId && timelineMatchedOptionId === timelineSelectedId);
              return (
                <div key={i} style={{
                  position: 'absolute',
                  top: t,
                  left: hasColumns ? `calc(10px + ${colLeft}%)` : '10px',
                  width: hasColumns ? `calc(${colWidth}% - 12px)` : 'calc(100% - 20px)',
                  height: entryH - 4,
                  background: st.bg, borderLeft: `3px ${entry.optional ? 'dashed' : 'solid'} ${st.border}`,
                  borderRadius: '6px',
                  padding: sm ? '4px 6px' : '6px 8px',  // Smaller padding for scaled fonts
                  display: 'flex',
                  gap: '6px',
                  alignItems: 'flex-start',
                  boxShadow: isTop ? '0 4px 12px rgba(0,0,0,0.12)' : '0 1px 3px rgba(0,0,0,0.04)',
                  zIndex: zIdx, overflow: 'hidden', transition: 'all .15s', cursor: 'pointer'
                }}
                  draggable={!!(timelineSlotId && timelineIsSelected)}
                  onDragStart={timelineSlotId && timelineIsSelected ? (e) => { currentDragSlotId = timelineSlotId; e.dataTransfer.setData('text/plain', JSON.stringify({ slotId: timelineSlotId, optionId: timelineSelectedId, sourceSlotId: timelineSlotId, direction: 'board' })); e.dataTransfer.effectAllowed = 'move'; } : undefined}
                  onDragEnd={timelineSlotId && timelineIsSelected ? () => { currentDragSlotId = null; } : undefined}
                  onClick={(e) => {
                    setTopItemIndex(i);
                    // Tap-to-select: if pendingSelection set and this slot is valid, apply or reject (AC14/AC18)
                    if (pendingSelection && timelineSlotId) {
                      if (_isCompatible(pendingSelection.slotId, timelineSlotId)) {
                        if (window.applyEditorSelection) window.applyEditorSelection(pendingSelection.optionId, timelineSlotId, pendingSelection.originSlotId);
                      } else {
                        // Incompatible: show reject feedback, do not open details (AC18)
                        e.currentTarget.style.outline = '2px solid #e07c5a';
                        setTimeout(() => { if (e.currentTarget) e.currentTarget.style.outline = ''; }, 400);
                      }
                      return;
                    }
                    onItemClick && onItemClick(entry, entry._type);
                  }}
                  onMouseEnter={e => { if (!isTop) e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)'; }}
                  onMouseLeave={e => { if (!isTop) e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04)'; }}
                >
                  <div style={{
                    position: 'absolute', left: '-8px', top: '50%', transform: 'translateY(-50%)',
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: st.dot, border: '2px solid #fff'
                  }} />

                  {/* Apple Calendar style: Image only for full-height entries */}
                  {entry.image && !sm && showDetails && (
                    <div style={{ width: '50px', height: '50px', borderRadius: '6px', overflow: 'hidden', flexShrink: 0 }}>
                      <img src={entry.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                  )}

                  <div style={{ flex: 1, minWidth: 0 }}>
                    {/* Time row (>= 24px) */}
                    {showTime && (
                      <div style={{ fontSize: timeFontSize, color: '#b4b4b4', lineHeight: 1.2 }}>
                        {entry.time.start} – {entry.time.end}
                      </div>
                    )}

                    {/* Title row (>= 14px) */}
                    {showTitle && (
                      <div style={{
                        fontSize: titleFontSize,
                        fontWeight: '600',
                        color: '#37352f',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        lineHeight: 1.2
                      }}>
                        {entry._type === 'transportation' || entry._type === 'travel' ? (
                          <span>{entry._type === 'transportation' ? entry.icon : (entry.icon || '🚶')} {entry._label}{entry.duration ? ` (${entry.duration})` : ''}</span>
                        ) : (
                          <span>{entry._label}: {getDisplayName(entry, lang)}</span>
                        )}
                        {entry.optional && showDetails && (
                          <span style={{
                            fontSize: `${9 * fontScale}px`,
                            padding: '1px 4px',
                            background: '#f5f5f3',
                            borderRadius: '3px',
                            color: '#9b9a97',
                            marginLeft: '4px',
                            verticalAlign: 'middle'
                          }}>
                            {L('optional', lang)}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Details row (>= 52px) */}
                    {showDetails && (entry._type === 'transportation' ? (
                      <div style={{ fontSize: detailFontSize, color: '#9b9a97', marginTop: '2px', lineHeight: 1.3 }}>
                        <div>{lang === 'local' && entry.departure_point_local ? entry.departure_point_local : entry.departure_point_base} → {lang === 'local' && entry.arrival_point_local ? entry.arrival_point_local : entry.arrival_point_base}</div>
                        {entry.route_number && entry.route_number !== 'VERIFIED' && (
                          <div>{lang === 'local' && entry.type_local ? entry.type_local : entry.type_base} {entry.route_number}</div>
                        )}
                        {entry.status_base && (
                          <span style={{
                            display: 'inline-block',
                            marginTop: '2px',
                            padding: '2px 4px',
                            borderRadius: '3px',
                            fontSize: `${9 * fontScale}px`,
                            fontWeight: '600',
                            background: entry.status_base?.includes('URGENT') ? '#fff4e6' :
                                       entry.status_base?.includes('VERIFIED') ? '#e9f5ec' : '#edf2fc',
                            color: entry.status_base?.includes('URGENT') ? '#d97706' :
                                  entry.status_base?.includes('VERIFIED') ? '#1a7a32' : '#2b63b5'
                          }}>
                            {lang === 'local' && entry.status_local ? entry.status_local : entry.status_base}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: detailFontSize, color: '#9b9a97', flexWrap: 'wrap', marginTop: '2px', lineHeight: 1.3 }}>
                        {entry.recommended_duration && <span>⏱ {entry.recommended_duration}</span>}
                        {entry.cost !== undefined && Number(entry.cost) > 0 && (
                          <span style={{
                            padding: '1px 4px', borderRadius: '3px', fontWeight: '600',
                            background: '#f5f5f3',
                            color: '#37352f'
                          }}>
                            {fmtCost(entry.cost, undefined, lang)}
                          </span>
                        )}
                        {entry.stars > 0 && <span style={{ color: '#e9b200' }}>{'★'.repeat(entry.stars)}</span>}
                      </div>
                    ))}
                    {showDetails && entry._type !== 'transportation' && <LinksRow links={entry.links} compact={sm} />}
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
// EDITOR HELPERS (always active — unified viewer/editor page)
// ============================================================

// Finding 8: adapt v2 option fields for CandidatesSidebar card display
function adaptV2Option(opt) {
  return {
    ...opt,
    name_base: opt.name,
    name_local: opt.name_local || '',
    location_base: opt.location_summary || '',
    cost_display: opt.cost ? Math.round(opt.cost) + ' CNY' : '',
  };
}

// R1 v3 — locate a v2 option object for a given slot+selectedId across
// precedence: (1) target slot options, (2) same-day cross-slot, (3) cross-day fallback.
// Returns null if not found. Preserves slot/day context (NOT a flat map).
function findSelectedOption(editorDay, slotId, selectedId, editorTripData) {
  if (!selectedId) return null;
  // 1. Target slot
  const tgt = editorDay && editorDay.slots && editorDay.slots[slotId];
  if (tgt && tgt.options) {
    const hit = tgt.options.find(o => o.option_id === selectedId);
    if (hit) return hit;
  }
  // 2. Same-day cross-slot
  if (editorDay && editorDay.slots) {
    for (const sKey of Object.keys(editorDay.slots)) {
      if (sKey === slotId) continue;
      const s = editorDay.slots[sKey];
      if (!s || !s.options) continue;
      const hit = s.options.find(o => o.option_id === selectedId);
      if (hit) return hit;
    }
  }
  // 3. Cross-day fallback (editorTripData.days[*])
  if (editorTripData && editorTripData.days) {
    for (const d of editorTripData.days) {
      if (!d || !d.slots) continue;
      for (const sKey of Object.keys(d.slots)) {
        const s = d.slots[sKey];
        if (!s || !s.options) continue;
        const hit = s.options.find(o => o.option_id === selectedId);
        if (hit) return hit;
      }
    }
  }
  return null;
}

// R1c v3 — locate a v2 accommodation option across editorDay then cross-day fallback.
function findSelectedAccommodationOption(editorDay, editorTripData, selectedId) {
  if (!selectedId) return null;
  const acc = editorDay && editorDay.accommodation;
  if (acc && acc.options) {
    const hit = acc.options.find(o => o.option_id === selectedId);
    if (hit) return hit;
  }
  if (editorTripData && editorTripData.days) {
    for (const d of editorTripData.days) {
      const a = d && d.accommodation;
      if (!a || !a.options) continue;
      const hit = a.options.find(o => o.option_id === selectedId);
      if (hit) return hit;
    }
  }
  return null;
}

// R1 v3 synthesis helper — map a v2 option into PLAN card shape.
// RC-12: NEVER write numeric cost = opt.cost (that is raw CNY, not display currency).
// Emit cost = 0 and cost_display = "<int> CNY" string instead; render path falls back.
function _synthesizeCardFromV2Option(opt, existingCard) {
  const base = existingCard ? { ...existingCard } : {};
  base.name_base = opt.name || base.name_base;
  base.name_local = opt.name_local || base.name_local || '';
  if (opt.location_summary) base.location_base = opt.location_summary;
  if (opt.location_local) base.location_local = opt.location_local;
  base.image = opt.cover_image || opt.image || base.image || null;
  // Time: preserve existing card's time if v2 omits (TimelineView filters 00:00)
  if (opt.time && opt.time.start && opt.time.start !== '00:00') base.time = opt.time;
  // notes
  if (opt.notes_base) base.notes_base = opt.notes_base;
  if (opt.notes_local) base.notes_local = opt.notes_local;
  // RC-12 cost rule: numeric cost stays 0 (gated out); cost_display is a STRING with explicit suffix
  base.cost = 0;
  if (opt.cost && opt.cost > 0) {
    base.cost_display = Math.round(opt.cost) + ' ' + (opt.currency_local || 'CNY');
  } else {
    base.cost_display = '';
  }
  base.option_id = opt.option_id;
  base.selected = true;
  return base;
}

// R1 v3 — match an existing card against a v2 option by option_id OR name.
function _matchesOption(card, opt) {
  if (!card || !opt) return false;
  if (card.option_id && opt.option_id && card.option_id === opt.option_id) return true;
  if (card.name_base && opt.name && card.name_base === opt.name) return true;
  if (card.name_local && opt.name_local && card.name_local === opt.name_local) return true;
  return false;
}

// Finding 10 / R1 v3: merge persisted + local selections into a cloned publishedDay
// REPLACES rendered slot card content for the selected option using the
// precedence: (1) active PLAN card match, (2) PLAN alternative match (promote), (3) v2 synthesis.
// 4-arg signature: needs editorTripData for cross-day fallback per RC-3.
function mergeEditorSelectionsIntoPublishedDay(publishedDay, editorDay, editorSelections, editorTripData) {
  if (!publishedDay || !editorDay) return publishedDay;
  const day = JSON.parse(JSON.stringify(publishedDay)); // deep clone
  editorSelections = editorSelections || {};

  // ===== Accommodation (R1c): treat as object (NOT array). =====
  const accKey = publishedDay.day + ':accommodation';
  const persistedAccId = editorDay.accommodation && editorDay.accommodation.selected_option_id;
  const selectedAccId = Object.prototype.hasOwnProperty.call(editorSelections, accKey)
    ? editorSelections[accKey]
    : persistedAccId;
  if (selectedAccId) {
    const selAccOpt = findSelectedAccommodationOption(editorDay, editorTripData, selectedAccId);
    if (selAccOpt && day.accommodation && typeof day.accommodation === 'object' && !Array.isArray(day.accommodation)) {
      if (_matchesOption(day.accommodation, selAccOpt)) {
        day.accommodation.selected = true;
        day.accommodation.option_id = selAccOpt.option_id;
      } else {
        // Synthesis: overwrite fields on the existing accommodation object
        const synth = _synthesizeCardFromV2Option(selAccOpt, day.accommodation);
        // Preserve a few PLAN-only fields that synthesis would not produce
        synth.check_in = day.accommodation.check_in || synth.check_in;
        synth.check_out = day.accommodation.check_out || synth.check_out;
        synth.stars = (selAccOpt.stars !== undefined ? selAccOpt.stars : day.accommodation.stars) || 0;
        day.accommodation = synth;
      }
      const coverImg = selAccOpt.cover_image || selAccOpt.image;
      if (coverImg) day.cover = coverImg;
    }
  }

  // ===== Meals (R1, R1a) =====
  const mealSlots = ['breakfast', 'lunch', 'dinner'];
  mealSlots.forEach(slotId => {
    const key = publishedDay.day + ':' + slotId;
    const persistedId = editorDay.slots && editorDay.slots[slotId] && editorDay.slots[slotId].selected_option_id;
    const selectedId = Object.prototype.hasOwnProperty.call(editorSelections, key)
      ? editorSelections[key]
      : persistedId;
    if (!selectedId) return;
    const selOpt = findSelectedOption(editorDay, slotId, selectedId, editorTripData);
    if (!selOpt) return;

    if (!day.meals) day.meals = {};
    const activeCard = day.meals[slotId];

    // Step 1: active PLAN card matches → mutate in place
    if (activeCard && _matchesOption(activeCard, selOpt)) {
      activeCard.selected = true;
      activeCard.option_id = selOpt.option_id;
    } else {
      // Step 2: PLAN alternative match → promote alternative into slot
      const alts = (day.meal_alternatives && day.meal_alternatives[slotId]) || [];
      const altIdx = alts.findIndex(a => _matchesOption(a, selOpt));
      if (altIdx >= 0) {
        const promoted = alts[altIdx];
        promoted.selected = true;
        promoted.option_id = selOpt.option_id;
        // Preserve target-slot time when promoted alternative has no time
        if ((!promoted.time || promoted.time.start === '00:00') && activeCard && activeCard.time) {
          promoted.time = activeCard.time;
        }
        // Swap: move old primary into the alternatives slot to preserve visible card count
        const newAlts = alts.slice();
        newAlts.splice(altIdx, 1);
        if (activeCard) {
          // Demote old primary (clear selected/option_id flags that pertained to it being primary)
          const demoted = { ...activeCard };
          demoted.selected = false;
          newAlts.push(demoted);
        }
        if (!day.meal_alternatives) day.meal_alternatives = {};
        day.meal_alternatives[slotId] = newAlts;
        day.meals[slotId] = promoted;
      } else {
        // Step 3: synthesis fallback (cross-meal injection — no PLAN alternative exists)
        const synth = _synthesizeCardFromV2Option(selOpt, activeCard || {});
        day.meals[slotId] = synth;
        // R1a: filter the selected option out of meal_alternatives by option_id/name
        if (day.meal_alternatives && day.meal_alternatives[slotId]) {
          day.meal_alternatives[slotId] = day.meal_alternatives[slotId].filter(a => !_matchesOption(a, selOpt));
        }
      }
    }
    // R1a (always): ensure no duplicate of the selected option remains in alternatives
    if (day.meal_alternatives && day.meal_alternatives[slotId]) {
      day.meal_alternatives[slotId] = day.meal_alternatives[slotId].filter(a => {
        // keep cards that don't match the selected option
        if (_matchesOption(a, selOpt)) return false;
        return true;
      });
    }
  });

  // ===== Activities (R1b) =====
  const actSlots = ['morning_activity', 'afternoon_activity', 'evening_activity'];
  const actArrays = ['attractions', 'entertainment', 'cafe', 'unscheduled_optionals'];
  actSlots.forEach(slotId => {
    const key = publishedDay.day + ':' + slotId;
    const persistedId = editorDay.slots && editorDay.slots[slotId] && editorDay.slots[slotId].selected_option_id;
    const selectedId = Object.prototype.hasOwnProperty.call(editorSelections, key)
      ? editorSelections[key]
      : persistedId;
    if (!selectedId) return;
    const selOpt = findSelectedOption(editorDay, slotId, selectedId, editorTripData);
    if (!selOpt) return;
    // Find existing anchor card across all four arrays.
    // Prefer (a) an anchor that matches the selected option, (b) a timed anchor whose name appears
    // in editorDay.slots[slotId].options[*] (the slot's option universe), prefer timed.
    const slotOpts = (editorDay.slots && editorDay.slots[slotId] && editorDay.slots[slotId].options) || [];
    const slotOptionNames = new Set();
    slotOpts.forEach(o => {
      if (o.name) slotOptionNames.add(o.name);
      if (o.name_local) slotOptionNames.add(o.name_local);
    });

    let anchorArr = null;
    let anchorIdx = -1;
    // First pass: card that already matches the selected option directly
    for (const arr of actArrays) {
      if (!day[arr]) continue;
      const idx = day[arr].findIndex(c => _matchesOption(c, selOpt));
      if (idx >= 0) { anchorArr = arr; anchorIdx = idx; break; }
    }
    // Second pass: any card whose name is in the slot's option universe; prefer timed
    if (anchorArr === null) {
      let timedHit = null;
      let untimedHit = null;
      for (const arr of actArrays) {
        if (!day[arr]) continue;
        for (let i = 0; i < day[arr].length; i++) {
          const c = day[arr][i];
          const nm = c.name_base;
          const nl = c.name_local;
          if ((nm && slotOptionNames.has(nm)) || (nl && slotOptionNames.has(nl))) {
            if (c.time && c.time.start && c.time.start !== '00:00') {
              if (!timedHit) timedHit = { arr, i };
            } else if (!untimedHit) {
              untimedHit = { arr, i };
            }
          }
        }
      }
      const hit = timedHit || untimedHit;
      if (hit) { anchorArr = hit.arr; anchorIdx = hit.i; }
    }
    if (anchorArr === null) return; // No anchor — synthesis-into-arbitrary-array is out of scope per codex Q3

    const existing = day[anchorArr][anchorIdx];
    if (_matchesOption(existing, selOpt)) {
      // PLAN card already matches → mutate
      existing.selected = true;
      existing.option_id = selOpt.option_id;
    } else {
      // Replace anchor in place; preserve anchor time
      const synth = _synthesizeCardFromV2Option(selOpt, existing);
      if (existing.time) synth.time = existing.time;
      day[anchorArr][anchorIdx] = synth;
    }
    // R1b: remove OTHER appearances of the selected option_id/name across all four arrays
    for (const arr of actArrays) {
      if (!day[arr]) continue;
      day[arr] = day[arr].filter((c, i) => {
        if (arr === anchorArr && i === anchorIdx) return true;
        return !_matchesOption(c, selOpt);
      });
    }
  });

  return day;
}

// Module-level drag state for onDragOver compatibility gate (AC18/FIX3)
let currentDragSlotId = null;

// _isCompatible: meal slots are mutually compatible; non-meal require exact match (M18)
const MEAL_SLOTS = new Set(['breakfast', 'lunch', 'dinner', 'meals-any']);
function _isCompatible(srcSlotId, tgtSlotId) {
  if (MEAL_SLOTS.has(srcSlotId) && MEAL_SLOTS.has(tgtSlotId)) return true;
  return srcSlotId === tgtSlotId;
}

// R3 / AC11 v3 — codex F9: success flash on the stable slot card (which survives
// React commits), not the .slot-drop overlay (which may unmount). 600 ms window.
function _flashSuccess(slotId) {
  if (typeof document === 'undefined' || !slotId) return;
  // querySelectorAll covers both Kanban primary card and Timeline entry
  const els = document.querySelectorAll('[data-slot-card="primary"][data-slot-id="' + slotId + '"], [data-timeline-entry][data-slot-id="' + slotId + '"]');
  els.forEach(el => {
    el.setAttribute('data-drop-success', '');
    setTimeout(() => { try { el.removeAttribute('data-drop-success'); } catch (_) {} }, 600);
  });
}

// CandidatesSidebar component: fixed right panel (always active)
const CandidatesSidebar = ({ editorTripData, publishedDay, lang, editorSelections, saveMutations,
    setEditorSelections, editorDay, pendingSelection, setPendingSelection, setEditorTripData, inlineMode }) => {
  if (!editorTripData) return (
    <div id="candidates-groups" style={{
      position: inlineMode ? 'static' : 'fixed', right: 0, top: 0, bottom: 0, width: inlineMode ? '100%' : '300px',
      overflowY: 'auto', background: 'white',
      borderLeft: inlineMode ? 'none' : '1px solid #e5e7eb', zIndex: inlineMode ? undefined : 100,
      fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif",
      padding: '16px 12px'
    }}>
      <div style={{ fontSize: '12px', color: '#9b9a97' }}>Loading candidates…</div>
    </div>
  );

  const resolveSelectionLocal = (key, publishedId) => {
    if (Object.prototype.hasOwnProperty.call(editorSelections || {}, key)) {
      return (editorSelections || {})[key];
    }
    return publishedId;
  };

  const dayNum = publishedDay && publishedDay.day;
  const slots = editorDay && editorDay.slots;

  if (!slots) return (
    <div id="candidates-groups" style={{
      position: inlineMode ? 'static' : 'fixed', right: 0, top: 0, bottom: 0, width: inlineMode ? '100%' : '300px',
      overflowY: 'auto', background: 'white',
      borderLeft: inlineMode ? 'none' : '1px solid #e5e7eb', zIndex: inlineMode ? undefined : 100,
      fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif",
      padding: '16px 12px'
    }}>
      <div style={{ fontSize: '12px', color: '#9b9a97' }}>No candidates for this day.</div>
    </div>
  );

  const slotLabels = {
    breakfast: '早餐 / Breakfast', lunch: '午餐 / Lunch', dinner: '晚餐 / Dinner',
    morning_activity: '上午 / Morning', afternoon_activity: '下午 / Afternoon',
    evening_activity: '晚上 / Evening',
  };

  // Build unified Meals group (M19): dedup breakfast/lunch/dinner options by option_id
  const mealSlotIds = ['breakfast', 'lunch', 'dinner'];
  const mealsGroup = [];
  const seenMealIds = new Set();
  mealSlotIds.forEach(slotId => {
    const slot = slots[slotId];
    if (!slot || !slot.options) return;
    slot.options.forEach(rawOpt => {
      if (seenMealIds.has(rawOpt.option_id)) return;
      seenMealIds.add(rawOpt.option_id);
      mealsGroup.push({ ...rawOpt, _originSlotId: slotId });
    });
  });

  // Check if a meal card is selected across breakfast/lunch/dinner
  const isMealSelected = (optionId) => {
    return mealSlotIds.some(slotId => {
      const slot = slots[slotId];
      const key = dayNum + ':' + slotId;
      const resolved = resolveSelectionLocal(key, slot && slot.selected_option_id);
      return resolved === optionId;
    });
  };

  // Non-meal slots
  const activitySlots = ['morning_activity', 'afternoon_activity', 'evening_activity'];

  // Drop handler: drop from CandidatesSidebar or board onto CandidatesSidebar = deselect (M17b)
  const handleSidebarDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const payload = JSON.parse(e.dataTransfer.getData('text/plain'));
      const srcSlotId = payload.sourceSlotId || payload.slotId;
      // board card dropped onto sidebar → deselect from source slot
      if ((payload.direction === 'plan-to-candidates' || payload.direction === 'board') && srcSlotId) {
        const key = dayNum + ':' + srcSlotId;
        setEditorSelections(prev => ({ ...prev, [key]: null }));
        saveMutations(dayNum, [{ type: 'select', slot: srcSlotId, option_id: null }]);
      }
    } catch (_) {}
  };

  // Apply selection from candidate tap/drop
  const applySelection = (optionId, targetSlotId, originSlotId) => {
    const key = dayNum + ':' + targetSlotId;
    // Cross-meal copy (M20): if meal option absent from target slot options, copy it
    if (MEAL_SLOTS.has(targetSlotId) && targetSlotId !== 'meals-any' && setEditorTripData) {
      setEditorTripData(prev => {
        if (!prev) return prev;
        const updated = JSON.parse(JSON.stringify(prev));
        const dayEntry = updated.days && updated.days.find(d => Number(d.day) === Number(dayNum));
        if (!dayEntry || !dayEntry.slots) return prev;
        const tgtSlot = dayEntry.slots[targetSlotId];
        if (!tgtSlot) return prev;
        if (!tgtSlot.options) tgtSlot.options = [];
        const alreadyThere = tgtSlot.options.some(o => o.option_id === optionId);
        if (!alreadyThere && originSlotId && originSlotId !== 'meals-any') {
          const srcSlot = dayEntry.slots[originSlotId];
          if (srcSlot && srcSlot.options) {
            const srcOpt = srcSlot.options.find(o => o.option_id === optionId);
            if (srcOpt) tgtSlot.options.push({ ...srcOpt });
          }
        }
        return updated;
      });
    }
    setEditorSelections(prev => ({ ...prev, [key]: optionId }));
    const mutations = [{ type: 'select', slot: targetSlotId, option_id: optionId, origin_slot_id: originSlotId || null }];
    saveMutations(dayNum, mutations);
    setPendingSelection && setPendingSelection(null);
  };

  const containerStyle = {
    position: inlineMode ? 'static' : 'fixed', right: 0, top: 0, bottom: 0, width: inlineMode ? '100%' : '300px',
    overflowY: 'auto', background: 'white',
    borderLeft: inlineMode ? 'none' : '1px solid #e5e7eb', zIndex: inlineMode ? undefined : 100,
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif",
  };

  return (
    <div id="candidates-groups" style={containerStyle}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleSidebarDrop}
    >
      <div style={{ padding: '12px 12px 4px', borderBottom: '1px solid #f0efed', fontSize: '13px', fontWeight: '600', color: '#37352f', position: inlineMode ? 'static' : 'sticky', top: 0, background: 'white', zIndex: 1 }}>
        Candidates — Day {dayNum}
      </div>

      {/* Accommodation group (AC15/FIX5): show accommodation options so user can select */}
      {editorDay && editorDay.accommodation && editorDay.accommodation.options && editorDay.accommodation.options.length > 0 && (() => {
        const accKey = dayNum + ':accommodation';
        const selectedAccId = resolveSelectionLocal(accKey, editorDay.accommodation.selected_option_id);
        return (
          <div style={{ padding: '8px 12px' }}>
            <div style={{ fontSize: '10px', fontWeight: '700', color: '#9b9a97', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
              住宿 / Accommodation
            </div>
            {editorDay.accommodation.options.map((rawOpt, oi) => {
              const opt = adaptV2Option(rawOpt);
              const isSelected = selectedAccId === rawOpt.option_id;
              const isPending = pendingSelection && pendingSelection.optionId === rawOpt.option_id && pendingSelection.slotId === 'accommodation';
              return (
                <div key={rawOpt.option_id || oi} className="card-candidate"
                  draggable={true}
                  data-option-id={rawOpt.option_id}
                  data-slot-id="accommodation"
                  data-origin-slot-id="accommodation"
                  onDragStart={(e) => {
                    currentDragSlotId = 'accommodation';
                    e.dataTransfer.setData('text/plain', JSON.stringify({ optionId: rawOpt.option_id, slotId: 'accommodation', originSlotId: 'accommodation' }));
                    e.dataTransfer.effectAllowed = 'move';
                  }}
                  onDragEnd={() => { currentDragSlotId = null; }}
                  onClick={() => {
                    if (isPending) { setPendingSelection && setPendingSelection(null); return; }
                    setPendingSelection && setPendingSelection({ optionId: rawOpt.option_id, slotId: 'accommodation', originSlotId: 'accommodation' });
                  }}
                  style={{
                    background: isPending ? '#e6f3ff' : isSelected ? '#e9f5ec' : '#fafafa',
                    borderRadius: '6px',
                    border: '1px solid ' + (isPending ? '#0085fe' : isSelected ? '#45b26b' : '#e5e7eb'),
                    padding: '8px 10px', marginBottom: '6px', cursor: 'grab', fontSize: '12px',
                    userSelect: 'none', position: 'relative'
                  }}
                >
                  {isSelected && <span style={{ position: 'absolute', top: '6px', right: '8px', color: '#45b26b', fontWeight: '700', fontSize: '13px' }}>✓</span>}
                  {(rawOpt.cover_image || rawOpt.image) && (
                    <div style={{ width: '100%', height: '60px', borderRadius: '4px', overflow: 'hidden', marginBottom: '6px' }}>
                      <img src={rawOpt.cover_image || rawOpt.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                  )}
                  <div style={{ fontWeight: '600', color: '#37352f', marginBottom: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: isSelected ? '16px' : 0 }}>
                    {lang === 'local' ? (opt.name_local || opt.name_base) : opt.name_base}
                  </div>
                  {opt.location_base && <div style={{ fontSize: '11px', color: '#9b9a97', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{opt.location_base}</div>}
                  {opt.cost_display && <div style={{ fontSize: '11px', color: '#6b6b6b' }}>{opt.cost_display}</div>}
                </div>
              );
            })}
          </div>
        );
      })()}

      {/* Unified Meals group (M19) */}
      {mealsGroup.length > 0 && (
        <div style={{ padding: '8px 12px' }}>
          <div style={{ fontSize: '10px', fontWeight: '700', color: '#9b9a97', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
            餐饮 / Meals
          </div>
          {mealsGroup.map((rawOpt, oi) => {
            const opt = adaptV2Option(rawOpt);
            const isSelected = isMealSelected(rawOpt.option_id);
            const isPending = pendingSelection && pendingSelection.optionId === rawOpt.option_id;
            return (
              <div key={rawOpt.option_id || oi} className="card-candidate"
                draggable={true}
                data-option-id={rawOpt.option_id}
                data-slot-id="meals-any"
                data-origin-slot-id={rawOpt._originSlotId}
                onDragStart={(e) => {
                  currentDragSlotId = 'meals-any';
                  e.dataTransfer.setData('text/plain', JSON.stringify({
                    optionId: rawOpt.option_id, slotId: 'meals-any',
                    originSlotId: rawOpt._originSlotId
                  }));
                  e.dataTransfer.effectAllowed = 'move';
                }}
                onDragEnd={() => { currentDragSlotId = null; }}
                onClick={() => {
                  if (isPending) { setPendingSelection && setPendingSelection(null); return; }
                  setPendingSelection && setPendingSelection({ optionId: rawOpt.option_id, slotId: 'meals-any', originSlotId: rawOpt._originSlotId });
                }}
                style={{
                  background: isPending ? '#e6f3ff' : isSelected ? '#e9f5ec' : '#fafafa',
                  borderRadius: '6px',
                  border: '1px solid ' + (isPending ? '#0085fe' : isSelected ? '#45b26b' : '#e5e7eb'),
                  padding: '8px 10px', marginBottom: '6px', cursor: 'grab', fontSize: '12px',
                  userSelect: 'none', position: 'relative'
                }}
              >
                {isSelected && <span style={{ position: 'absolute', top: '6px', right: '8px', color: '#45b26b', fontWeight: '700', fontSize: '13px' }}>✓</span>}
                <div style={{ fontWeight: '600', color: '#37352f', marginBottom: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: isSelected ? '16px' : 0 }}>
                  {lang === 'local' ? (opt.name_local || opt.name_base) : opt.name_base}
                </div>
                {opt.location_base && <div style={{ fontSize: '11px', color: '#9b9a97', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{opt.location_base}</div>}
                {opt.cost_display && <div style={{ fontSize: '11px', color: '#6b6b6b' }}>{opt.cost_display}</div>}
              </div>
            );
          })}
        </div>
      )}

      {/* Activity slots */}
      {activitySlots.map(slotId => {
        const slot = slots[slotId];
        if (!slot || !slot.options || slot.options.length === 0) return null;
        const key = dayNum + ':' + slotId;
        const selectedId = resolveSelectionLocal(key, slot.selected_option_id);
        return (
          <div key={slotId} style={{ padding: '8px 12px' }}>
            <div style={{ fontSize: '10px', fontWeight: '700', color: '#9b9a97', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
              {slotLabels[slotId] || slotId}
            </div>
            {slot.options.map((rawOpt, oi) => {
              const opt = adaptV2Option(rawOpt);
              const isSelected = selectedId === rawOpt.option_id;
              const isPending = pendingSelection && pendingSelection.optionId === rawOpt.option_id && pendingSelection.slotId === slotId;
              return (
                <div key={rawOpt.option_id || oi} className="card-candidate"
                  draggable={true}
                  data-option-id={rawOpt.option_id}
                  data-slot-id={slotId}
                  data-origin-slot-id={slotId}
                  onDragStart={(e) => {
                    currentDragSlotId = slotId;
                    e.dataTransfer.setData('text/plain', JSON.stringify({ optionId: rawOpt.option_id, slotId: slotId, originSlotId: slotId }));
                    e.dataTransfer.effectAllowed = 'move';
                  }}
                  onDragEnd={() => { currentDragSlotId = null; }}
                  onClick={() => {
                    if (isPending) { setPendingSelection && setPendingSelection(null); return; }
                    setPendingSelection && setPendingSelection({ optionId: rawOpt.option_id, slotId: slotId, originSlotId: slotId });
                  }}
                  style={{
                    background: isPending ? '#e6f3ff' : isSelected ? '#e9f5ec' : '#fafafa',
                    borderRadius: '6px',
                    border: '1px solid ' + (isPending ? '#0085fe' : isSelected ? '#45b26b' : '#e5e7eb'),
                    padding: '8px 10px', marginBottom: '6px', cursor: 'grab', fontSize: '12px',
                    userSelect: 'none', position: 'relative'
                  }}
                >
                  {isSelected && <span style={{ position: 'absolute', top: '6px', right: '8px', color: '#45b26b', fontWeight: '700', fontSize: '13px' }}>✓</span>}
                  <div style={{ fontWeight: '600', color: '#37352f', marginBottom: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: isSelected ? '16px' : 0 }}>
                    {lang === 'local' ? (opt.name_local || opt.name_base) : opt.name_base}
                  </div>
                  {opt.location_base && <div style={{ fontSize: '11px', color: '#9b9a97', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{opt.location_base}</div>}
                  {opt.cost_display && <div style={{ fontSize: '11px', color: '#6b6b6b' }}>{opt.cost_display}</div>}
                </div>
              );
            })}
          </div>
        );
      })}
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
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedBudgetCat, setSelectedBudgetCat] = useState(null);
  // Root cause fix (commit 8f2bddd): Add language toggle for bilingual POI display
  const [lang, setLang] = useState('local');  // 'local' or 'base'
  const [mapProvider, setMapProvider] = useState('gaode');  // 'gaode' or 'google'
  // Editor state (always active — unified viewer/editor page)
  const [editorTripData, setEditorTripData] = useState(null);
  const [editorSelections, setEditorSelections] = useState({});
  const [editorSession] = useState(() => (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)));
  const [saveState, setSaveState] = useState('idle'); // 'idle'|'saving'|'saved'|'error'
  const [lastSaveTs, setLastSaveTs] = useState(null);
  const [isOffline, setIsOffline] = useState(() => !navigator.onLine);
  const [conflictDetected, setConflictDetected] = useState(false);
  const [isMobileLayout, setIsMobileLayout] = useState(() => window.innerWidth < 768);
  const [mobileTab, setMobileTab] = useState('kanban'); // 'kanban'|'timeline'|'candidates'
  const [pendingSelection, setPendingSelection] = useState(null); // {optionId, slotId, originSlotId} for tap-to-select
  const [routeCache, setRouteCache] = useState({}); // {pairKey: {status, duration_minutes}} for route gaps (AC12/AC23)
  const routeSeqRef = React.useRef({}); // per-pair monotonic seq for stale-response guard
  const saveSeqRef = React.useRef(0);    // monotonic counter for saveMutations only
  const budgetSeqRef = React.useRef({}); // per-day counters for recomputeBudget
  const saveStateRef = React.useRef('idle');
  const lastSaveTsRef = React.useRef(null);
  const [saveStatusText, setSaveStatusText] = useState('');
  const bp = useBreakpoint();
  const sm = bp === 'sm';

  const trip = PLAN_DATA.trips[selTrip];
  const publishedDay = trip?.days?.[selDay];

  // Resolve editorDay using absolute day number from PLAN_DATA
  const editorDay = useMemo(() => {
    if (!editorTripData) return null;
    return editorTripData.days && editorTripData.days.find(
      d => Number(d.day) === Number(publishedDay && publishedDay.day)
    ) || null;
  }, [editorTripData, publishedDay]);

  // effectiveDay merges editor selections into published day for both views
  // R1 v3: 4-arg signature — editorTripData required for cross-day option fallback.
  const effectiveDay = useMemo(() => {
    if (!editorDay) return publishedDay;
    return mergeEditorSelectionsIntoPublishedDay(publishedDay, editorDay, editorSelections, editorTripData);
  }, [publishedDay, editorDay, editorSelections, editorTripData]);

  // Fetch v2 trip data for CandidatesSidebar candidates (only when TRIP_ID is set)
  useEffect(() => {
    if (!TRIP_ID) return;
    fetch('/api/trip/' + encodeURIComponent(TRIP_ID))
      .then(r => r.json())
      .then(data => setEditorTripData(data))
      .catch(() => {});
  }, [TRIP_ID]);

  // Shared selection resolver — key-presence semantics (AC10)
  const resolveSelection = useCallback((selections, key, publishedId) => {
    if (Object.prototype.hasOwnProperty.call(selections, key)) {
      return selections[key]; // null = explicitly cleared
    }
    return publishedId;
  }, []);

  // Online/offline detection (M6, M28)
  useEffect(() => {
    const goOnline = () => setIsOffline(false);
    const goOffline = () => setIsOffline(true);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  // Mobile layout resize listener (M12)
  useEffect(() => {
    const h = () => setIsMobileLayout(window.innerWidth < 768);
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);

  // Save status auto-refresh every 15s (M27)
  useEffect(() => {
    const interval = setInterval(() => {
      const st = saveStateRef.current;
      const ts = lastSaveTsRef.current;
      if (st === 'saved' && ts) {
        const elapsed = Math.floor((Date.now() - ts) / 1000);
        setSaveStatusText('saved ' + elapsed + 's ago');
      }
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  // Keep refs in sync for setInterval stale-closure avoidance
  useEffect(() => { saveStateRef.current = saveState; }, [saveState]);
  useEffect(() => { lastSaveTsRef.current = lastSaveTs; }, [lastSaveTs]);

  // Budget recompute helper
  const recomputeBudget = useCallback((dayNum) => {
    if (!TRIP_ID) return;
    const seq = (budgetSeqRef.current[dayNum] || 0) + 1;
    budgetSeqRef.current[dayNum] = seq;
    fetch('/api/budget/recompute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trip_id: TRIP_ID, day: dayNum }),
    })
      .then(r => r.json())
      .then(resp => {
        if (budgetSeqRef.current[dayNum] !== seq) return; // stale
        const entry = resp.days && resp.days.find(d => d.day === dayNum);
        if (entry && entry.day_total !== undefined) {
          // Budget total update is displayed via a separate state
          setLiveDayTotal(prev => ({ ...prev, [dayNum]: entry.day_total }));
        }
      })
      .catch(() => {});
  }, []);

  const [liveDayTotal, setLiveDayTotal] = useState({});

  // fetchRoute: POST /api/route for a pair of consecutive filled slots (AC12/AC23)
  const fetchRoute = useCallback((fromOptionId, toOptionId, pairKey) => {
    if (!TRIP_ID || !fromOptionId || !toOptionId) return;
    routeSeqRef.current[pairKey] = (routeSeqRef.current[pairKey] || 0) + 1;
    const seq = routeSeqRef.current[pairKey];
    fetch('/api/route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trip_id: TRIP_ID, from_option_id: fromOptionId, to_option_id: toOptionId, mode: 'driving', request_seq: seq }),
    })
      .then(r => r.json())
      .then(data => {
        if (routeSeqRef.current[pairKey] !== seq) return; // stale
        setRouteCache(prev => ({ ...prev, [pairKey]: data }));
      })
      .catch(() => { setRouteCache(prev => ({ ...prev, [pairKey]: { status: 'error' } })); });
  }, []);

  // saveMutations: central save helper (M5, M6, M7, M11)
  const saveMutations = useCallback(async (dayNum, mutations) => {
    if (isOffline) {
      setSaveState('error');
      setSaveStatusText('offline — not saved');
      return;
    }
    setSaveState('saving');
    setSaveStatusText('saving…');
    const seq = ++saveSeqRef.current;
    try {
      const resp = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: TRIP_ID,
          day: dayNum,
          editor_session: editorSession,
          mutations,
        }),
      });
      if (saveSeqRef.current !== seq) return; // stale
      if (resp.status === 409) {
        setConflictDetected(true);
        setSaveState('error');
        setSaveStatusText('conflict');
        return;
      }
      const data = await resp.json();
      if (saveSeqRef.current !== seq) return; // stale after json parse
      if (data.conflict === '409-soft') {
        setConflictDetected(true);
        setSaveState('error');
        setSaveStatusText('conflict');
        return;
      }
      if (!resp.ok) {
        setSaveState('error');
        setSaveStatusText('error');
        return;
      }
      const ts = Date.now();
      setSaveState('saved');
      setLastSaveTs(ts);
      setSaveStatusText('saved');
      // AC8: update editorTripData.days[n].stage after successful stage mutation so editorDay doesn't stay stale
      if (mutations && mutations.some(m => m.type === 'stage')) {
        const stageMut = mutations.find(m => m.type === 'stage');
        const stageVal = stageMut && (stageMut.to_stage != null ? stageMut.to_stage : stageMut.value);
        if (stageVal) setEditorTripData(prev => {
          if (!prev || !prev.days) return prev;
          return { ...prev, days: prev.days.map(d => Number(d.day) === Number(dayNum) ? { ...d, stage: stageVal } : d) };
        });
      }
      // Post-save budget recompute (M10, M25)
      recomputeBudget(dayNum);
    } catch (_) {
      if (saveSeqRef.current !== seq) return;
      setSaveState('error');
      setSaveStatusText('error');
    }
  }, [isOffline, editorSession, recomputeBudget]);

  // setEditorSelection bridge (also used internally)
  const setEditorSelection = useCallback((slotId, optionId, dayNum, originSlotId) => {
    const key = (dayNum || (publishedDay && publishedDay.day)) + ':' + slotId;
    setEditorSelections(prev => ({ ...prev, [key]: optionId }));
  }, [publishedDay]);

  // Expose legacy bridge for compatibility (deps: publishedDay.day, saveMutations)
  useEffect(() => {
    const bridge = (slotId, optionId, originSlotId = null) => {
      const dayNum = publishedDay && publishedDay.day;
      if (!dayNum) return;
      const updates = { [dayNum + ':' + slotId]: optionId };
      if (originSlotId && _isCompatible(originSlotId, slotId)) {
        updates[dayNum + ':' + originSlotId] = optionId;
      }
      setEditorSelections(prev => ({ ...prev, ...updates }));
      // AC20: if cross-meal drop, copy option object into editorTripData so mergeEditorSelectionsIntoPublishedDay can find it in the target slot
      if (originSlotId && editorDay && editorDay.slots) {
        setEditorTripData(prev => {
          if (!prev || !prev.days) return prev;
          const updated = JSON.parse(JSON.stringify(prev));
          const dayEntry = updated.days && updated.days.find(d => Number(d.day) === Number(dayNum));
          if (!dayEntry || !dayEntry.slots) return prev;
          const tgtSlot = dayEntry.slots[slotId];
          if (!tgtSlot) return prev;
          if (!tgtSlot.options) tgtSlot.options = [];
          const alreadyThere = tgtSlot.options.some(o => o.option_id === optionId);
          if (!alreadyThere) {
            const srcSlot = dayEntry.slots[originSlotId];
            if (srcSlot && srcSlot.options) {
              const srcOpt = srcSlot.options.find(o => o.option_id === optionId);
              if (srcOpt) tgtSlot.options.push({ ...srcOpt });
            }
          }
          return updated;
        });
      }
      saveMutations(dayNum, [{ type: 'select', slot: slotId, option_id: optionId, origin_slot_id: originSlotId }]);
    };
    window.setEditorSelection = bridge;
    // applyEditorSelection: used by slot-drop onClick for tap-to-select second step (AC14)
    const applyBridge = (optionId, targetSlotId, originSlotId) => {
      const dayNum = publishedDay && publishedDay.day;
      if (!dayNum) return;
      const key = dayNum + ':' + targetSlotId;
      setEditorSelections(prev => ({ ...prev, [key]: optionId }));
      saveMutations(dayNum, [{ type: 'select', slot: targetSlotId, option_id: optionId, origin_slot_id: originSlotId || null }]);
      setPendingSelection(null);
    };
    window.applyEditorSelection = applyBridge;
    return () => {
      if (window.setEditorSelection === bridge) delete window.setEditorSelection;
      if (window.applyEditorSelection === applyBridge) delete window.applyEditorSelection;
    };
  }, [publishedDay && publishedDay.day, saveMutations, editorDay]);

  // Budget recompute on page load after editorTripData fetched (M25)
  const editorTripDataRef = React.useRef(null);
  useEffect(() => {
    if (editorTripData && !editorTripDataRef.current && publishedDay) {
      recomputeBudget(publishedDay.day);
    }
    editorTripDataRef.current = editorTripData;
  }, [editorTripData, publishedDay, recomputeBudget]);

  const day = effectiveDay;

  // Fetch routes between consecutive filled slots after each effectiveDay change (AC12/AC23)
  useEffect(() => {
    if (!day || !editorDay) return;
    const filledSlots = ['breakfast', 'morning_activity', 'lunch', 'afternoon_activity', 'dinner', 'evening_activity'].filter(slotId => {
      const key = (day.day) + ':' + slotId;
      const persistedId = editorDay.slots && editorDay.slots[slotId] && editorDay.slots[slotId].selected_option_id;
      return Object.prototype.hasOwnProperty.call(editorSelections, key) ? editorSelections[key] : persistedId;
    });
    for (let i = 0; i < filledSlots.length - 1; i++) {
      const aSlot = filledSlots[i];
      const bSlot = filledSlots[i + 1];
      const aKey = day.day + ':' + aSlot;
      const bKey = day.day + ':' + bSlot;
      const aId = Object.prototype.hasOwnProperty.call(editorSelections, aKey) ? editorSelections[aKey] : (editorDay.slots && editorDay.slots[aSlot] && editorDay.slots[aSlot].selected_option_id);
      const bId = Object.prototype.hasOwnProperty.call(editorSelections, bKey) ? editorSelections[bKey] : (editorDay.slots && editorDay.slots[bSlot] && editorDay.slots[bSlot].selected_option_id);
      const pairKey = aId + ':' + bId;
      if (aId && bId && !routeCache[pairKey]) fetchRoute(aId, bId, pairKey);
    }
  }, [effectiveDay, editorSelections, editorDay, fetchRoute]);

  const handleItemClick = (item, type) => {
    setSelectedBudgetCat(null);
    setSelectedItem({ item, type });
  };

  const handleBudgetClick = (category, dayData) => {
    setSelectedItem(null);

    let items = [];
    let total = 0;

    if (category === 'meals') {
      ['breakfast', 'lunch', 'dinner'].forEach(mealType => {
        if (dayData.meals[mealType]) {
          items.push(dayData.meals[mealType]);
          total += dayData.meals[mealType].cost || 0;
        }
      });
    } else if (category === 'attractions') {
      items = dayData.attractions || [];
      total = dayData.budget.attractions || 0;
    } else if (category === 'entertainment') {
      items = dayData.entertainment || [];
      total = dayData.budget.entertainment || 0;
    } else if (category === 'accommodation') {
      items = dayData.accommodation ? [dayData.accommodation] : [];
      total = dayData.budget.accommodation || 0;
    } else if (category === 'shopping') {
      items = dayData.shopping || [];
      total = dayData.budget.shopping || 0;
    } else if (category === 'cafe') {
      items = dayData.cafe || [];
      total = dayData.budget.cafe || 0;
    } else if (category === 'transportation') {
      items = dayData.transportation ? [dayData.transportation] : [];
      total = dayData.budget.transportation || 0;
    }

    setSelectedBudgetCat({ category, items, total });
  };

  return (
    <div style={{
      display: 'flex',
      fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, 'Noto Sans SC', sans-serif",
      background: '#ffffff', minHeight: '100vh', color: '#37352f'
    }}>
      <Sidebar
        trips={PLAN_DATA.trips} selTrip={selTrip} selDay={selDay}
        onSelect={(ti, di) => {
          setSelTrip(ti); setSelDay(di);
          // Budget recompute on day switch (M25)
          const newDay = PLAN_DATA.trips[ti] && PLAN_DATA.trips[ti].days && PLAN_DATA.trips[ti].days[di];
          if (newDay) recomputeBudget(newDay.day);
        }}
        isOpen={sbOpen} onClose={() => setSbOpen(false)} bp={bp}
        lang={lang}
      />

      <div style={{ flex: 1, minWidth: 0, marginRight: isMobileLayout ? 0 : '300px' }}>
        <div style={{
          borderBottom: '1px solid #f0efed',
          padding: `0 ${sm ? '12px' : '20px'}`,
          display: 'flex', alignItems: 'center', flexWrap: 'wrap',
          position: 'sticky', top: 0, background: 'rgba(255,255,255,0.97)',
          backdropFilter: 'blur(8px)', zIndex: 50, gap: '2px'
        }}>
          {sm && (
            <button onClick={() => setSbOpen(true)} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '17px', padding: '10px 6px 10px 2px', color: '#37352f'
            }}>☰</button>
          )}
          {(isMobileLayout ? ['kanban', 'timeline', 'candidates'] : ['kanban', 'timeline']).map(m => (
            <button key={m} onClick={() => { if (isMobileLayout) setMobileTab(m); else setView(m); }} style={{
              padding: sm ? '10px 8px' : '11px 16px', background: 'none', border: 'none',
              borderBottom: (isMobileLayout ? mobileTab : view) === m ? '2px solid #37352f' : '2px solid transparent',
              fontSize: '14px', fontWeight: (isMobileLayout ? mobileTab : view) === m ? '600' : '400',
              color: (isMobileLayout ? mobileTab : view) === m ? '#37352f' : '#b4b4b4',
              cursor: 'pointer', transition: 'all .12s', whiteSpace: 'nowrap'
            }}>
              {m === 'kanban' ? L('kanban_view', lang) : m === 'timeline' ? L('timeline_view', lang) : 'Candidates'}
            </button>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: sm ? '6px' : '12px', ...(sm ? { width: '100%', justifyContent: 'flex-end', paddingBottom: '6px' } : {}) }}>
            {/* Map provider toggle */}
            <div style={{ display: 'flex', gap: '2px', background: '#f5f5f3', borderRadius: '6px', padding: '2px', border: '1px solid #e0e0e0' }}>
              <button onClick={() => setMapProvider('gaode')} style={{
                padding: sm ? '5px 6px' : '6px 10px',
                background: mapProvider === 'gaode' ? '#e6f3ff' : 'transparent',
                border: mapProvider === 'gaode' ? '1px solid #0085fe' : '1px solid transparent',
                borderRadius: '4px',
                fontSize: '12px', fontWeight: mapProvider === 'gaode' ? '600' : '400',
                color: mapProvider === 'gaode' ? '#0085fe' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s',
                display: 'flex', alignItems: 'center', gap: '3px'
              }}>
                <GaodeLogo size={12} />
                {sm ? '高德' : '高德地图'}
              </button>
              <button onClick={() => setMapProvider('google')} style={{
                padding: sm ? '5px 6px' : '6px 10px',
                background: mapProvider === 'google' ? '#e8f0fe' : 'transparent',
                border: mapProvider === 'google' ? '1px solid #4285F4' : '1px solid transparent',
                borderRadius: '4px',
                fontSize: '12px', fontWeight: mapProvider === 'google' ? '600' : '400',
                color: mapProvider === 'google' ? '#4285F4' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s',
                display: 'flex', alignItems: 'center', gap: '3px'
              }}>
                <GoogleMapsLogo size={12} />
                Google
              </button>
            </div>
            {/* Language toggle */}
            <div style={{ display: 'flex', gap: '4px' }}>
              <button onClick={() => setLang('local')} style={{
                padding: sm ? '8px 10px' : '9px 14px',
                background: lang === 'local' ? '#e9f5ec' : '#f5f5f3',
                border: `1px solid ${lang === 'local' ? '#45b26b' : '#e0e0e0'}`,
                borderRadius: '6px',
                fontSize: '13px', fontWeight: lang === 'local' ? '600' : '400',
                color: lang === 'local' ? '#45b26b' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s'
              }}>
                {PLAN_DATA.trip_summary.local_display || 'Local'}
              </button>
              <button onClick={() => setLang('base')} style={{
                padding: sm ? '8px 10px' : '9px 14px',
                background: lang === 'base' ? '#e9f5ec' : '#f5f5f3',
                border: `1px solid ${lang === 'base' ? '#45b26b' : '#e0e0e0'}`,
                borderRadius: '6px',
                fontSize: '13px', fontWeight: lang === 'base' ? '600' : '400',
                color: lang === 'base' ? '#45b26b' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s'
              }}>
                {PLAN_DATA.trip_summary.base_display || 'EN'}
              </button>
            </div>
            {/* Save status badge (M5, M27) */}
            <span style={{
              fontSize: '11px', padding: '3px 7px', borderRadius: '4px',
              background: saveState === 'saving' ? '#fff3cd' : saveState === 'saved' ? '#d4edda' : saveState === 'error' ? '#f8d7da' : '#f5f5f3',
              color: saveState === 'saving' ? '#856404' : saveState === 'saved' ? '#155724' : saveState === 'error' ? '#721c24' : '#9b9a97',
              border: '1px solid transparent', whiteSpace: 'nowrap'
            }}>
              {saveStatusText || (saveState === 'idle' ? '' : saveState)}
            </span>
            {/* Conn-status badge (M28) */}
            <span className="conn-status" data-state={isOffline ? 'offline' : 'online'} style={{
              fontSize: '11px', padding: '3px 7px', borderRadius: '4px',
              background: isOffline ? '#f8d7da' : '#d4edda',
              color: isOffline ? '#721c24' : '#155724',
              border: '1px solid transparent', whiteSpace: 'nowrap'
            }}>
              {isOffline ? 'offline' : 'online'}
            </span>
            {/* Export buttons (M26) */}
            {TRIP_ID && (() => {
              const REQUIRED_SLOT_KEYS_CHECK = ['accommodation', 'breakfast', 'lunch', 'dinner'];
              const _anyValidationError = () => {
                if (!editorTripData || !editorTripData.days) return true;
                return editorTripData.days.some(edDay => {
                  return REQUIRED_SLOT_KEYS_CHECK.some(slotId => {
                    // accommodation is top-level; named meal slots are under .slots
                    const slot = slotId === 'accommodation' ? edDay.accommodation : (edDay.slots && edDay.slots[slotId]);
                    if (!slot) return true; // missing slot = validation error
                    if (slot.skipped) return false;
                    const key = edDay.day + ':' + slotId;
                    const resolved = Object.prototype.hasOwnProperty.call(editorSelections, key) ? editorSelections[key] : slot.selected_option_id;
                    return !resolved;
                  });
                });
              };
              const exportDisabled = isOffline || _anyValidationError();
              const handleExport = async (kind) => {
                if (exportDisabled) return;
                try {
                  const resp = await fetch('/api/export/' + kind, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ trip_id: TRIP_ID }),
                  });
                  const data = await resp.json();
                  if (data.file_path) {
                    setSaveStatusText(data.file_path);
                  } else {
                    setSaveStatusText('export ' + kind + ' failed');
                    setSaveState('error');
                  }
                } catch (_) {
                  setSaveStatusText('export ' + kind + ' failed');
                  setSaveState('error');
                }
              };
              return (<>
                <button onClick={() => handleExport('pdf')} disabled={exportDisabled} style={{
                  fontSize: '11px', padding: '4px 8px', borderRadius: '4px',
                  background: exportDisabled ? '#f5f5f3' : '#edf2fc', color: exportDisabled ? '#c4c4c0' : '#2b63b5',
                  border: '1px solid ' + (exportDisabled ? '#e0e0e0' : '#b4caf0'), cursor: exportDisabled ? 'default' : 'pointer'
                }}>PDF</button>
                <button onClick={() => handleExport('ical')} disabled={exportDisabled} style={{
                  fontSize: '11px', padding: '4px 8px', borderRadius: '4px',
                  background: exportDisabled ? '#f5f5f3' : '#edf2fc', color: exportDisabled ? '#c4c4c0' : '#2b63b5',
                  border: '1px solid ' + (exportDisabled ? '#e0e0e0' : '#b4caf0'), cursor: exportDisabled ? 'default' : 'pointer'
                }}>iCal</button>
              </>);
            })()}
          </div>
        </div>
        {/* OfflineBanner (M6) */}
        {isOffline && (
          <div style={{ background: '#f8d7da', color: '#721c24', padding: '8px 20px', fontSize: '13px', fontWeight: '500' }}>
            You are offline. Changes will not be saved until you reconnect.
          </div>
        )}
        {/* ConflictBanner (M7, M29) */}
        {conflictDetected && (
          <div style={{ background: '#fff3cd', color: '#856404', padding: '8px 20px', fontSize: '13px', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>Another session modified this plan. Reload to see the latest version.</span>
            <button onClick={() => window.location.reload()} style={{ fontSize: '12px', padding: '3px 10px', borderRadius: '4px', background: '#856404', color: '#fff', border: 'none', cursor: 'pointer' }}>Reload</button>
            <button onClick={() => setConflictDetected(false)} style={{ fontSize: '12px', padding: '3px 10px', borderRadius: '4px', background: 'transparent', color: '#856404', border: '1px solid #856404', cursor: 'pointer' }}>Dismiss</button>
          </div>
        )}

        {/* Approve Day button (M8, M24) */}
        {TRIP_ID && day && editorDay && (() => {
          const REQUIRED_SLOT_KEYS_BTN = ['accommodation', 'breakfast', 'lunch', 'dinner'];
          // AC24: use editorDay (v2 slot-envelope) not effectiveDay (PLAN_DATA shape)
          const getEdSlot = (slotId) =>
            slotId === 'accommodation' ? editorDay.accommodation : (editorDay.slots && editorDay.slots[slotId]);
          const allFilled = REQUIRED_SLOT_KEYS_BTN.every(slotId => {
            const slot = getEdSlot(slotId);
            if (!slot) return false; // missing slot = not filled
            if (slot.skipped) return true;
            const key = day.day + ':' + slotId;
            const resolved = Object.prototype.hasOwnProperty.call(editorSelections, key) ? editorSelections[key] : slot.selected_option_id;
            return !!resolved;
          });
          const isApproved = editorDay && editorDay.stage === 'user-selected';
          const canApprove = allFilled && editorDay && (editorDay.stage === 'draft-options' || editorDay.stage === 'user-review');
          const approveDisabled = isApproved || !canApprove;
          return (
            <div style={{ padding: '6px 20px', borderBottom: '1px solid #f0efed', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                disabled={approveDisabled}
                onClick={() => {
                  if (approveDisabled) return;
                  const dayNum = day.day;
                  saveMutations(dayNum, [{ type: 'stage', from_stage: editorDay.stage, to_stage: 'user-selected' }]);
                }}
                style={{
                  fontSize: '12px', padding: '5px 14px', borderRadius: '5px', fontWeight: '600',
                  background: isApproved ? '#e9f5ec' : approveDisabled ? '#f5f5f3' : '#45b26b',
                  color: isApproved ? '#1a7a32' : approveDisabled ? '#c4c4c0' : '#fff',
                  border: '1px solid ' + (isApproved ? '#a2d9b1' : approveDisabled ? '#e0e0e0' : '#3a9a5c'),
                  cursor: approveDisabled ? 'default' : 'pointer', transition: 'all .12s'
                }}
              >
                {isApproved ? 'Approved' : 'Approve Day'}
              </button>
            </div>
          );
        })()}
        {day ? (() => {
          const activeView = isMobileLayout ? mobileTab : view;
          if (isMobileLayout && activeView === 'candidates') {
            return (
              <CandidatesSidebar
                editorTripData={editorTripData}
                publishedDay={publishedDay}
                lang={lang}
                editorSelections={editorSelections}
                saveMutations={saveMutations}
                setEditorSelections={setEditorSelections}
                editorDay={editorDay}
                pendingSelection={pendingSelection}
                setPendingSelection={setPendingSelection}
                setEditorTripData={setEditorTripData}
                inlineMode={true}
              />
            );
          }
          return activeView === 'kanban'
            ? <KanbanView
                day={day}
                tripSummary={PLAN_DATA.trip_summary}
                showSummary={selDay === 0 && selTrip === 0}
                bp={bp}
                lang={lang}
                mapProvider={mapProvider}
                onItemClick={handleItemClick}
                onBudgetClick={handleBudgetClick}
                editorDay={editorDay}
                editorSelections={editorSelections}
                saveMutations={saveMutations}
                setEditorSelections={setEditorSelections}
                pendingSelection={pendingSelection}
                setPendingSelection={setPendingSelection}
                setEditorTripData={setEditorTripData}
                editorTripData={editorTripData}
                liveDayTotal={liveDayTotal}
                routeCache={routeCache}
                fetchRoute={fetchRoute}
              />
            : <TimelineView
                day={day}
                bp={bp}
                lang={lang}
                mapProvider={mapProvider}
                onItemClick={handleItemClick}
                editorDay={editorDay}
                editorSelections={editorSelections}
                pendingSelection={pendingSelection}
                setPendingSelection={setPendingSelection}
                saveMutations={saveMutations}
                setEditorSelections={setEditorSelections}
                routeCache={routeCache}
                fetchRoute={fetchRoute}
              />;
        })() : (
          <div style={{ padding: `60px ${sm ? '16px' : '48px'}`, color: '#c4c4c0' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>🗺️</div>
            <div style={{ fontWeight: '500', fontSize: '16px', color: '#9b9a97' }}>{trip?.name}</div>
            <div style={{ marginTop: '4px' }}>{L('coming_soon', lang)}</div>
          </div>
        )}

        {selectedItem && (
          <ItemDetailSidebar
            item={selectedItem.item}
            type={selectedItem.type}
            onClose={() => setSelectedItem(null)}
            bp={bp}
            lang={lang}
            mapProvider={mapProvider}
          />
        )}

        {selectedBudgetCat && (
          <BudgetDetailSidebar
            category={selectedBudgetCat.category}
            items={selectedBudgetCat.items}
            total={selectedBudgetCat.total}
            onClose={() => setSelectedBudgetCat(null)}
            bp={bp}
            lang={lang}
          />
        )}
      </div>

      {!isMobileLayout && (
        <CandidatesSidebar
          editorTripData={editorTripData}
          publishedDay={publishedDay}
          lang={lang}
          editorSelections={editorSelections}
          saveMutations={saveMutations}
          setEditorSelections={setEditorSelections}
          editorDay={editorDay}
          pendingSelection={pendingSelection}
          setPendingSelection={setPendingSelection}
          setEditorTripData={setEditorTripData}
        />
      )}
    </div>
  );
}