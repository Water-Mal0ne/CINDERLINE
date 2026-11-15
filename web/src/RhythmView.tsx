import {useEffect, useMemo, useRef, useState} from 'react';
import {AlertTriangle, ShieldCheck, Waves} from 'lucide-react';
import {invalidateData, loadData} from './loadData';
import {validRhythmPayload} from './rhythmData';
import FrpComparison from './FrpComparison';
import './rhythm.css';
import './rhythm-workspace.css';

type Num = number | null;
export interface RhythmDay {day: string; index: Num; lo: Num; hi: Num}
export interface RhythmStreamRow {
  stream: string; status: string; detections: number; years?: number; rest_index?: Num; lowest_day?: string;
  rest_is_lowest?: boolean; p_null?: Num; bonferroni_m?: number; significant?: boolean; weekdays?: RhythmDay[];
}
interface CountryRow {country: string; name: string; rest_day: string; status: string; streams: RhythmStreamRow[]; daytime_streams: RhythmStreamRow[]}
interface Check {passed: boolean; [key: string]: unknown}
interface RobustnessCountry {ci_upper_below_one: Check; strict_reanalysis: Check; matched_static_controls: Check; failed: string[]; all_passed: boolean}
export interface RhythmPayload {
  label: string;
  official: {decision: string; rule: string; source: string; countries_passing: string[];
    per_country: Record<string, {status: string; streams_significant: number; streams_with_data: number; predicted_rest_day: string}>};
  sunday_caveat: string | null;
  headline?: string | null;
  robustness: null | {role: string; descriptions: Record<string, string>; per_country: Record<string, RobustnessCountry>; flagged: Record<string, string[]>; notes?: Record<string, string>; control_nuance?: string | null; source?: string};
  countries: CountryRow[];
  negative_control: {stream: string; status: string; detections: number; max_abs_deviation?: number}[];
  caveats: string[]; wording: string;
}

const CHECK_LABELS: Record<string, string> = {
  ci_upper_below_one: 'Upper bound below 1',
  strict_reanalysis: 'Strict re-analysis',
  matched_static_controls: 'Matched static controls',
};
const fmt = (v: Num | undefined, d = 3) => (typeof v === 'number' && Number.isFinite(v) ? v.toFixed(d) : '—');
const pct = (v: Num | undefined) => (typeof v === 'number' ? `${Math.round((v - 1) * 100)}%` : '—');

export function WeekdayChart({row, rest}: {row: RhythmStreamRow; rest: string}) {
  const days = row.weekdays || [];
  const values = days.flatMap(d => [d.lo, d.hi, d.index]).filter((v): v is number => typeof v === 'number');
  const lo = Math.min(0.6, ...values) - 0.05, hi = Math.max(1.4, ...values) + 0.05;
  const W = 300, H = 170, L = 34, R = 8, T = 10, B = 24;
  const y = (v: number) => T + (hi - v) / (hi - lo) * (H - T - B);
  const step = (W - L - R) / 7;
  const ticks = [0.6, 0.8, 1, 1.2, 1.4].filter(t => t > lo && t < hi);
  const summary = days.map(d => `${d.day} ${fmt(d.index, 2)} (95% CI ${fmt(d.lo, 2)} to ${fmt(d.hi, 2)})`).join('; ');
  return <svg className="rh-chart" viewBox={`0 0 ${W} ${H}`} role="img"
    aria-label={`${row.stream} weekday index, 1.0 is an average day, predicted rest day ${rest}: ${summary}`}>
    {ticks.map(t => <g key={t}><line x1={L} x2={W - R} y1={y(t)} y2={y(t)} className={t === 1 ? 'rh-one' : 'rh-grid'}/>
      <text x={L - 5} y={y(t) + 3} textAnchor="end" className="rh-tick">{t.toFixed(1)}</text></g>)}
    {days.map((d, i) => {
      const x = L + i * step + step * 0.2, w = step * 0.6, isRest = d.day === rest;
      if (typeof d.index !== 'number') return null;
      const top = Math.min(y(d.index), y(1)), height = Math.max(1, Math.abs(y(d.index) - y(1)));
      return <g key={d.day}>
        <rect x={x} y={top} width={w} height={height} rx={2} className={isRest ? 'rh-bar rest' : 'rh-bar'}/>
        {typeof d.lo === 'number' && typeof d.hi === 'number' && <g className="rh-whisker">
          <line x1={x + w / 2} x2={x + w / 2} y1={y(d.hi)} y2={y(d.lo)}/>
          <line x1={x + w / 2 - 4} x2={x + w / 2 + 4} y1={y(d.hi)} y2={y(d.hi)}/>
          <line x1={x + w / 2 - 4} x2={x + w / 2 + 4} y1={y(d.lo)} y2={y(d.lo)}/></g>}
        <text x={x + w / 2} y={H - 7} textAnchor="middle" className={isRest ? 'rh-day rest' : 'rh-day'}>{d.day}</text>
      </g>;
    })}
  </svg>;
}

