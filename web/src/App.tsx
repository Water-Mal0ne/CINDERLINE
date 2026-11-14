import {useEffect, useMemo, useRef, useState} from 'react';
import {ArrowDownToLine, ArrowRight, ArrowUpRight, CalendarDays, Check, ChevronDown, CircleHelp, Database, Flame, Globe2, Layers3, MapPin, Radio, ScanLine, ShieldCheck, SlidersHorizontal, Waves, X} from 'lucide-react';
import type {Anomaly, Climatology, Daily, Evaluation, Index, Region, RhythmStream, Week} from './types';
import {aggregateWeeks, compact, exportCSV, exportICS, fmt, isoWeek, monthly, numeric, prettyDate, sum} from './utils';

type View = 'explore' | 'evidence' | 'methods';
type Mode = 'harmonized' | 'raw';
const COLORS = ['#26353b','#4e4b3d','#786040','#a86c3d','#d77945','#f89965','#ffd4ad'];
const BLANK_INDEX: Index = {label:'DATA NOT LOADED',regions:[],generated_at:'',limitations:[]};

function DataBadge({label}:{label:string}) {
  const synthetic = /synthetic|demo|simulat/i.test(label);
  return <span className={`data-badge ${synthetic ? 'synthetic' : ''}`}><span className="status-dot"/>{label}</span>;
}
function Empty({title,children}:{title:string;children?:React.ReactNode}) {
  return <div className="empty-state"><Database size={28}/><h3>{title}</h3><p>{children || 'No values are available for this selection. Missing observations are never displayed as zero.'}</p></div>;
}
function PanelTitle({eyebrow,title,children}:{eyebrow:string;title:string;children?:React.ReactNode}) {
  return <div className="panel-heading"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>{children}</div>;
}
function ChartLabel({label}:{label:string}) {return <span className="chart-label">{label}</span>;}

function CellMap({cells,selected,onSelect,name}:{cells:Region['cells'];selected:string;onSelect:(id:string)=>void;name:string}) {
  const valid = cells.filter(c => numeric(c.lon) && numeric(c.lat));
  if (!valid.length) return <div className="map-placeholder"><Globe2 size={35}/><span>Regional aggregate</span><small>Grid cells will appear when processed data are available.</small></div>;
  const minX = Math.min(...valid.map(c=>c.lon)), maxX = Math.max(...valid.map(c=>c.lon));
  const minY = Math.min(...valid.map(c=>c.lat)), maxY = Math.max(...valid.map(c=>c.lat));
  const rangeX = Math.max(maxX-minX, .5), rangeY = Math.max(maxY-minY,.5);
  const scale = Math.min(220/rangeX, 105/rangeY);
  const x = (lon:number) => 140 + (lon - (minX+maxX)/2)*scale;
  const y = (lat:number) => 85 - (lat - (minY+maxY)/2)*scale;
  return <div className="map-wrap"><svg viewBox="0 0 280 170" role="group" aria-label={`${name} grid cell centers. Use the grid selector below for keyboard selection.`}>
    <defs><pattern id="map-grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M 28 0 L 0 0 0 28" fill="none" stroke="#33444a" strokeWidth=".5"/></pattern><radialGradient id="map-glow"><stop stopColor="#e69a62" stopOpacity=".13"/><stop offset="1" stopColor="#e69a62" stopOpacity="0"/></radialGradient></defs>
    <rect width="280" height="170" fill="url(#map-grid)"/><ellipse cx="140" cy="85" rx="120" ry="65" fill="url(#map-glow)"/>
    {valid.map(c=><circle key={c.id} cx={x(c.lon)} cy={y(c.lat)} r={selected===c.id?5:2.8} fill={selected===c.id?'#fff2d5':'#ed9562'} opacity={selected==='ALL'||selected===c.id?.9:.35} onClick={()=>onSelect(c.id)} className="map-point"><title>{c.id}: {c.lat.toFixed(2)}°, {c.lon.toFixed(2)}°</title></circle>)}
    <text x="12" y="16" className="svg-micro">N ↑</text><text x="12" y="157" className="svg-micro">{minY.toFixed(1)}°–{maxY.toFixed(1)}° N</text><text x="268" y="157" textAnchor="end" className="svg-micro">{minX.toFixed(1)}°–{maxX.toFixed(1)}° E</text>
  </svg><div className="map-caption"><span><span className="map-dot"/> {fmt(valid.length)} grid centers</span><button onClick={()=>onSelect('ALL')} disabled={selected==='ALL'}>Reset</button></div></div>;
}

