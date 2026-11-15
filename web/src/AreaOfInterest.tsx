import {useEffect, useId, useMemo, useRef, useState} from 'react';
import type {FormEvent, PointerEvent as ReactPointerEvent} from 'react';
import {AlertTriangle, Crosshair, MapPinned, RotateCcw} from 'lucide-react';
import MonthCalendar from './MonthCalendar';
import {invalidateData, loadData} from './loadData';
import {AREA_NOTE, circleError, describeSelection, firstYear, selectCells, sumSeries, validPayload} from './areaSelection';
import type {AreaPayload, Rect, Selection} from './areaSelection';
import {monthMatrixFromMonthly, RAMP} from './monthStats';
import {fmt} from './utils';
import './area.css';

type Land = {features: {geometry: {type: string; coordinates: number[][][] | number[][][][]}}[]};
interface Props {regionId: string; regionName: string; label: string}
const W = 720, H = 400;

function bounds(area: AreaPayload) {
  let s = 90, n = -90, w = 180, e = -180;
  for (let i = 0; i < area.lat.length; i++) {
    s = Math.min(s, area.lat[i]); n = Math.max(n, area.lat[i]); w = Math.min(w, area.lon[i]); e = Math.max(e, area.lon[i]);
  }
  const pad = .6;
  return {s: s - pad, n: n + pad, w: w - pad, e: e + pad};
}