function StreamCard({row, rest}: {row: RhythmStreamRow; rest: string}) {
  if (row.status !== 'ok' || !row.weekdays) return <div className="rh-stream empty"><h3>{row.stream}</h3><p>Not enough complete years ({row.detections.toLocaleString()} detections).</p></div>;
  const restDay = row.weekdays.find(d => d.day === rest);
  return <article className="rh-stream">
    <div className="rh-stream-head"><h3>{row.stream}</h3>{row.significant
      ? <span className="rh-chip sig">significant</span> : <span className="rh-chip">not significant</span>}</div>
    <WeekdayChart row={row} rest={rest}/>
    <dl className="rh-facts">
      <div><dt>{rest} index</dt><dd>{fmt(row.rest_index)} <small>({pct(row.rest_index)})</small></dd></div>
      <div><dt>95% CI</dt><dd>{fmt(restDay?.lo)}–{fmt(restDay?.hi)}</dd></div>
      <div><dt>Lowest day</dt><dd>{row.lowest_day}</dd></div>
      <div><dt>p (null test)</dt><dd>{fmt(row.p_null, 4)}</dd></div>
    </dl>
    <p className="rh-small">{row.years} complete years · {row.detections.toLocaleString()} detections</p>
  </article>;
}

export default function RhythmView({children}: {children?: React.ReactNode}) {
  const [data, setData] = useState<RhythmPayload | null>(null), [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [country, setCountry] = useState('United_States'), [subset, setSubset] = useState<'all' | 'day'>('all');
  const [detailsRequest, setDetailsRequest] = useState(0);
  const [analysisView, setAnalysisView] = useState<'charts' | 'results' | 'map'>('charts');
  const [mapOpened, setMapOpened] = useState(false);
  const [showFrp, setShowFrp] = useState(false);
  const countryTitle = useRef<HTMLHeadingElement | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setError('');
    loadData<RhythmPayload>('rhythm.json', controller.signal)
      .then(value => {
        if (!validRhythmPayload(value)) throw new Error('Invalid weekday data');
        if (!controller.signal.aborted) setData(value);
      })
      .catch(() => { if (!controller.signal.aborted) setError('The rhythm results could not be loaded. Please try again.'); });
    return () => controller.abort();
  }, [attempt]);
  const selected = useMemo(() => data?.countries.find(c => c.country === country), [data, country]);
  useEffect(() => {
    if (!detailsRequest || analysisView !== 'charts') return;
    countryTitle.current?.focus({preventScroll: true});
    countryTitle.current?.scrollIntoView({block: 'start'});
  }, [detailsRequest]);
  if (error) return <div role="alert" className="error-banner rh-load-error"><AlertTriangle size={20}/><div><strong>Data not available</strong><p>{error}</p></div><button type="button" className="button" onClick={() => { invalidateData('rhythm.json'); setAttempt(n => n + 1); }}>Retry weekday analysis</button></div>;
  if (!data) return <div className="loading-state" role="status"><span className="loader"/><h2>Loading the weekday analysis…</h2></div>;
  const official = data.official, passed = official.decision === 'pass';
  const passing = Object.entries(official.per_country).filter(([, v]) => v.status === 'pass').map(([c]) => c);
  const flagged = data.robustness?.flagged || {};
  const nameOf = (c: string) => data.countries.find(x => x.country === c)?.name || c;
  const rows = selected ? (subset === 'all' ? selected.streams : selected.daytime_streams) : [];
  const testCount = data.countries.flatMap(c => c.streams).find(r => typeof r.bonferroni_m === 'number')?.bonferroni_m ?? '—';

  return <div className="rhythm-page rhythm-workspace">
    <p className="rh-page-intro">The test uses a stated expected rest day for each country. These weekday associations do not establish ignition cause or identify who burns or why.</p>
    <nav className="rh-analysis-nav" aria-label="Rhythm analysis views">
      {([['charts', 'Weekday charts'], ['results', 'Country results'], ['map', 'Spatial patterns']] as const).map(([key, title]) =>
        <button key={key} type="button" aria-pressed={analysisView === key} aria-controls={`rh-analysis-${key}`} onClick={() => { setAnalysisView(key); if (key === 'map') setMapOpened(true); }}>{title}</button>)}
    </nav>
    <div id="rh-analysis-charts" className="rh-analysis-content" hidden={analysisView !== 'charts'}>
    {selected && <section className="panel rh-charts-panel" id="rh-country-panel" aria-labelledby="rh-country-title">
      <h2 className="rh-visually-hidden" id="rh-country-title" ref={countryTitle} tabIndex={-1}>{selected.name}</h2>
      <div className="rh-chart-toolbar"><label className="rh-country-select" htmlFor="rh-country-select"><span>Country</span>
        <select id="rh-country-select" value={country} onChange={event => setCountry(event.target.value)}>{data.countries.map(c => <option key={c.country} value={c.country}>{c.name}</option>)}</select>
      </label><span className="rh-prediction">Predicted rest day <strong>{selected.rest_day}</strong></span>
      <div className="segmented" role="group" aria-label="Detections included">{(['all', 'day'] as const).map(s => <button key={s} className={subset === s ? 'active' : ''} aria-pressed={subset === s} onClick={() => setSubset(s)}>{s === 'all' ? 'All detections' : 'Daytime only'}</button>)}</div></div>
      <div className="rh-streams">{rows.map(r => <StreamCard key={r.stream} row={r} rest={selected.rest_day}/>)}</div>
      <p className="chart-note">Bars show each weekday's index relative to an average day (1.0). Orange = predicted rest day. Whiskers = 95% intervals from resampling whole years. Terra, Aqua and VIIRS observe many of the same fires, so agreement between them is corroboration, not independent replication.{subset === 'day' ? ' Daytime-only results are a sensitivity check and are not used by the gate.' : ''}</p>
    </section>}

      {selected && data.robustness?.notes?.[country] && <p className="rh-selected-caveat" role="note">{data.robustness.notes[country]}</p>}
      {country === 'United_States' && <details className="rh-disclosure rh-frp-disclosure" open={showFrp} onToggle={event => setShowFrp(event.currentTarget.open)}>
        <summary><span>Radiative power</span><small>US daytime study</small></summary>
        {showFrp && <FrpComparison/>}
      </details>}
    </div>
    <div id="rh-analysis-results" className="rh-analysis-content" hidden={analysisView !== 'results'}>
    <section className="panel rh-verdict" aria-labelledby="rh-verdict-title">
      <div className="panel-heading"><div>
        <h2 id="rh-verdict-title">{passed ? 'The pre-specified rule passes, narrowly' : `Decision: ${official.decision.replaceAll('_', ' ')}`}</h2></div>
        <span className={`gate-badge ${passed ? 'pass' : ''}`}><ShieldCheck size={13}/>{official.decision.replaceAll('_', ' ')}</span></div>
      {data.headline && <p className="rh-headline">{data.headline}</p>}
      {data.sunday_caveat && <div className="rh-caveat" role="note"><AlertTriangle size={18}/><p>{data.sunday_caveat}</p></div>}
      <p className="panel-description">{passing.map(nameOf).join(', ') || 'No country'} passed: the predicted rest day is the lowest weekday and significant after correction in at least two satellite streams. The United States is the replication check. Source: {official.source}.</p>
      <div className="table-scroll" role="group" aria-labelledby="rh-verdict-title" tabIndex={0}><table className="rh-table"><thead><tr><th scope="col">Country</th><th scope="col">Rest day</th><th scope="col">Result</th><th scope="col">Streams significant</th><th scope="col">Terra</th><th scope="col">Aqua</th><th scope="col">VIIRS</th></tr></thead>
        <tbody>{data.countries.map(c => <tr key={c.country} className={c.country === country ? 'active' : ''}>
          <th scope="row"><button className="rh-link" aria-pressed={c.country === country} aria-controls="rh-country-panel" onClick={() => { setCountry(c.country); setAnalysisView('charts'); setDetailsRequest(n => n + 1); }}>{c.name}</button></th><td>{c.rest_day}</td>
          <td><span className={`rh-chip ${c.status === 'pass' ? 'sig' : ''}`}>{c.status.replaceAll('_', ' ')}</span></td>
          <td>{official.per_country[c.country]?.streams_significant ?? 0} of {official.per_country[c.country]?.streams_with_data ?? 0}</td>
          {['Terra', 'Aqua', 'VIIRS'].map(s => { const r = c.streams.find(x => x.stream === s);
            return <td key={s} className={r?.significant ? 'rh-sig' : ''}>{r?.status === 'ok' ? fmt(r.rest_index) : '—'}</td>; })}
        </tr>)}</tbody></table></div>
      <p className="chart-note">Values are the rest-day index: detections on the rest day divided by an average day (1.000 = average). Bold = significant after Bonferroni correction across all {testCount} country-stream tests.</p>
    </section>

    {data.robustness && <section className="panel" aria-labelledby="rh-robust-title">
      <div className="panel-heading"><div><h2 id="rh-robust-title">Stricter checks on the passing countries</h2><p className="rh-small">Robustness checks · do not change the decision</p></div></div>
      {Object.keys(flagged).length > 0
        ? <div className="rh-caveat warn" role="note"><AlertTriangle size={18}/><div><p><strong>Not every robustness check holds.</strong> {Object.entries(flagged).map(([c, f]) => `${nameOf(c)}: ${f.map(k => CHECK_LABELS[k] || k).join(', ')} not met`).join('. ')}.</p>
          {Object.entries(data.robustness.notes || {}).map(([c, note]) => <p key={c}>{note}</p>)}
          {data.robustness.control_nuance && <p>{data.robustness.control_nuance}</p>}</div></div>
        : <p className="panel-description">All passing countries meet all three stricter checks.</p>}
      <details className="rh-disclosure"><summary>View robustness results and definitions</summary>
      <div className="table-scroll" role="group" aria-labelledby="rh-robust-title" tabIndex={0}><table className="rh-table"><thead><tr><th scope="col">Country</th>{Object.keys(CHECK_LABELS).map(k => <th scope="col" key={k}>{CHECK_LABELS[k]}</th>)}</tr></thead>
        <tbody>{Object.entries(data.robustness.per_country).map(([c, v]) => <tr key={c}><th scope="row">{nameOf(c)}</th>
          {Object.keys(CHECK_LABELS).map(k => { const check = v[k as keyof RobustnessCountry] as Check;
            const detail = String(check.status ?? (check.streams !== undefined ? `${check.streams} of 3 streams` : '')).replaceAll('_', ' ');
            return <td key={k}><span className={`rh-chip ${check.passed ? 'sig' : 'warn'}`}>{check.passed ? 'holds' : 'not met'}</span><small className="rh-detail">{detail}</small></td>; })}
        </tr>)}</tbody></table></div>
      {data.robustness.source && <p className="chart-note">Strict re-analysis source: {data.robustness.source}.</p>}
      <ul className="rh-defs">{Object.entries(data.robustness.descriptions).map(([k, d]) => <li key={k}><strong>{CHECK_LABELS[k] || k}:</strong> {d}</li>)}</ul>
      </details>
    </section>}

    <section className="panel" aria-labelledby="rh-control-title">
      <div className="panel-heading"><div><h2 id="rh-control-title">Static heat sources</h2></div></div>
      <p className="panel-description">Gas flares, volcanoes and other static sources provide a comparison for the weekday pattern. Pooled across all seven countries, their largest weekday deviation is shown below. Per-country checks are in the robustness section above.</p>
      <div className="rh-control">{data.negative_control.map(c => <div key={c.stream}><span>{c.stream}</span><strong>{typeof c.max_abs_deviation === 'number' ? `${(c.max_abs_deviation * 100).toFixed(1)}%` : '—'}</strong><small>{c.detections.toLocaleString()} detections</small></div>)}</div>
    </section>
    </div>
    <div id="rh-analysis-map" className="rh-analysis-content" hidden={analysisView !== 'map'}>
      {mapOpened && children}
    </div>
    <details className="rh-disclosure rh-limitations"><summary>What this does and does not show</summary>
      <p>We reproduce a known weekly pattern in each satellite record separately. Independently, CINDERLINE tests whether its historical calendar survives a change of sensor and calibration.</p>
      <ul><li>{data.wording}</li>{data.caveats.map(c => <li key={c}>{c}</li>)}</ul>
      <span className="chart-label"><Waves size={12}/> {data.label}</span></details>
  </div>;
}
