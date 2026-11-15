import {useEffect, useState} from 'react';
import {AlertTriangle, ArrowDownToLine, ArrowUpRight, RotateCcw} from 'lucide-react';
import './frp.css';

interface FrpStream {
  stream: string;
  name: string;
  count_weekdays: number[];
  frp_weekdays: number[];
  count_sunday: number;
  frp_sunday: number;
  delta: number;
  ci_low: number;
  ci_high: number;
  passed: boolean;
  loyo_min: number;
  max_day_removed_delta: number;
}

export interface FrpPayload {
  version: number;
  label: string;
  scope: {country: string; years: number[]; source_type: number; subset: string; year_blocks: number};
  protocol: {sha256: string; frozen_utc: string; git_receipt_commit: string; git_receipt_after_original_results: boolean; chronology_note: string};
  verdict: string;
  pass_sentence: string;
  weekdays: string[];
  inference: {baseline: number; ci_percent: number; bootstrap_draws: number; point_threshold: number};
  streams: FrpStream[];
  masks: {name: string; excluded_days: number; passing_streams: string[]; streams: FrpStream[]}[];
  data_gate: {passed: boolean; valid_frp_fraction: number; records_primary: number; records_padded: number};
  limitations: string[];
  evidence: Record<'chart' | 'report' | 'protocol' | 'summary' | 'annual' | 'verification', string>;
}

const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value);
const index = (value: number) => value.toFixed(3);
const signed = (value: number) => `${value > 0 ? '+' : value < 0 ? '−' : ''}${Math.abs(value).toFixed(3)}`;

/** Reject incomplete evidence instead of drawing plausible-looking values. */
export function parseFrpPayload(value: unknown): FrpPayload {
  if (!object(value) || value.version !== 1 || typeof value.label !== 'string' || typeof value.pass_sentence !== 'string'
      || !object(value.scope) || !object(value.protocol) || !object(value.inference) || !object(value.data_gate)
      || !object(value.evidence) || !Array.isArray(value.streams) || !Array.isArray(value.masks)
      || !Array.isArray(value.weekdays) || value.weekdays.length !== 7 || !value.weekdays.every(d => typeof d === 'string')
      || !Array.isArray(value.limitations) || !value.limitations.every(d => typeof d === 'string')) throw new Error('Incomplete FRP evidence');
  const {scope, protocol, inference, data_gate: gate, evidence} = value;
  if (scope.country !== 'United States' || scope.subset !== 'daytime' || !finite(scope.year_blocks)
      || !Array.isArray(scope.years) || scope.years.length !== 2 || !scope.years.every(finite)
      || typeof protocol.sha256 !== 'string' || !/^[a-f\d]{64}$/i.test(protocol.sha256)
      || typeof protocol.git_receipt_commit !== 'string' || !/^[a-f\d]{40}$/i.test(protocol.git_receipt_commit)
      || protocol.git_receipt_after_original_results !== true || typeof protocol.chronology_note !== 'string'
      || typeof protocol.frozen_utc !== 'string' || !Number.isFinite(Date.parse(protocol.frozen_utc))
      || !finite(inference.baseline) || inference.baseline <= 0 || !finite(inference.ci_percent)
      || inference.ci_percent <= 0 || inference.ci_percent >= 100 || !finite(inference.bootstrap_draws)
      || !finite(inference.point_threshold) || !finite(gate.valid_frp_fraction)
      || !finite(gate.records_primary) || !finite(gate.records_padded)) throw new Error('Invalid FRP scope or provenance');
  const streamValid = (row: unknown): row is FrpStream => {
    if (!object(row) || typeof row.stream !== 'string' || typeof row.name !== 'string' || typeof row.passed !== 'boolean'
        || !['count_sunday', 'frp_sunday', 'delta', 'ci_low', 'ci_high', 'loyo_min', 'max_day_removed_delta'].every(k => finite(row[k]))
        || !['count_weekdays', 'frp_weekdays'].every(k => Array.isArray(row[k]) && row[k].length === 7 && row[k].every((n: unknown) => finite(n) && n >= 0))) return false;
    const r = row as unknown as FrpStream;
    return r.ci_low <= r.ci_high && Math.abs(r.count_sunday - r.count_weekdays[6]) < 1e-9
      && Math.abs(r.frp_sunday - r.frp_weekdays[6]) < 1e-9 && Math.abs(r.delta - (r.frp_sunday - r.count_sunday)) < 1e-9;
  };
  const streams = value.streams, masks = value.masks;
  if (streams.length !== 3 || !streams.every(streamValid)
      || new Set(streams.map(r => r.stream)).size !== 3
      || !['Terra', 'Aqua', 'VIIRS'].every(s => streams.some(r => r.stream === s))
      || !masks.every(mask => object(mask) && typeof mask.name === 'string' && finite(mask.excluded_days)
        && Array.isArray(mask.passing_streams) && mask.passing_streams.every(s => typeof s === 'string')
        && Array.isArray(mask.streams) && mask.streams.length === 3 && mask.streams.every(streamValid))
      || !['primary', 'padded'].every(name => masks.some(m => object(m) && m.name === name))) throw new Error('Invalid FRP profiles');
  for (const key of ['chart', 'report', 'protocol', 'summary', 'annual', 'verification']) {
    if (typeof evidence[key] !== 'string' || !/^\/?evidence\/frp\/[\w./-]+$/.test(evidence[key]) || evidence[key].includes('..')) throw new Error('Invalid evidence link');
  }
  if (value.verdict !== 'pass' || gate.passed !== true || streams.filter(r => r.passed).length < 2) throw new Error('The published FRP test is not established');
  const criteriaMet = (row: FrpStream) => row.delta >= Number(inference.point_threshold) && row.ci_low > 0 && row.loyo_min > 0 && row.max_day_removed_delta > 0;
  const checkedMasks = masks as FrpPayload['masks'];
  if (streams.some(row => row.passed && !criteriaMet(row))
      || checkedMasks.some(mask => mask.streams.some(row => row.passed && !criteriaMet(row)))
      || streams.filter(row => row.passed && checkedMasks.every(mask => mask.streams.some(m => m.stream === row.stream && m.passed))).length < 2) throw new Error('Inconsistent FRP criteria');
  return value as unknown as FrpPayload;
}