function Heatmap({weeks,mode,label,onSelect}:{weeks:Week[];mode:Mode;label:string;onSelect:(w:Week)=>void}) {
  const years = [...new Set(weeks.map(w=>w.year))].sort((a,b)=>b-a);
  const indexed = new Map(weeks.map(w=>[w.key,w]));
  const vals = weeks.flatMap(w=>[w.raw,w.harmonized]).filter(numeric);
  const max = Math.max(...vals, 1);
  if (!years.length) return <Empty title="No calendar data in this range"/>;
  return <><div className="calendar-scroller"><div className="calendar-grid" style={{minWidth:700}}>
    <div className="calendar-months"><span className="year-label">YEAR</span><div>{['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'].map(m=><span key={m}>{m}</span>)}</div></div>
    {years.map(year=><div className="calendar-row" key={year}><span className="year-label">{year}</span><div className="week-cells">{Array.from({length:53},(_,i)=>{
      const w=indexed.get(`${year}-${i+1}`); const v=w?.[mode]; const known=numeric(v);
      const color=known?COLORS[Math.min(6,Math.floor(Math.sqrt(Math.max(v,0)/max)*6))]:undefined;
      return <button key={i} className={`week-cell ${known?'':'missing'}`} style={{backgroundColor:color}} disabled={!w} onClick={()=>w&&onSelect(w)} aria-label={`${year}, calendar week ${i+1}: ${known?fmt(v,1)+' '+(mode==='raw'?'raw detections':'Aqua-equivalent detections'):'unavailable'}. Open evidence.`} title={`Week ${i+1} · ${known?fmt(v,1):'No value'}${w?` · ${w.rows.length} day records`:''}`}/>;
    })}</div></div>)}
  </div></div><div className="chart-bottom"><span><ScanLine size={13}/> Select a week for evidence · 7-day bins start Jan 1</span><div className="heat-legend"><span>LOW</span>{COLORS.map(c=><i key={c} style={{background:c}}/>)}<span>HIGH</span><i className="missing"/><span>UNKNOWN</span></div></div><ChartLabel label={label}/></>;
}

function TraceChart({rows,mode,label}:{rows:Daily[];mode:Mode;label:string}) {
  const points=useMemo(()=>monthly(rows),[rows]);
  const [hover,setHover]=useState<number|null>(null);
  if(!points.length) return <Empty title="No observations to compare"/>;
  const W=850,H=220,L=55,R=12,T=20,B=32;
  const max=Math.max(...points.flatMap(p=>[p.raw,p.harmonized]).filter(numeric),1)*1.06;
  const x=(i:number)=>L+(i/(Math.max(points.length-1,1)))*(W-L-R);
  const y=(v:number)=>H-B-v/max*(H-T-B);
  function path(key:Mode) {let connected=false; return points.map((p,i)=>{const v=p[key]; if(!numeric(v)){connected=false;return '';}const cmd=connected?'L':'M';connected=true;return `${cmd}${x(i).toFixed(1)},${y(v).toFixed(1)}`;}).join(' ');}
  const active=hover===null?null:points[hover];
  const indices=[0,Math.floor((points.length-1)/3),Math.floor((points.length-1)*2/3),points.length-1].filter((v,i,a)=>a.indexOf(v)===i);
  return <><div className="trace-legend"><span><i className="line-key orange"/>Aqua-equivalent</span><span><i className="line-key dashed"/>Constructed raw baseline</span><span className="unit-note">Monthly sum of available values</span></div>
  <div className="svg-chart"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Monthly raw and harmonized detections, compared on their respective reference scales" onMouseLeave={()=>setHover(null)} onMouseMove={e=>{const rect=e.currentTarget.getBoundingClientRect();setHover(Math.max(0,Math.min(points.length-1,Math.round(((e.clientX-rect.left)/rect.width*W-L)/(W-L-R)*(points.length-1)))));}}>
    {Array.from({length:4},(_,i)=>{const val=max*i/3;return <g key={i}><line x1={L} x2={W-R} y1={y(val)} y2={y(val)} stroke="#334147" strokeDasharray="3 5"/><text x={L-10} y={y(val)+4} textAnchor="end" className="svg-axis">{compact(val)}</text></g>;})}
    {indices.map(i=><text key={i} x={x(i)} y={H-6} textAnchor={i===0?'start':i===points.length-1?'end':'middle'} className="svg-axis">{points[i].date}</text>)}
    <path d={path('raw')} fill="none" stroke="#92a2a8" strokeWidth={mode==='raw'?2.4:1.6} strokeDasharray="5 4" opacity={mode==='raw'?1:.5}/>
    <path d={path('harmonized')} fill="none" stroke="#f79963" strokeWidth={mode==='harmonized'?2.8:1.8} opacity={mode==='harmonized'?1:.55}/>
    {hover!==null&&<line x1={x(hover)} x2={x(hover)} y1={T} y2={H-B} stroke="#d5dfde" opacity=".5"/>}
    {hover!==null&&numeric(points[hover][mode])&&<circle cx={x(hover)} cy={y(points[hover][mode]!)} r="4" fill="#fff0d6"/>}
  </svg></div><div className="chart-bottom"><span>{active?`${active.date} · raw ${fmt(active.raw,1)} / Aqua-equivalent ${fmt(active.harmonized,1)}`:'Move across the chart to inspect monthly values'}</span><span>Gaps remain gaps</span></div><ChartLabel label={label}/></>;
}

