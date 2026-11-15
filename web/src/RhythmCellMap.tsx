import {useEffect, useMemo, useState} from 'react';
import {FlaskConical} from 'lucide-react';
import {loadData} from './loadData';

type Num = number | null;
interface CellProps {
  country: string; cell_lat: number; cell_lon: number; rest_day: string; years: number; mean_detections_per_year: number;
  rest_index: number; ci_lo: number; ci_hi: number; p_null: number; q_bh: number; significant: boolean; lowest_day: string;
  aqua_rest_index: Num; aqua_q_bh: Num; aqua_significant: boolean | null;
}
interface Cells {metadata: {label: string; significant: string; cell: string}; features: {properties: CellProps}[]}
interface CellTable {metadata: Cells['metadata']; columns: string[]; rows: unknown[][]}
const decodeCells = (t: CellTable): Cells => ({metadata: t.metadata, features: t.rows.map(r => ({properties: Object.fromEntries(t.columns.map((k, i) => [k, r[i]])) as unknown as CellProps}))});
interface AquaCheck {cells_with_both: number; corr_rest_index: Num; share_same_side_of_1: Num; viirs_sig_cells_with_aqua: number; of_those_aqua_below_1: number; of_those_aqua_significant: number}
interface AreaGroup {cells: number; significant: number; median_sunday_index: Num}
interface Summary {aqua_check: Record<string, AquaCheck>; per_country: Record<string, Record<string, {cells: number; significant: number}>>;
  northeast_india_area?: {northeast_mostly_india: AreaGroup; northeast_cross_border: AreaGroup; rest_of_india_mostly_india: AreaGroup}}
type Land = {features: {geometry: {type: string; coordinates: number[][][][] | number[][][]}}[]};

const NAMES: Record<string, string> = {United_States: 'United States', Brazil: 'Brazil', Australia: 'Australia', India: 'India'};
// A highlighted area is drawn by eye after viewing the maps; every number shown for it is computed from the cells.
// context: team-written description (see METHODS.md and reports/review/northeast_india/).
const HIGHLIGHTS: Record<string, {title: string; test: (p: CellProps) => boolean; rest: string; restTest: (p: CellProps) => boolean; context?: string}> = {
  India: {title: 'Northeast India (east of 89° E)', test: p => p.cell_lon >= 89, rest: 'rest of India', restTest: p => p.cell_lon < 89,
    context: "Within India, the Sunday dip is concentrated in the northeastern hill states, deepest in Nagaland, Mizoram and Manipur, where Sunday detections fall to about 40% of an average day; the rest of India, including the Punjab crop-burning belt, shows no weekly dip. This is an exploratory association; these data do not establish its cause."},
};

function color(v: number) {
  const stops: [number, number[]][] = [[0.7, [33, 102, 172]], [0.85, [103, 169, 207]], [1, [247, 247, 247]], [1.15, [239, 138, 98]], [1.3, [178, 24, 43]]];
  const x = Math.max(0.7, Math.min(1.3, v));
  for (let i = 1; i < stops.length; i++) {
    const [a, ca] = stops[i - 1], [b, cb] = stops[i];
    if (x <= b) { const t = (x - a) / (b - a); return `rgb(${ca.map((c, k) => Math.round(c + (cb[k] - c) * t)).join(',')})`; }
  }
  return 'rgb(178,24,43)';
}
const lat = (v: number) => `${Math.abs(v)}° ${v < 0 ? 'S' : 'N'}`;
const lon = (v: number) => `${Math.abs(v)}° ${v < 0 ? 'W' : 'E'}`;
const f3 = (v: Num | undefined) => (typeof v === 'number' ? v.toFixed(3) : '—');
const median = (xs: number[]) => { const s = [...xs].sort((a, b) => a - b); return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : null; };