function FrpHeading() {
  return <div className="panel-heading frp-heading"><div><span className="eyebrow">PRE-SPECIFIED ROBUSTNESS TEST · US DAYTIME</span><h2 id="frp-title">Count the detections. Compare their power.</h2></div></div>;
}

function Profile({row, data, bounds}: {row: FrpStream; data: FrpPayload; bounds: [number, number]}) {
  const W = 320, H = 188, L = 34, R = 14, T = 18, B = 30;
  const [low, high] = bounds;
  const x = (i: number) => L + i * (W - L - R) / (data.weekdays.length - 1);
  const y = (n: number) => T + (high - n) / (high - low) * (H - T - B);
  const ticks = Array.from({length: Math.round((high - low) / .2) + 1}, (_, i) => low + i * .2);
  const points = (values: number[]) => values.map((n, i) => `${x(i)},${y(n)}`).join(' ');
  const description = data.weekdays.map((day, i) => `${day}: count ${index(row.count_weekdays[i])}, observed FRP ${index(row.frp_weekdays[i])}`).join('; ');
  return <svg className="frp-profile" viewBox={`0 0 ${W} ${H}`} role="img"
    aria-label={`${row.name}, weekday profiles. Baseline ${data.inference.baseline}. ${description}`}>
    <rect className="frp-sunday-band" x={x(6) - 12} y={T} width="24" height={H - T - B}/>
    {ticks.map(t => <g key={t}><line className={Math.abs(t - data.inference.baseline) < 1e-8 ? 'frp-baseline' : 'frp-grid'} x1={L} x2={W - R} y1={y(t)} y2={y(t)}/>
      <text className="frp-axis" x={L - 8} y={y(t) + 4} textAnchor="end">{t.toFixed(1)}</text></g>)}
    <polyline className="frp-count-line" points={points(row.count_weekdays)}/>
    <polyline className="frp-power-line" points={points(row.frp_weekdays)}/>
    {data.weekdays.map((day, i) => <g key={day}>
      <circle className="frp-count-point" cx={x(i)} cy={y(row.count_weekdays[i])} r="3"/>
      <path className="frp-power-point" d={`M${x(i)},${y(row.frp_weekdays[i]) - 4}l4,4l-4,4l-4,-4Z`}/>
      <text className={`frp-axis ${i === 6 ? 'frp-sunday-label' : ''}`} x={x(i)} y={H - 9} textAnchor="middle">{day}</text>
    </g>)}
  </svg>;
}