function SeasonChart({data,label}:{data:Climatology[];label:string}) {
  if(!data.some(d=>numeric(d.median)))return <Empty title="Seasonal pattern unavailable"/>;
  const points=[...data].sort((a,b)=>a.week-b.week);
  const W=600,H=210,L=45,R=14,T=20,B=34;
  const max=Math.max(...points.flatMap(p=>[p.p90,p.median]).filter(numeric),1)*1.08;
  const x=(week:number)=>L+(week-1)/52*(W-L-R);const y=(v:number)=>H-B-v/max*(H-B-T);
  const valid=points.filter(p=>numeric(p.median));
  const bands=points.filter(p=>numeric(p.p10)&&numeric(p.p90));
  const band=bands.length?bands.map((p,i)=>`${i?'L':'M'}${x(p.week)},${y(p.p90!)}`).join(' ')+[...bands].reverse().map(p=>` L${x(p.week)},${y(p.p10!)}`).join('')+' Z':'';
  const line=valid.map((p,i)=>`${i?'L':'M'}${x(p.week)},${y(p.median!)}`).join(' ');
  return <><div className="trace-legend"><span><i className="line-key orange"/>Median</span><span><i className="band-key"/>10th–90th percentile</span></div><div className="svg-chart"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Historical weekly activity, median and 10th to 90th percentile range">
    {points.filter(p=>p.critical).map(p=><rect key={p.week} x={x(p.week)-4} y={T} width={(W-L-R)/53+1} height={H-T-B} fill="#f49a60" opacity=".065"/>)}
    {[0,.5,1].map(f=><g key={f}><line x1={L} x2={W-R} y1={y(max*f)} y2={y(max*f)} stroke="#334147" strokeDasharray="3 5"/><text x={L-8} y={y(max*f)+4} textAnchor="end" className="svg-axis">{compact(max*f)}</text></g>)}
    <path d={band} fill="#d3915e" opacity=".18"/><path d={line} fill="none" stroke="#f79963" strokeWidth="2.3"/>
    {[1,14,27,40,53].map((w,i)=><text key={w} x={x(w)} y={H-9} textAnchor="middle" className="svg-axis">{['JAN','APR','JUL','OCT','DEC'][i]}</text>)}
  </svg></div><p className="chart-note">Shaded weeks meet the historical high-activity threshold. This describes past observations, not a forecast.</p><ChartLabel label={label}/></>;
}

function EvaluationTable({rows}:{rows:Evaluation[]}) {
  if(!rows.length)return <Empty title="Held-out evaluation not available">Model performance will appear after training, validation and the final test split have been processed.</Empty>;
  return <div className="table-scroll"><table><thead><tr><th>Model</th><th>Split / scale</th><th>MAE</th><th>Bias</th><th>Correlation</th><th>Peak error</th></tr></thead><tbody>{rows.map((r,i)=><tr key={i}><td><span className="model-chip">{r.model}</span></td><td>{r.split}<span className="table-sub">{r.aggregation}</span></td><td>{fmt(r.mae,2)}</td><td>{numeric(r.bias_pct)?`${fmt(r.bias_pct,1)}%`:'—'}</td><td>{fmt(r.correlation,3)}</td><td>{numeric(r.peak_week_error)?`${fmt(r.peak_week_error,1)} wk`:'—'}</td></tr>)}</tbody></table></div>;
}