export default function AreaOfInterest({regionId, regionName, label}: Props) {
  const [requested, setRequested] = useState(false), [attempt, setAttempt] = useState(0);
  const [area, setArea] = useState<AreaPayload | null>(null), [error, setError] = useState(''), [loading, setLoading] = useState(false);
  const [land, setLand] = useState<Land | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [drag, setDrag] = useState<{x0: number; y0: number; x1: number; y1: number} | null>(null);
  const [form, setForm] = useState({lat: '', lon: '', km: '50'}), [formError, setFormError] = useState('');
  const canvas = useRef<HTMLCanvasElement>(null), svg = useRef<SVGSVGElement>(null);
  const ids = {lat: useId(), lon: useId(), km: useId(), help: useId(), err: useId()};

  useEffect(() => { setRequested(false); setArea(null); setSelection(null); setError(''); setDrag(null); }, [regionId]);
  useEffect(() => {
    if (!requested) return;
    const controller = new AbortController();
    setLoading(true); setError('');
    Promise.all([loadData<unknown>(`area/${regionId}.json`, controller.signal), loadData<Land>('world-land.json', controller.signal).catch(() => null)])
      .then(([value, outline]) => {
        if (!validPayload(value)) throw new Error('invalid');
        setArea(value); setLand(outline); setLoading(false);
      })
      .catch(e => { if (e.name !== 'AbortError') { setError('Area cells could not be loaded for this country.'); setLoading(false); } });
    return () => controller.abort();
  }, [requested, regionId, attempt]);

  const wraps = useMemo(() => !!area && area.lon.some(l => l > 150) && area.lon.some(l => l < -150), [area]);
  const norm = (lon: number) => wraps && lon > 0 ? lon - 360 : lon;
  const view = useMemo(() => area && wraps ? {...area, lon: area.lon.map(l => l > 0 ? l - 360 : l)} : area, [area, wraps]);
  const box = useMemo(() => view ? bounds(view) : null, [view]);
  const scale = box ? Math.min(W / (box.e - box.w), H / (box.n - box.s)) : 1;
  const px = (lon: number) => box ? (lon - box.w) * scale : 0;
  const py = (lat: number) => box ? (box.n - lat) * scale : 0;
  const mapW = box ? Math.ceil((box.e - box.w) * scale) : W, mapH = box ? Math.ceil((box.n - box.s) * scale) : H;
  const totals = useMemo(() => area ? area.series.map(s => { let t = 0; for (let k = 1; k < s.length; k += 2) t += s[k]; return t; }) : [], [area]);

  useEffect(() => {
    const c = canvas.current;
    if (!c || !area || !box) return;
    const ratio = window.devicePixelRatio || 1;
    c.width = mapW * ratio; c.height = mapH * ratio;
    const g = c.getContext('2d');
    if (!g) return;
    g.setTransform(ratio, 0, 0, ratio, 0, 0);
    g.clearRect(0, 0, mapW, mapH);
    const max = Math.log1p(Math.max(1, ...totals));
    const size = Math.max(1.5, area.grid * scale);
    for (let i = 0; i < area.lat.length; i++) {
      g.fillStyle = RAMP[Math.min(RAMP.length - 1, Math.floor(Math.log1p(totals[i]) / max * (RAMP.length - 1)))];
      g.fillRect(px(view!.lon[i]) - size / 2, py(area.lat[i]) - size / 2, size, size);
    }
  }, [area, view, box, totals, mapW, mapH]); // eslint-disable-line react-hooks/exhaustive-deps

  const outline = useMemo(() => {
    if (!land || !box) return '';
    const parts: string[] = [];
    for (const f of land.features) {
      const polys = (f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates) as number[][][][];
      for (const poly of polys) for (const ring of poly) {
        if (!ring.some(([lon, lat]) => norm(lon) >= box.w - 5 && norm(lon) <= box.e + 5 && lat >= box.s - 5 && lat <= box.n + 5)) continue;
        let d = '', prev: number | null = null;
        for (const [lon, lat] of ring) {
          const x = px(norm(lon)), y = py(lat);
          // break the path where a ring jumps across the shifted antimeridian instead of drawing a line across the map
          d += `${prev === null || Math.abs(x - prev) > mapW / 2 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
          prev = x;
        }
        parts.push(d);
      }
    }
    return parts.join('');
  }, [land, box, scale, mapW]); // eslint-disable-line react-hooks/exhaustive-deps

  const chosen = useMemo(() => view && selection ? selectCells(view, selection.kind === 'circle' ? {kind: 'circle', circle: {...selection.circle, lon: norm(selection.circle.lon)}} : selection) : [], [view, selection]); // eslint-disable-line react-hooks/exhaustive-deps
  const matrix = useMemo(() => area && chosen.length ? monthMatrixFromMonthly(sumSeries(area, chosen), firstYear(area), area.outage_months, 'harmonized') : null, [area, chosen]);

  function toMap(event: ReactPointerEvent<SVGSVGElement>) {
    const r = svg.current!.getBoundingClientRect();
    return {x: Math.max(0, Math.min(mapW, (event.clientX - r.left) / r.width * mapW)), y: Math.max(0, Math.min(mapH, (event.clientY - r.top) / r.height * mapH))};
  }
  function down(event: ReactPointerEvent<SVGSVGElement>) {
    if (!event.isPrimary || event.button !== 0) return;
    const p = toMap(event);
    svg.current?.setPointerCapture(event.pointerId);
    setDrag({x0: p.x, y0: p.y, x1: p.x, y1: p.y});
  }
  function move(event: ReactPointerEvent<SVGSVGElement>) { if (drag) { const p = toMap(event); setDrag({...drag, x1: p.x, y1: p.y}); } }
  function up() {
    if (!drag || !box) return;
    const {x0, y0, x1, y1} = drag;
    setDrag(null);
    if (Math.abs(x1 - x0) < 4 || Math.abs(y1 - y0) < 4) return;
    const rect: Rect = {west: box.w + Math.min(x0, x1) / scale, east: box.w + Math.max(x0, x1) / scale,
      north: box.n - Math.min(y0, y1) / scale, south: box.n - Math.max(y0, y1) / scale};
    setSelection({kind: 'rect', rect}); setFormError('');
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    const problem = circleError(form.lat, form.lon, form.km);
    setFormError(problem ?? '');
    if (!problem) setSelection({kind: 'circle', circle: {lat: Number(form.lat), lon: Number(form.lon), km: Number(form.km)}});
  }

  if (!requested) return <div className="area-start">
    <p className="panel-description">Draw a rectangle on a map, or type a point and radius, to see the monthly calendar for that area. The cell data for {regionName} load only when you ask for them.</p>
    <button type="button" className="button subtle" onClick={() => setRequested(true)}><MapPinned size={15}/> Load {regionName} area cells</button>
  </div>;
  if (loading) return <div className="area-start" role="status"><span className="loader"/> Loading {regionName} area cells…</div>;
  if (error || !area || !box) return <div className="error-banner" role="alert"><AlertTriangle size={18}/><div><p>{error || 'Area cells are unavailable.'}</p>
    <button type="button" className="button" onClick={() => { invalidateData(`area/${regionId}.json`); setAttempt(n => n + 1); }}>Retry</button></div></div>;

  const shown = selection?.kind === 'rect' ? selection.rect : null;
  const circle = selection?.kind === 'circle' ? selection.circle : null;
  const kmPerPx = 111.32 / scale;
  return <div className="area-tool">
    <div className="area-note" role="note"><AlertTriangle size={16}/><p><strong>{AREA_NOTE}</strong> Cells are 0.25° squares summed from the same frozen {area.model} model as the national series, with no refitting. Observed Aqua through 2012, converted VIIRS from {area.switch.slice(0, 4)}.</p></div>
    <div className="area-layout">
      <div className="area-map-wrap">
        <div className="area-map" style={{aspectRatio: `${mapW} / ${mapH}`}}>
          <canvas ref={canvas} aria-hidden="true" style={{width: '100%', height: '100%'}}/>
          <svg ref={svg} viewBox={`0 0 ${mapW} ${mapH}`} onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={() => setDrag(null)}
            role="img" aria-label={`${regionName}: ${fmt(area.lat.length)} cells with detections. Drag to draw a rectangle; or use the point and radius form.`} aria-describedby={ids.help}>
            {outline && <path d={outline} className="area-land"/>}
            {shown && <rect className="area-rect" x={px(shown.west)} y={py(shown.north)} width={px(shown.east) - px(shown.west)} height={py(shown.south) - py(shown.north)}/>}
            {circle && <ellipse className="area-rect" cx={px(norm(circle.lon))} cy={py(circle.lat)} rx={circle.km / (kmPerPx * Math.max(.05, Math.cos(circle.lat * Math.PI / 180)))} ry={circle.km / kmPerPx}/>}
            {drag && <rect className="area-rect drawing" x={Math.min(drag.x0, drag.x1)} y={Math.min(drag.y0, drag.y1)} width={Math.abs(drag.x1 - drag.x0)} height={Math.abs(drag.y1 - drag.y0)}/>}
          </svg>
        </div>
        <p id={ids.help} className="chart-note"><Crosshair size={11}/> Drag on the map to draw a rectangle. Colour shows each cell's total over the record (log scale). Uncoloured areas have no processed detections; that is not a claim of no fire.</p>
      </div>
      <form className="area-form" onSubmit={submit} noValidate aria-describedby={formError ? ids.err : undefined}>
        <h3>Point and radius</h3>
        <label htmlFor={ids.lat}>Latitude<input id={ids.lat} inputMode="decimal" value={form.lat} onChange={e => setForm({...form, lat: e.target.value})} placeholder={`${((box.s + box.n) / 2).toFixed(2)}`}/></label>
        <label htmlFor={ids.lon}>Longitude<input id={ids.lon} inputMode="decimal" value={form.lon} onChange={e => setForm({...form, lon: e.target.value})} placeholder={`${((box.w + box.e) / 2).toFixed(2)}`}/></label>
        <label htmlFor={ids.km}>Radius (km)<input id={ids.km} inputMode="decimal" value={form.km} onChange={e => setForm({...form, km: e.target.value})}/></label>
        {formError && <p id={ids.err} className="area-error" role="alert">{formError}</p>}
        <button type="submit" className="button primary">Show this area</button>
        {selection && <button type="button" className="button subtle" onClick={() => setSelection(null)}><RotateCcw size={13}/> Clear selection</button>}
      </form>
    </div>
    <div aria-live="polite" className="area-summary">{selection ? <p><strong>{describeSelection(selection)}</strong>: {fmt(chosen.length)} cell{chosen.length === 1 ? '' : 's'} with detections inside.</p> : <p>No area selected yet.</p>}</div>
    {selection && !chosen.length && <p className="panel-description">No cells with processed detections fall inside this area. Try a larger area.</p>}
    {matrix && selection && <MonthCalendar matrix={matrix} mode="harmonized" label={label} regionId={regionId} regionName={regionName}
      scopeName={`${describeSelection(selection)} (${chosen.length} cells; ${AREA_NOTE})`} scopeId={`area-${chosen.length}`} fileScope="area"/>}
  </div>;
}