export default function FrpComparison() {
  const [data, setData] = useState<FrpPayload | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    setData(null);
    fetch(`${import.meta.env.BASE_URL}data/frp.json`, {signal: controller.signal, cache: 'no-cache'})
      .then(response => { if (!response.ok) throw new Error('FRP evidence unavailable'); return response.json(); })
      .then(parseFrpPayload)
      .then(value => { if (!controller.signal.aborted) setData(value); })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [attempt]);
  const heading = <FrpHeading/>;
  if (error) return <section className="panel frp-panel" aria-labelledby="frp-title">{heading}
    <div className="frp-load-note" role="status"><AlertTriangle size={18}/><p>The count-versus-power comparison could not be loaded. The other rhythm results remain available.</p></div>
    <button className="button" onClick={() => setAttempt(n => n + 1)}><RotateCcw size={15}/> Retry comparison</button>
  </section>;
  if (!data) return <section className="panel frp-panel" aria-labelledby="frp-title" aria-busy="true">{heading}<p className="frp-load-note" role="status">Loading the count-versus-power evidence…</p></section>;
  return <FrpEvidence data={data}/>;
}

/** Pure evidence view also used by the source-to-render contract test. */
export function FrpEvidence({data}: {data: FrpPayload}) {
  const values = data.streams.flatMap(row => [...row.count_weekdays, ...row.frp_weekdays]);
  const bounds: [number, number] = [Math.max(0, Math.floor(Math.min(...values, data.inference.baseline) * 5) / 5 - .2), Math.ceil(Math.max(...values, data.inference.baseline) * 5) / 5 + .2];
  const evidence = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\/+/, '')}`;
  const ciLabel = `${data.inference.ci_percent.toFixed(2)}%`;
  const receiptUrl = `https://github.com/Water-Mal0ne/FIRETRACE/blob/${data.protocol.git_receipt_commit}/DECISIONS.md`;
  return <section className="panel frp-panel" aria-labelledby="frp-title"><FrpHeading/>
    <p className="frp-scope">Fixed US daytime study · {data.scope.years.join('–')} · {data.scope.year_blocks} equally weighted years. The all/daytime selector above does not change this separate test.</p>
    <p className="frp-result">{data.pass_sentence}</p>
    <p className="frp-chronology">The protocol was recorded locally before the original analysis. <a href={receiptUrl} target="_blank" rel="noreferrer">Git receipt {data.protocol.git_receipt_commit.slice(0, 7)}</a> was added after the results; it is not prior Git registration.</p>
    <p className="frp-description">A detection count gives each observed hotspot equal weight. FRP weights those same detections by the radiative power reported by the satellite. Both profiles use their own average weekday as the baseline.</p>
    <div className="frp-legend" aria-label="Chart legend"><span><i className="frp-count-key"/> Detection count</span><span><i className="frp-power-key"/> Observed radiative power (FRP)</span></div>
    <div className="frp-streams">{data.streams.map(row => <article className="frp-stream" key={row.stream} data-frp-stream={row.stream}>
      <div className="frp-stream-heading"><h3>{row.name}</h3><span className={`frp-status ${row.passed ? 'is-pass' : 'is-uncertain'}`}>{row.passed ? 'Criteria met' : 'Criteria not met'}</span></div>
      <Profile row={row} data={data} bounds={bounds}/>
      <dl className="frp-facts"><div><dt>Sunday count index</dt><dd>{index(row.count_sunday)}</dd></div><div><dt>Sunday FRP index</dt><dd>{index(row.frp_sunday)}</dd></div>
        <div className="frp-difference"><dt>FRP minus count</dt><dd>{signed(row.delta)}</dd><small>{ciLabel} interval: {signed(row.ci_low)} to {signed(row.ci_high)}</small></div></dl>
      {!row.passed && <p className="frp-uncertain-note">{row.ci_low <= 0 && row.ci_high >= 0 ? 'The interval includes zero. This stream does not establish a difference.' : 'This stream does not meet all the fixed criteria.'}</p>}
    </article>)}</div>
    <p className="frp-chart-note">Baseline {data.inference.baseline.toFixed(1)} = average weekday. Lines show equal-year mean indices; the interval shown below each chart applies to the Sunday difference. These are separately observed streams, not harmonized FRP.</p>
    <details className="frp-details"><summary>Read the values and test criteria</summary>
      <p>The mean Sunday difference must reach {data.inference.point_threshold.toFixed(2)}, its adjusted interval must be above zero, and its direction must remain positive after leaving out each year and removing each year’s largest-FRP day. The same passing streams must satisfy the criteria under both outage masks.</p>
      <p>Intervals use {data.inference.bootstrap_draws.toLocaleString()} shared whole-year bootstrap draws across {data.scope.year_blocks} year blocks. These are project criteria, not a NASA standard.</p>
      <div className="frp-table-wrap" tabIndex={0} role="region" aria-label="Weekday count and FRP indices, scroll horizontally if needed"><table>
        <caption>Primary common-date mask · count and FRP use the same detections</caption>
        <thead><tr><th scope="col">Stream / measure</th>{data.weekdays.map(day => <th scope="col" key={day}>{day}</th>)}</tr></thead>
        <tbody>{data.streams.flatMap(row => [<tr key={`${row.stream}-count`}><th scope="row">{row.name} · count</th>{row.count_weekdays.map((n, i) => <td key={i}>{index(n)}</td>)}</tr>,
          <tr key={`${row.stream}-frp`}><th scope="row">{row.name} · FRP</th>{row.frp_weekdays.map((n, i) => <td key={i}>{index(n)}</td>)}</tr>])}</tbody>
      </table></div>
      <ul className="frp-mask-list">{data.masks.map(mask => <li key={mask.name}>{mask.name === 'padded' ? 'Outage mask padded by one day' : 'Primary outage mask'}: {mask.excluded_days} excluded dates; passing streams: {mask.passing_streams.map(s => data.streams.find(row => row.stream === s)?.name || s).join(', ')}.</li>)}</ul>
    </details>
    <div className="frp-limits" role="note"><AlertTriangle size={18}/><div><strong>What this comparison cannot establish</strong><p>Summed FRP is sampled radiative power, not energy, emissions, burned area or fire counts. It does not establish fire size, severity or human causes. These observations share weather, cloud and sampling limitations.</p></div></div>
    <details className="frp-details frp-provenance"><summary>Protocol timing and reproducible evidence</summary>
      <p>{data.protocol.chronology_note}</p>
      <p>Original local protocol record: <time dateTime={data.protocol.frozen_utc}>{data.protocol.frozen_utc.replace('T', ' ').replace('Z', ' UTC')}</time>. <a href={receiptUrl} target="_blank" rel="noreferrer">Later Git receipt {data.protocol.git_receipt_commit.slice(0, 7)} <ArrowUpRight size={12}/></a>. This commit does not precede the results.</p>
      <p className="frp-hash">Original protocol SHA-256: <code>{data.protocol.sha256}</code></p>
      <ul>{data.limitations.map(item => <li key={item}>{item}</li>)}</ul>
      <nav className="frp-downloads" aria-label="Download FRP evidence">
        <a href={evidence(data.evidence.summary)} download><ArrowDownToLine size={14}/> Summary CSV</a>
        <a href={evidence(data.evidence.annual)} download><ArrowDownToLine size={14}/> Annual differences CSV</a>
        <a href={evidence(data.evidence.protocol)} download><ArrowDownToLine size={14}/> Original protocol</a>
        <a href={evidence(data.evidence.verification)} download><ArrowDownToLine size={14}/> Independent check</a>
        <a href={evidence(data.evidence.report)} download><ArrowDownToLine size={14}/> Full report</a>
        <a href={evidence(data.evidence.chart)} download><ArrowDownToLine size={14}/> Chart</a>
      </nav>
    </details>
    <span className="frp-data-label">{data.label}</span>
  </section>;
}