function RhythmChart({stream,rest}:{stream:RhythmStream;rest:string}) {
  const values=stream.weekdays||[];const W=260,H=150,B=25,T=12,L=12;const max=Math.max(1.2,...values.map(v=>v.hi).filter(numeric));const y=(v:number)=>H-B-v/max*(H-T-B);
  return <div className="rhythm-stream"><h3>{stream.stream}<span>{fmt(stream.years)} years</span></h3><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${stream.stream} weekday indices and uncertainty`}>
    <line x1={L} x2={W-L} y1={y(1)} y2={y(1)} stroke="#94a3a8" strokeDasharray="3 4"/>
    {values.map((v,i)=>{const x=L+i*34;return <g key={v.day}>{numeric(v.index)&&<rect x={x} y={y(v.index)} width="23" height={H-B-y(v.index)} rx="2" fill={v.day===rest?'#f79963':'#576a71'}/>} {numeric(v.lo)&&numeric(v.hi)&&<g stroke="#f3efdf"><line x1={x+11.5} x2={x+11.5} y1={y(v.lo)} y2={y(v.hi)}/><line x1={x+8} x2={x+15} y1={y(v.lo)} y2={y(v.lo)}/><line x1={x+8} x2={x+15} y1={y(v.hi)} y2={y(v.hi)}/></g>}<text x={x+11} y={H-5} textAnchor="middle" className="svg-axis">{v.day}</text></g>;})}
  </svg><small>Adjusted p: {fmt(stream.p_adjusted,4)}</small></div>;
}

function EvidenceDrawer({week,onClose,label,region}:{week:Week;onClose:()=>void;label:string;region:Region}) {
  const ref=useRef<HTMLElement>(null);
  useEffect(()=>{const old=document.activeElement as HTMLElement;ref.current?.querySelector<HTMLButtonElement>('button')?.focus();const onKey=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose();if(e.key==='Tab'){const list=ref.current?.querySelectorAll<HTMLElement>('button,a,[tabindex="0"]');if(!list?.length)return;const first=list[0],last=list[list.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}};document.addEventListener('keydown',onKey);return()=>{document.removeEventListener('keydown',onKey);old?.focus();};},[onClose]);
  const streams=[['Terra',sum(week.rows.map(r=>r.raw_terra))],['Aqua',sum(week.rows.map(r=>r.raw_aqua))],['VIIRS',sum(week.rows.map(r=>r.raw_viirs))]] as const;
  const sources=[...new Set(week.rows.map(r=>r.source).filter(Boolean))];
  const coverage=[...new Set(week.rows.map(r=>r.coverage).filter(Boolean))];
  const anomalies=region.anomalies.filter(a=>{const w=isoWeek(a.date);return w.year===week.year&&w.week===week.week;});
  return <div className="drawer-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><aside ref={ref} className="evidence-drawer" role="dialog" aria-modal="true" aria-labelledby="evidence-title">
    <div className="drawer-head"><span className="eyebrow">FOLLOW THE EVIDENCE</span><button className="icon-button" onClick={onClose} aria-label="Close evidence"><X size={20}/></button></div>
    <h2 id="evidence-title">Week {week.week}, {week.year}</h2><p className="drawer-date">Starting {prettyDate(week.date)} · {region.meta.name}</p><DataBadge label={label}/>
    <div className="evidence-number"><span>Aqua-equivalent activity</span><strong>{fmt(week.harmonized,1)}</strong><small>Sum of {week.rows.filter(r=>numeric(r.harmonized)).length} available daily estimates</small></div>
    <div className="evidence-section"><h3>What each sensor detected</h3>{streams.map(([name,value])=><div className="key-value" key={name}><span><span className={`sensor-dot ${name.toLowerCase()}`}/>{name}</span><strong>{fmt(value)}</strong></div>)}<p>Detections are sensor observations, not a count of distinct fires.</p></div>
    <div className="evidence-section"><h3>How this estimate was made</h3><dl><dt>Model</dt><dd>{[...new Set(week.rows.map(r=>r.model))].join(', ')||region.meta.model}</dd><dt>Source</dt><dd>{sources.join('; ')||'Not supplied'}</dd><dt>Coverage</dt><dd>{coverage.join('; ')||'Unknown'}</dd><dt>Daily interval</dt><dd>Reported below. Intervals are not summed into a weekly confidence interval.</dd></dl></div>
    <div className="evidence-section"><h3>Daily estimates</h3><div className="table-scroll"><table><thead><tr><th>Date</th><th>Estimate</th><th>Interval</th></tr></thead><tbody>{week.rows.map((r,i)=><tr key={r.date+i}><td>{r.date}</td><td>{fmt(r.harmonized,1)}</td><td>{numeric(r.lo)&&numeric(r.hi)?`${fmt(r.lo,1)}–${fmt(r.hi,1)}`:'Not available'}</td></tr>)}</tbody></table></div></div>
    <div className="callout"><CircleHelp size={17}/><p>{region.meta.coverage_note || 'Cloud and overpass gaps can affect detection counts. Missing detection records do not establish absence of fire.'}</p></div>
    {anomalies.length>0&&<div className="evidence-section"><h3>Historical comparison</h3>{anomalies.map((a,i)=><p key={i}>{a.status} · z-score {fmt(a.z_score,2)}</p>)}</div>}
    <button className="button primary full" onClick={()=>exportCSV(week.rows,region.meta.region,label)}><ArrowDownToLine size={16}/> Download this evidence</button>
  </aside></div>;
}

function Methods({region,index}:{region:Region|null;index:Index}) {
  return <div className="methods-page"><div className="section-intro"><span className="eyebrow">OPEN METHODS</span><h2>A clearer record.<br/><em>Not a perfect one.</em></h2><p>FIRETRACE compares satellite observations on a named reference scale. Each conclusion should be traceable to a source, an assumption and a test.</p></div>
    <div className="method-grid"><article className="panel method-card"><span className="step">01 / OBSERVE</span><h3>Keep the instruments separate</h3><p>MODIS Terra, MODIS Aqua and VIIRS S-NPP observe fire activity at different resolutions and times. Their detection counts cannot be treated as interchangeable.</p><p>Dates are assigned using local civil time. Low-confidence observations and non-vegetation sources are handled explicitly by the pipeline.</p></article>
    <article className="panel method-card"><span className="step">02 / COMPARE</span><h3>Use Aqua as a reference</h3><p>The pipeline compares a raw baseline, a single conversion ratio and stratified conversion ratios. Models are selected using validation years; held-out test years are reserved for evaluation.</p><p>Output is expressed as MODIS-Aqua-equivalent detections. This is not a reconstruction of the true number of fires.</p></article>
    <article className="panel method-card"><span className="step">03 / CHECK</span><h3>Let the evidence set the story</h3><p>A real trend may remain after harmonization. Simulated sensor-switch tests check behavior under known conditions and are labeled separately from real observations.</p><p>A weekly rhythm is published only when its predefined gate passes. A rest-day dip alone does not establish ignition cause.</p></article></div>
    <section className="panel limitations"><PanelTitle eyebrow="READ BEFORE INTERPRETING" title="What the record cannot tell you"/><ul><li><strong>No detection is not “no fire.”</strong> Cloud, missed overpasses and detection limits affect the record.</li><li><strong>Intervals are conditional.</strong> Calibration uncertainty does not cover every observational or modeling error.</li><li><strong>Historical patterns are not forecasts.</strong> Calendar exports are planning context, not warnings or emergency advice.</li><li><strong>Independent instruments do not mean independent events.</strong> Sensors can observe the same fires.</li>{index.limitations.map((l,i)=><li key={i}>{l}</li>)}</ul>{region?.meta.coverage_note&&<div className="callout"><ShieldCheck size={18}/><p>{region.meta.coverage_note}</p></div>}</section>
    <section className="panel sources-panel"><PanelTitle eyebrow="PROVENANCE" title="Data sources"/>{(region?.meta.sources?.length?region.meta.sources:[{name:'NASA FIRMS — active fire data',url:'https://firms.modaps.eosdis.nasa.gov/'}]).map(s=><a key={s.url} href={s.url} target="_blank" rel="noreferrer"><Database size={18}/><span>{s.name}<small>{new URL(s.url).hostname}</small></span><ArrowUpRight size={17}/></a>)}<p>Generated: {index.generated_at?new Date(index.generated_at).toLocaleString():'not yet available'}. Source files and analysis scripts accompany the project repository.</p></section>
  </div>;
}

export default function App() {
  const [index,setIndex]=useState<Index>(BLANK_INDEX),[regionId,setRegionId]=useState(''),[region,setRegion]=useState<Region|null>(null);
  const [loading,setLoading]=useState(true),[error,setError]=useState(''),[view,setView]=useState<View>('explore'),[mode,setMode]=useState<Mode>('harmonized');
  const [start,setStart]=useState(''),[end,setEnd]=useState(''),[cell,setCell]=useState('ALL'),[selected,setSelected]=useState<Week|null>(null),[toast,setToast]=useState('');
  useEffect(()=>{const controller=new AbortController();fetch(`${import.meta.env.BASE_URL}data/index.json`,{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('The processed data index has not been published yet.');return r.json();}).then((data:Index)=>{setIndex(data);if(data.regions.length)setRegionId(data.regions[0].id);else setLoading(false);}).catch(e=>{if(e.name!=='AbortError'){setError('Processed data is not available yet. Run the data pipeline or reload once processing completes.');setLoading(false);}});return()=>controller.abort();},[]);
  useEffect(()=>{if(!regionId)return;const controller=new AbortController();const entry=index.regions.find(r=>r.id===regionId);if(!entry)return;setLoading(true);setError('');setSelected(null);fetch(`${import.meta.env.BASE_URL}data/${entry.file}`,{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('This region’s processed data could not be loaded.');return r.json();}).then((data:Region)=>{setRegion({...data,daily:data.daily||[],cells:data.cells||[],anomalies:data.anomalies||[],eval:data.eval||[],weekly_climatology:data.weekly_climatology||[],critical_periods:data.critical_periods||[]});setStart(data.meta.period_start?.slice(0,10)||'');setEnd(data.meta.period_end?.slice(0,10)||'');setCell('ALL');setLoading(false);}).catch(e=>{if(e.name!=='AbortError'){setError('This region has no readable processed data yet. Reload once processing completes.');setRegion(null);setLoading(false);}});return()=>controller.abort();},[regionId,index]);
  useEffect(()=>{if(!toast)return;const timer=setTimeout(()=>setToast(''),3500);return()=>clearTimeout(timer);},[toast]);
  const sourceRows=useMemo(()=>cell==='ALL'?region?.daily||[]:region?.cells.find(c=>c.id===cell)?.daily||[],[region,cell]);
  const rows=useMemo(()=>sourceRows.filter(r=>(!start||r.date>=start)&&(!end||r.date.slice(0,10)<=end)),[sourceRows,start,end]);
  const weeks=useMemo(()=>aggregateWeeks(rows),[rows]);
  const label=region?.meta.label||index.label;
  const values=rows.map(r=>r[mode]).filter(numeric);const total=sum(values);
  const years=[...new Set(rows.map(r=>r.date.slice(0,4)))].length;
  const peak=weeks.filter(w=>numeric(w[mode])).sort((a,b)=>b[mode]!-a[mode]!)[0];
  const gate=region?.rhythm?.gate;const decision=typeof gate==='string'?gate:gate?.decision||'insufficient_data';
  const scopeName=cell==='ALL'?'Region total':`Cell ${cell}`;
  const isSynthetic=/synthetic|demo|simulat/i.test(label);
  const selectedAnomalies=region?.anomalies.filter(a=>(!start||a.date>=start)&&(!end||a.date.slice(0,10)<=end))||[];
  function openAnomaly(a:Anomaly){const {year,week}=isoWeek(a.date);const found=weeks.find(w=>w.year===year&&w.week===week);if(found)setSelected(found);}
  function download(kind:'csv'|'ics'){if(!region)return;if(kind==='csv')exportCSV(rows,region.meta.region,label);else exportICS(region.critical_periods,Number(end.slice(0,4))||new Date().getFullYear(),region.meta.name,label);setToast(`${kind.toUpperCase()} export downloaded`);}

  return <><a className="skip-link" href="#main">Skip to content</a><header className="site-header"><a href="#" className="brand" onClick={e=>{e.preventDefault();setView('explore');}}><span className="brand-symbol"><Flame size={24}/></span><span>FIRE<span className="brand-light">TRACE</span></span></a><nav aria-label="Main navigation">{(['explore','evidence','methods'] as const).map(v=><button key={v} className={view===v?'active':''} onClick={()=>setView(v)}>{v==='explore'?'Explore the record':v==='evidence'?'Evidence & validation':'Methods'}</button>)}</nav><a className="header-source" href="https://firms.modaps.eosdis.nasa.gov/" target="_blank" rel="noreferrer">NASA FIRMS <ArrowUpRight size={14}/></a></header>
    <div className="masthead"><div><div className="eyebrow masthead-eyebrow"><span className="tiny-cross">+</span> SATELLITE FIRE OBSERVATORY <span className="masthead-separator">/</span> MODIS × VIIRS</div><h1>Look beyond<br className="mobile-break"/> the <em>hotspots.</em></h1><p>A changing signal doesn’t always mean a changing planet.<br/>Trace fire activity across instruments, seasons and years.</p></div><div className="masthead-orbit" aria-hidden="true"><div className="orbit-line one"/><div className="orbit-line two"/><div className="orbit-center"><ScanLine size={38}/></div><span className="orbit-tag">OBSERVE · COMPARE · VERIFY</span></div></div>
    <main id="main"><div className="workspace-toolbar"><div className="workspace-title"><span className="live-dot"/><span>{view==='explore'?'Explore the fire record':view==='evidence'?'Inspect the evidence':'Understand the methods'}</span></div><DataBadge label={label}/></div>
      {isSynthetic&&<div className="synthetic-banner"><FlaskIcon/><span><strong>Synthetic demonstration.</strong> These observations were generated to test the pipeline. They are not measured fire activity.</span></div>}
      {error&&<div role="alert" className="error-banner"><CircleHelp size={20}/><div><strong>Data not available</strong><p>{error} The interface will never substitute fabricated observations.</p></div></div>}
      {view==='methods'?<Methods region={region} index={index}/>:<div className="workspace"><aside className="sidebar"><div className="sidebar-title"><SlidersHorizontal size={15}/><span>YOUR VIEW</span></div>
        <label className="field-label" htmlFor="region">Region</label><div className="select-wrap region-select"><MapPin size={17}/><select id="region" value={regionId} onChange={e=>setRegionId(e.target.value)} disabled={!index.regions.length}>{!index.regions.length&&<option>No processed regions</option>}{index.regions.map(r=><option key={r.id} value={r.id}>{r.name}</option>)}</select><ChevronDown size={15}/></div>
        <CellMap cells={region?.cells||[]} selected={cell} onSelect={id=>{setCell(id);setSelected(null);}} name={region?.meta.name||'Region'}/>{region?.meta.cell_scope&&<p className="cell-scope">{region.meta.cell_scope}</p>}
        <label className="field-label" htmlFor="cell">Spatial scope</label><div className="select-wrap"><select id="cell" value={cell} onChange={e=>{setCell(e.target.value);setSelected(null);}}><option value="ALL">Whole region</option>{region?.cells.map(c=><option key={c.id} value={c.id}>{c.id} · {c.lat.toFixed(2)}, {c.lon.toFixed(2)}</option>)}</select><ChevronDown size={15}/></div>
        <div className="sidebar-divider"/><label className="field-label" htmlFor="start">Observation period</label><div className="date-fields"><label><span>FROM</span><input id="start" type="date" value={start} min={region?.meta.period_start} max={end||region?.meta.period_end} onChange={e=>setStart(e.target.value)}/></label><label><span>TO</span><input aria-label="End date" type="date" value={end} min={start||region?.meta.period_start} max={region?.meta.period_end} onChange={e=>setEnd(e.target.value)}/></label></div><button className="text-button" onClick={()=>{setStart(region?.meta.period_start?.slice(0,10)||'');setEnd(region?.meta.period_end?.slice(0,10)||'');}}>Use full available record <ArrowRight size={13}/></button>
        <div className="sidebar-divider"/><span className="field-label">Observation streams</span><div className="stream-list">{['Terra','Aqua','VIIRS'].map((s,i)=><div key={s}><span className={`sensor-dot ${s.toLowerCase()}`}/><span>{s}<small>{i===2?'S-NPP · VIIRS':'MODIS'}</small></span><Check size={13}/></div>)}</div><p className="sidebar-caption">Streams are analyzed separately. Available values appear in each evidence card.</p>
        <div className="sidebar-note"><ShieldCheck size={20}/><h3>Evidence before conclusions.</h3><p>A hotspot is an observation, not a distinct fire. Unknown coverage remains unknown.</p><button onClick={()=>setView('methods')}>How to read this record <ArrowUpRight size={13}/></button></div>
      </aside><div className="main-column">
        {loading?<div className="loading-state" role="status"><span className="loader"/><h2>Tracing the observations…</h2><p>Loading the processed record and its evidence.</p></div>:!region?<Empty title="Ready for the first observations">Run the reproducible data pipeline to publish a region. The calendar, comparisons and evidence cards will populate from its output.</Empty>:<>
          <div className="region-heading"><div><span className="eyebrow">{scopeName.toUpperCase()} <span className="heading-slash">/</span> {start&&end?`${start.slice(0,4)}–${end.slice(0,4)}`:'AVAILABLE RECORD'}</span><h2>{region.meta.name}<span className="region-coordinate">{numeric(region.meta.centroid?.[1])?`${region.meta.centroid[1].toFixed(1)}° N / ${region.meta.centroid[0].toFixed(1)}° E`:''}</span></h2></div><button className="button subtle" onClick={()=>download('csv')} disabled={!rows.length}><ArrowDownToLine size={15}/> Export data</button></div>
          {view==='explore'?<><div className="metric-strip"><div><span>{mode==='harmonized'?'AQUA-EQUIVALENT ACTIVITY':'RAW BASELINE ACTIVITY'}</span><strong>{compact(total)}</strong><small>Sum of available values</small></div><div><span>RECORD IN VIEW</span><strong>{years}<i> years</i></strong><small>{fmt(rows.length)} day records · {scopeName.toLowerCase()}</small></div><div><span>PEAK OBSERVED WEEK</span><strong>{peak?String(peak.week).padStart(2,'0'):'—'}<i>{peak?` / ${peak.year}`:''}</i></strong><small>{peak?prettyDate(peak.date):'No estimate available'}</small></div></div>
          <section className="panel calendar-panel"><PanelTitle eyebrow="01 / THE LONG VIEW" title="Burning activity calendar"><div className="segmented" aria-label="Calendar reference scale">{(['harmonized','raw'] as const).map(m=><button key={m} className={mode===m?'active':''} onClick={()=>setMode(m)} aria-pressed={mode===m}>{m==='harmonized'?<Layers3 size={13}/>:<Radio size={13}/>} {m==='harmonized'?'Harmonized':'Raw baseline'}</button>)}</div></PanelTitle><p className="panel-description">{mode==='harmonized'?'Each square is a week of Aqua-equivalent activity. Follow a season across years, then inspect the observations behind it.':'A deliberately naive sensor-switch baseline, shown for comparison. Counts from different instruments are not directly equivalent.'}</p><Heatmap weeks={weeks} mode={mode} label={label} onSelect={setSelected}/></section>
          <section className="panel"><PanelTitle eyebrow="02 / QUESTION THE CHANGE" title="Did activity change—or the instrument?"/><TraceChart rows={rows} mode={mode} label={label}/></section>
          <div className="two-panels"><section className="panel season-panel"><PanelTitle eyebrow="03 / SEASONAL CONTEXT" title="The shape of a fire season"/>{cell==='ALL'?<SeasonChart data={region.weekly_climatology} label={label}/>:<Empty title="Regional climatology only">Return to “Whole region” to view the precomputed seasonal baseline.</Empty>}</section><section className="panel critical-panel"><PanelTitle eyebrow="HISTORICAL PATTERNS" title="Periods to pay attention to"><CalendarDays size={19}/></PanelTitle>{region.critical_periods.length?<div className="critical-list">{region.critical_periods.map((p,i)=><div key={i}><span className="period-mark"/><div><strong>Weeks {String(p.start_week).padStart(2,'0')}–{String(p.end_week).padStart(2,'0')}</strong><p>{p.label}</p></div></div>)}</div>:<p className="muted">No critical periods were identified from the available historical baseline.</p>}<p className="chart-note">Regional historical pattern. Calendar events use {end.slice(0,4)||'the selected year'} and are not forecasts.</p><button className="button subtle full" onClick={()=>download('ics')} disabled={!region.critical_periods.length}><ArrowDownToLine size={15}/> Export seasonal calendar</button></section></div>
          <section className="panel anomaly-panel"><PanelTitle eyebrow="04 / LOOK CLOSER" title="Unusual observations"><span className="count-badge">{fmt(selectedAnomalies.length)} in view</span></PanelTitle>{cell!=='ALL'?<p className="muted">Anomaly comparisons are available for the regional aggregate. Select “Whole region” to inspect them.</p>:selectedAnomalies.length?<div className="anomaly-list">{selectedAnomalies.slice(0,8).map((a,i)=><button key={i} onClick={()=>openAnomaly(a)}><span className={`anomaly-icon ${/low/i.test(a.status)?'low':''}`}><Waves size={16}/></span><span><strong>{prettyDate(a.date)}</strong><small>{a.status.replaceAll('_',' ')} · week {a.week}</small></span><span className="anomaly-value">{fmt(a.value,1)}<small>z {fmt(a.z_score,2)}</small></span><ArrowUpRight size={16}/></button>)}{selectedAnomalies.length>8&&<p className="chart-note">Showing the first 8 of {fmt(selectedAnomalies.length)} observations. Download the full dataset for further analysis.</p>}</div>:<p className="muted">No flagged observations are available for this period. This does not establish normal conditions where coverage is missing.</p>}</section>
          </>:<><section className="panel"><PanelTitle eyebrow="HELD-OUT COMPARISON" title="Let the baselines compete"/><p className="panel-description">Performance against the Aqua reference. A more complex model is useful only if it improves validation performance; test results remain visible even when they disappoint.</p><EvaluationTable rows={region.eval}/><ChartLabel label={label}/></section><section className="panel rhythm-panel"><PanelTitle eyebrow="EXPERIMENTAL / HUMAN RHYTHM" title="Is there a weekly pattern?"><span className={`gate-badge ${decision==='pass'?'pass':''}`}><ShieldCheck size={13}/>{decision.replaceAll('_',' ')}</span></PanelTitle>{decision==='pass'&&region.rhythm?<><p className="panel-description">Per-stream local-weekday indices. The highlighted rest day was specified before analysis. A value of 1 is the annual weekday average.</p><div className="rhythm-grid">{region.rhythm.streams.map(s=><RhythmChart key={s.stream} stream={s} rest={region.rhythm!.rest_day}/>)}</div><p className="chart-note">A rest-day dip is consistent with human scheduling. It does not establish ignition cause. Streams are corroborating observations of overlapping events.</p></>:<div className="rhythm-locked"><div className="locked-mark"><Waves size={30}/></div><div><h3>The evidence gate has not passed.</h3><p>The weekly-rhythm view stays unpublished until the US replication check and at least two other countries meet the predefined requirements, with control diagnostics reviewed.</p><p>Current result: <strong>{decision.replaceAll('_',' ')}</strong>. An unavailable pattern is not evidence of absence.</p></div></div>}<ChartLabel label={label}/></section><section className="panel"><PanelTitle eyebrow="TRACEABILITY" title="What every estimate carries"/><div className="provenance-grid"><div><Database size={19}/><h3>Source observations</h3><p>Separate Terra, Aqua and VIIRS counts, without silently treating missing records as zero.</p></div><div><Layers3 size={19}/><h3>Transformation</h3><p>The selected calibration model and whether the value was observed, converted or reconstructed.</p></div><div><ShieldCheck size={19}/><h3>Uncertainty</h3><p>Reported intervals and coverage limitations accompany the estimate.</p></div></div><button className="text-button" onClick={()=>setView('explore')}>Open a calendar week to inspect evidence <ArrowRight size={14}/></button></section></>}
          <div className="bottom-note"><CircleHelp size={15}/><p>{region.meta.coverage_note||'Cloud and overpass coverage may be unknown. These observations are not a complete inventory of fires.'}</p></div>
        </>}
      </div></div>}
    </main><footer><a className="brand footer-brand" href="#" onClick={e=>{e.preventDefault();window.scrollTo({top:0,behavior:'smooth'});}}><Flame size={18}/> FIRETRACE</a><p>Built for NASA Space Apps · Bhaktapur<br/><span>NASA does not endorse this project.</span></p><button onClick={()=>{setView('methods');window.scrollTo({top:360,behavior:'smooth'});}}>Sources & limitations <ArrowUpRight size={13}/></button></footer>
    {selected&&region&&<EvidenceDrawer week={selected} onClose={()=>setSelected(null)} label={label} region={region}/>}{toast&&<div role="status" className="toast"><Check size={16}/>{toast}</div>}
  </>;
}

function FlaskIcon(){return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M9 3h6M10 3v7L4 20h16l-6-10V3M7 15h10"/></svg>;}