export default function RhythmCellMap() {
  const [cells, setCells] = useState<Cells | null>(null), [summary, setSummary] = useState<Summary | null>(null);
  const [land, setLand] = useState<Land | null>(null), [error, setError] = useState('');
  const [country, setCountry] = useState('India'), [active, setActive] = useState<CellProps | null>(null);
  useEffect(() => {
    const c = new AbortController();
    Promise.all([loadData<CellTable>('rhythm_cells.json', c.signal), loadData<Summary>('rhythm_cells_summary.json', c.signal)])
      .then(([g, s]) => { setCells(decodeCells(g)); setSummary(s); })
      .catch(e => { if (e.name !== 'AbortError') setError('The per-cell results have not been published.'); });
    loadData<Land>('world-land.json', c.signal).then(setLand).catch(() => {});
    return () => c.abort();
  }, []);
  const props = useMemo(() => (cells?.features || []).map(f => f.properties).filter(p => p.country === country), [cells, country]);
  const countries = useMemo(() => [...new Set((cells?.features || []).map(f => f.properties.country))], [cells]);
  const view = useMemo(() => {
    if (!props.length) return null;
    const minLon = Math.min(...props.map(p => p.cell_lon)) - 2, maxLon = Math.max(...props.map(p => p.cell_lon)) + 3;
    const minLat = Math.min(...props.map(p => p.cell_lat)) - 2, maxLat = Math.max(...props.map(p => p.cell_lat)) + 3;
    const k = Math.cos(((minLat + maxLat) / 2) * Math.PI / 180);
    const W = 720, scale = W / ((maxLon - minLon) * k), H = Math.min(620, (maxLat - minLat) * scale);
    const s = Math.min(scale, H / (maxLat - minLat));
    const x = (lon: number) => (lon - minLon) * k * s, y = (lat: number) => (maxLat - lat) * s;
    const landPath: string[] = [];
    for (const feature of land?.features || []) {
      const polys = (feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates) as number[][][][];
      for (const poly of polys) for (const ring of poly) {
        if (!ring.some(([lo, la]) => lo >= minLon - 5 && lo <= maxLon + 5 && la >= minLat - 5 && la <= maxLat + 5)) continue;
        landPath.push('M' + ring.map(([lo, la]) => `${x(lo).toFixed(1)},${y(la).toFixed(1)}`).join('L') + 'Z');
      }
    }
    return {x, y, w: (maxLon - minLon) * k * s, h: (maxLat - minLat) * s, cw: k * s, ch: s, land: landPath.join('')};
  }, [props, land]);

  if (error) return <section className="panel"><p className="panel-description">{error}</p></section>;
  if (!cells || !summary || !view) return <section className="panel"><div className="loading-state" role="status"><span className="loader"/><h2>Loading the per-cell map…</h2></div></section>;
  const sig = props.filter(p => p.significant);
  const check = summary.aqua_check[country], all = summary.aqua_check.ALL;
  const hl = HIGHLIGHTS[country];
  const hlStats = hl && (() => {
    const inside = props.filter(hl.test), outside = props.filter(hl.restTest), s = inside.filter(p => p.significant);
    const withAqua = s.filter(p => typeof p.aqua_rest_index === 'number');
    return {n: inside.length, sig: s.length, med: median(inside.map(p => p.rest_index)), aqua: withAqua.length,
      aquaBelow: withAqua.filter(p => (p.aqua_rest_index as number) < 1).length, aquaSig: withAqua.filter(p => p.aqua_significant).length,
      outN: outside.length, outSig: outside.filter(p => p.significant).length, outMed: median(outside.map(p => p.rest_index))};
  })();

  return <section className="panel" aria-labelledby="rh-map-title">
    <div className="panel-heading"><div><span className="rh-exploratory"><FlaskConical size={11}/> EXPLORATORY</span>
      <h2 id="rh-map-title">Where is the dip? One-degree cells</h2></div></div>
    <p className="panel-description">Not part of the pre-specified test. The same weekday method run for every 1° cell with enough VIIRS detections (at least 300 a year on average and 8 usable years), with a false-discovery correction (Benjamini-Hochberg, 5%) across all cells. Aqua is computed the same way as a check.</p>
    <div className="rh-country-picker" role="group" aria-label="Country map">{countries.map(c => <button key={c} className={c === country ? 'active' : ''} aria-pressed={c === country} onClick={() => { setCountry(c); setActive(null); }}>{NAMES[c] || c}<small>{cells.features.find(f => f.properties.country === c)?.properties.rest_day}</small></button>)}</div>
    <div className="rh-map-wrap">
      <svg className="rh-map" viewBox={`0 0 ${view.w.toFixed(0)} ${view.h.toFixed(0)}`} role="group" aria-label={`${NAMES[country]}: ${props.length} cells analysed, ${sig.length} with a significant Sunday dip. Select a cell for its values.`}>
        <path d={view.land} fill="#22333a" stroke="#3a4d55" strokeWidth={0.6}/>
        {props.map(p => <rect key={`${p.cell_lat}:${p.cell_lon}`} x={view.x(p.cell_lon)} y={view.y(p.cell_lat + 1)} width={view.cw} height={view.ch}
          fill={color(p.rest_index)} className={`rh-cell ${p.significant ? 'sig' : ''}`} tabIndex={0}
          aria-label={`Cell ${lat(p.cell_lat)} to ${lat(p.cell_lat + 1)}, ${lon(p.cell_lon)} to ${lon(p.cell_lon + 1)}: Sunday index ${f3(p.rest_index)}${p.significant ? ', significant' : ''}`}
          onMouseEnter={() => setActive(p)} onFocus={() => setActive(p)} onClick={() => setActive(p)}/>)}
      </svg>
      <div className="rh-legend">
        <div><div className="rh-ramp"/><div className="rh-ramp-labels"><span>0.7</span><span>1.0</span><span>1.3+</span></div>
          <small>Sunday index (1.0 = average day). Blue = fewer Sunday detections.</small></div>
        <div><span className="rh-swatch"/>Significant after Benjamini-Hochberg (q &lt; 0.05)</div>
        <div className="rh-tooltip" aria-live="polite">{active ? <>
          <strong>{lat(active.cell_lat)} to {lat(active.cell_lat + 1)}, {lon(active.cell_lon)} to {lon(active.cell_lon + 1)}</strong><br/>
          VIIRS Sunday {f3(active.rest_index)} (95% CI {f3(active.ci_lo)}–{f3(active.ci_hi)}), q {f3(active.q_bh)}{active.significant ? ', significant' : ''}<br/>
          Aqua Sunday {typeof active.aqua_rest_index === 'number' ? `${f3(active.aqua_rest_index)}${active.aqua_significant ? ', significant' : ''}` : 'too few detections'}<br/>
          <small>{Math.round(active.mean_detections_per_year).toLocaleString()} VIIRS detections a year · {active.years} years</small></> : 'Select a cell to see its values.'}</div>
        <div><strong>{NAMES[country]}</strong>: {props.length} cells analysed, {sig.length} significant.</div>
        {check && <div>Aqua check: {check.cells_with_both} cells have both satellites; their Sunday indices correlate at r = {f3(check.corr_rest_index)}. Of {check.viirs_sig_cells_with_aqua} VIIRS-significant cells with Aqua data, {check.of_those_aqua_below_1} are also below 1 in Aqua and {check.of_those_aqua_significant} are significant in Aqua.</div>}
      </div>
    </div>
    {hl && hlStats && <div className="rh-finding"><strong>{hl.title}.</strong> {hlStats.sig} of {hlStats.n} cells have a significant Sunday dip (median index {f3(hlStats.med)}). Of the {hlStats.aqua} significant cells that Aqua can also measure, {hlStats.aquaBelow} are below 1 in Aqua and {hlStats.aquaSig} are significant in Aqua. In the {hl.rest}, {hlStats.outSig} of {hlStats.outN} cells are significant (median {f3(hlStats.outMed)}). {country === 'India' && summary.northeast_india_area && <>Of the {hlStats.n} northeast cells, {summary.northeast_india_area.northeast_cross_border.cells} lie mostly outside India (their detections come from the Indian side of the border); using only the {summary.northeast_india_area.northeast_mostly_india.cells} cells mostly inside India, {summary.northeast_india_area.northeast_mostly_india.significant} are significant (median {f3(summary.northeast_india_area.northeast_mostly_india.median_sunday_index)}). </>}The area boundary was drawn after looking at the map; it is a description, not a test. This descriptive pattern does not establish ignition cause.{hl.context && <><br/><br/>{hl.context}</>}</div>}
    {all && <p className="chart-note">All four countries: Aqua and VIIRS Sunday indices correlate at r = {f3(all.corr_rest_index)} across {all.cells_with_both} shared cells. Neighbouring cells share weather and farming practice, so a cluster of significant cells is one regional pattern, not many independent findings. Grey land means too few detections to analyse, not "no dip".</p>}
    <span className="chart-label">{cells.metadata.label} · EXPLORATORY</span>
  </section>;
}
