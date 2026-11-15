import {lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {ArrowDownToLine, ArrowRight, ArrowUpRight, CalendarDays, Check, ChevronDown, CircleHelp, Database, Flame, Globe2, Layers3, MapPin, Radio, ScanLine, ShieldCheck, SlidersHorizontal, Waves, X} from 'lucide-react';
import type {Anomaly, Climatology, Daily, Evaluation, Index, Region, Week} from './types';
import {aggregateWeeks, compact, exportCSV, exportICS, fmt, geoCoordinate, isoWeek, monthly, numeric, prettyDate, saveFile, sum} from './utils';
import {buildEvidenceBrief} from './evidenceBrief';
import ComparisonJourney from './ComparisonJourney';
import ComparisonChart from './ComparisonChart';
import SeasonalContext from './SeasonalContext';
import AnomalyPanel from './AnomalyPanel';
import {loadData,decodeCell,invalidateData} from './loadData';
import ShareView from './ShareView';
import RhythmView from './RhythmView';
import RhythmCellMap from './RhythmCellMap';
import {createShareLink,defaultExploration,linkedRegion,linkedView} from './explorationState';
import type {ExplorationState} from './explorationState';
import {canShareSelection,catalogForRegion,isPublishedIndex,resolveAppExploration,restoreEvidenceWeek} from './explorationIntegration';
import {dateRangeError,weekCoverage} from './calendarView';
const Globe=lazy(()=>import('./Globe'));

type View = 'explore' | 'evidence' | 'rhythm' | 'methods';
type Mode = 'harmonized' | 'raw';
const COLORS = ['#26353b','#4e4b3d','#786040','#a86c3d','#d77945','#f89965','#ffd4ad'];
const BLANK_INDEX: Index = {label:'DATA NOT LOADED',regions:[],generated_at:'',limitations:[]};
const EVIDENCE_LOAD_NOTICE='The linked evidence panel could not be restored because its grid data was unavailable.';

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
    <defs><pattern id="map-grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M 28 0 L 0 0 0 28" fill="none" stroke="#33444a" strokeWidth=".5"/></pattern></defs>
    <rect width="280" height="170" fill="url(#map-grid)"/>
    {valid.map(c=><circle key={c.id} cx={x(c.lon)} cy={y(c.lat)} r={selected===c.id?5:2.8} fill={selected===c.id?'#fff2d5':'#ed9562'} opacity={selected==='ALL'||selected===c.id?.9:.35} onClick={()=>onSelect(c.id)} className="map-point"><title>{c.id}: {c.lat.toFixed(2)}°, {c.lon.toFixed(2)}°</title></circle>)}
    <text x="12" y="16" className="svg-micro">N ↑</text><text x="12" y="157" className="svg-micro">{geoCoordinate(minY,'lat')}–{geoCoordinate(maxY,'lat')}</text><text x="268" y="157" textAnchor="end" className="svg-micro">{geoCoordinate(minX,'lon')}–{geoCoordinate(maxX,'lon')}</text>
  </svg><div className="map-caption"><span><span className="map-dot"/> {fmt(valid.length)} grid centers</span><button onClick={()=>onSelect('ALL')} disabled={selected==='ALL'}>Reset</button></div></div>;
}

function Heatmap({weeks,mode,label,onSelect}:{weeks:Week[];mode:Mode;label:string;onSelect:(w:Week)=>void}) {
  const [focusKey,setFocusKey]=useState(''),[hoverKey,setHoverKey]=useState('');
  const years = [...new Set(weeks.map(w=>w.year))].sort((a,b)=>b-a);
  const indexed = new Map(weeks.map(w=>[w.key,w]));
  const vals = weeks.flatMap(w=>[w.raw,w.harmonized]).filter(numeric);
  const max = Math.max(...vals, 1);
  const details=useMemo(()=>new Map(weeks.map(week=>{const days=weekCoverage(week,mode);return [week.key,{...days,dateLabel:`${prettyDate(days.start)} to ${prettyDate(days.end)}`,valueLabel:fmt(week[mode],1)}];})),[weeks,mode]);
  const activeKey=indexed.has(focusKey)?focusKey:weeks.find(w=>w.year===years[0])?.key;
  const preview=indexed.get(hoverKey)||indexed.get(activeKey||'');
  const coverage=preview?weekCoverage(preview,mode):null;
  if (!years.length) return <Empty title="No calendar data in this range"/>;
  return <><div className="calendar-scroller"><div className="calendar-grid" style={{minWidth:700}}>
    <div className="calendar-months"><span className="year-label">YEAR</span><div>{['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'].map(m=><span key={m}>{m}</span>)}</div></div>
    {years.map(year=><div className="calendar-row" key={year}><span className="year-label">{year}</span><div className="week-cells">{Array.from({length:53},(_,i)=>{
      const w=indexed.get(`${year}-${i+1}`); const v=w?.[mode]; const known=numeric(v);const days=w?details.get(w.key):null;
      const color=known?COLORS[Math.min(6,Math.floor(Math.sqrt(Math.max(v,0)/max)*6))]:undefined;
      return <button key={i} className={`week-cell ${known?'':'missing'} ${days?.partial?'partial-week':''}`} style={{backgroundColor:color}} disabled={!w} tabIndex={w?.key===activeKey?0:-1} onMouseEnter={()=>w&&setHoverKey(w.key)} onFocus={()=>{if(w)setFocusKey(w.key);setHoverKey('');}} onKeyDown={event=>{const step=({ArrowLeft:-1,ArrowRight:1,ArrowUp:-53,ArrowDown:53} as Record<string,number>)[event.key];if(!step)return;setHoverKey('');event.preventDefault();const buttons=Array.from(event.currentTarget.closest('.calendar-grid')?.querySelectorAll<HTMLButtonElement>('.week-cell')||[]);let next=buttons.indexOf(event.currentTarget)+step;while(next>=0&&next<buttons.length&&buttons[next].disabled)next+=step;if(next>=0&&next<buttons.length)buttons[next].focus();}} onClick={()=>w&&onSelect(w)} aria-label={`${year}, calendar week ${i+1}: ${known?days?.valueLabel+' '+(mode==='raw'?'raw detections':'Aqua-reference-equivalent detections'):'unavailable'}.${days?` ${days.dateLabel}. ${days.partial?'Partial week: ':''}${days.recordDays} of ${days.expectedDays} calendar days included; ${days.availableDays} available daily values.`:''} Arrow keys move between weeks; Enter opens evidence.`} title={`Week ${i+1} · ${known?days?.valueLabel:'No value'}${days?` · ${days.recordDays}/${days.expectedDays} days${days.partial?' · partial week':''}`:''}`}/>;
    })}</div></div>)}
  </div></div>{preview&&coverage&&<div className="calendar-inspector"><div><span>WEEK {preview.week} · {preview.year}</span><strong>{prettyDate(coverage.start)} – {prettyDate(coverage.end)}</strong><small>{coverage.partial?'Partial week · ':''}{coverage.recordDays} of {coverage.expectedDays} calendar days included · {coverage.availableDays} available daily values</small></div><div className="calendar-inspector-value"><strong>{fmt(preview[mode],1)}</strong><small>{mode==='raw'?'raw baseline detections':'Aqua-reference-equivalent detections'}</small></div><button className="text-button" onClick={()=>onSelect(preview)}>Open week evidence <ArrowUpRight size={13}/></button></div>}<div className="chart-bottom"><span><ScanLine size={13}/> Arrow keys explore · Enter opens evidence · 7-day bins start Jan 1</span><div className="heat-legend"><span>LOW</span>{COLORS.map(c=><i key={c} style={{background:c}}/>)}<span>HIGH</span><i className="missing"/><span>NO OBSERVATION / UNKNOWN</span></div></div><ChartLabel label={label}/></>;
}

function EvaluationTable({rows}:{rows:Evaluation[]}) {
  if(!rows.length)return <Empty title="Held-out evaluation not available">Model performance will appear after training, validation and the final test split have been processed.</Empty>;
  return <div className="table-scroll evidence-table-scroll evaluation-table" tabIndex={0} role="region" aria-label="Held-out model comparison table"><table><thead><tr><th scope="col">Model</th><th scope="col">Split / scale</th><th scope="col">MAE</th><th scope="col">Bias</th><th scope="col">Correlation</th><th scope="col">Peak error</th></tr></thead><tbody>{rows.map((r,i)=><tr key={i} className={i>0&&rows[i-1].model!==r.model?'model-start':undefined}><th scope="row"><span className="model-chip">{r.model}</span></th><td>{r.split}<span className="table-sub">{r.aggregation}</span></td><td>{fmt(r.mae,2)}</td><td>{numeric(r.bias_pct)?`${fmt(r.bias_pct,1)}%`:'—'}</td><td>{fmt(r.correlation,3)}</td><td>{numeric(r.peak_week_error)?`${fmt(r.peak_week_error,1)} wk`:'—'}</td></tr>)}</tbody></table></div>;
}

function EvidenceDrawer({week,onClose,onViewEarth,label,region,shareUrl,cellId}:{week:Week;onClose:()=>void;onViewEarth:()=>void;label:string;region:Region;shareUrl:string|null;cellId:string}) {
  const ref=useRef<HTMLElement>(null);
  useEffect(()=>{const old=document.activeElement as HTMLElement;const oldOverflow=document.body.style.overflow;document.body.style.overflow='hidden';ref.current?.querySelector<HTMLButtonElement>('button')?.focus();const onKey=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose();if(e.key==='Tab'){const list=ref.current?.querySelectorAll<HTMLElement>('button:not([disabled]),a[href],input:not([disabled]),[tabindex="0"]');if(!list?.length)return;const first=list[0],last=list[list.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}};document.addEventListener('keydown',onKey);return()=>{document.removeEventListener('keydown',onKey);document.body.style.overflow=oldOverflow;old?.focus();};},[onClose]);
  const streams=[['Terra',sum(week.rows.map(r=>r.raw_terra))],['Aqua',sum(week.rows.map(r=>r.raw_aqua))],['VIIRS',sum(week.rows.map(r=>r.raw_viirs))]] as const;
  const sources=[...new Set(week.rows.map(r=>r.source).filter(Boolean))];
  const coverage=[...new Set(week.rows.map(r=>r.coverage).filter(Boolean))];
  const cellInfo=region.cells.find(c=>c.id===cellId);
  const days=weekCoverage(week,'harmonized');
  const spatialScope=cellId==='ALL'?'Whole region':`Cell ${cellId}${cellInfo?` · ${geoCoordinate(cellInfo.lat,'lat')}, ${geoCoordinate(cellInfo.lon,'lon')}`:''}`;
  const fullRegionalWeek=week.week<53&&new Set(week.rows.map(r=>r.date.slice(0,10))).size===7&&week.rows.every(r=>r.cell_id==='ALL'&&numeric(r.harmonized));
  const anomalies=fullRegionalWeek?region.anomalies.filter(a=>{const w=isoWeek(a.date);return w.year===week.year&&w.week===week.week;}):[];
  function downloadBrief(){
    const caveats=[
      'Detections are sensor observations, not a count of distinct fires.',
      'Conversion intervals are reported below, not summed into a weekly confidence interval. Direct Aqua values have no calibration step; this does not mean observation uncertainty is zero.',
      region.meta.coverage_note||'Cloud and overpass gaps can affect detection counts. Missing detection records do not establish absence of fire.',
      ...(days.partial?[`Partial week in this view. Records cover ${prettyDate(days.firstRecord)} – ${prettyDate(days.lastRecord)} (${days.recordDays} of ${days.expectedDays} calendar days). Totals include only these records.`]:[]),
      ...(cellId!=='ALL'?['This cell uses a nationally selected calibration. Its bands omit spatial model error, and cell agreement can be much poorer than national agreement.']:[]),
      ...(!fullRegionalWeek?['Regional anomaly labels are not applied to individual cells or partial weeks.']:[]),
    ];
    const brief=buildEvidenceBrief({week,region,label,cellId,shareUrl,caveats});
    saveFile(brief.filename,brief.content,'text/markdown;charset=utf-8');
  }
  return <div className="drawer-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><aside ref={ref} className="evidence-drawer" role="dialog" aria-modal="true" aria-labelledby="evidence-title">
    <div className="drawer-head"><span className="eyebrow">FOLLOW THE EVIDENCE</span><button className="icon-button" onClick={onClose} aria-label="Close evidence"><X size={20}/></button></div>
    <h2 id="evidence-title">Week {week.week}, {week.year}</h2><p className="drawer-date">{prettyDate(days.start)} – {prettyDate(days.end)} · {region.meta.name}<br/><strong>{spatialScope}</strong></p><DataBadge label={label}/>
    {days.partial&&<p className="partial-week-note"><strong>Partial week in this view.</strong> Records cover {prettyDate(days.firstRecord)} – {prettyDate(days.lastRecord)} ({days.recordDays} of {days.expectedDays} calendar days). Totals include only these records.</p>}
    {cellId!=='ALL'&&<p className="chart-note">This cell uses a nationally selected calibration. Its bands omit spatial model error, and cell agreement can be much poorer than national agreement.</p>}
    <div className="evidence-number"><span>Aqua-reference-equivalent activity</span><strong>{fmt(week.harmonized,1)}</strong><small>Sum of {week.rows.filter(r=>numeric(r.harmonized)).length} available daily estimates</small></div>
    <div className="evidence-section"><h3>What each sensor detected</h3>{streams.map(([name,value])=><div className="key-value" key={name}><span><span className={`sensor-dot ${name.toLowerCase()}`}/>{name}</span><strong>{fmt(value)}</strong></div>)}<p>Detections are sensor observations, not a count of distinct fires.</p></div>
    <div className="evidence-section"><h3>How this estimate was made</h3><dl><dt>Model</dt><dd>{[...new Set(week.rows.map(r=>r.model))].join(', ')||region.meta.model}</dd><dt>Source</dt><dd>{sources.join('; ')||'Not supplied'}</dd><dt>Coverage</dt><dd>{coverage.join('; ')||'Unknown'}</dd><dt>Daily interval</dt><dd>Conversion intervals are reported below, not summed into a weekly confidence interval. Direct Aqua values have no calibration step; this does not mean observation uncertainty is zero.</dd></dl></div>
    <div className="evidence-section"><h3>Daily estimates</h3><div className="table-scroll evidence-table-scroll" tabIndex={0} role="region" aria-label="Daily estimates table"><table><thead><tr><th scope="col">Date</th><th scope="col">Estimate</th><th scope="col">Calibration interval</th></tr></thead><tbody>{week.rows.map((r,i)=><tr key={r.date+i}><td>{r.date}</td><td>{fmt(r.harmonized,1)}</td><td>{/observed aqua/i.test(r.source)?'Not applicable':numeric(r.lo)&&numeric(r.hi)?`${fmt(r.lo,1)}–${fmt(r.hi,1)}`:'Not available'}</td></tr>)}</tbody></table></div></div>
    <div className="callout"><CircleHelp size={17}/><p>{region.meta.coverage_note || 'Cloud and overpass gaps can affect detection counts. Missing detection records do not establish absence of fire.'}</p></div>
    {anomalies.length>0&&<div className="evidence-section"><h3>Historical regional comparison</h3>{anomalies.map((a,i)=><p key={i}>{a.status} · z-score {fmt(a.z_score,2)}</p>)}</div>}{!fullRegionalWeek&&<p className="chart-note">Regional anomaly labels are not applied to individual cells or partial weeks.</p>}
    <button className="button primary full" onClick={()=>exportCSV(week.rows,region.meta.region,label)}><ArrowDownToLine size={16}/> Download daily CSV</button>
    <div className="evidence-actions"><button className="button subtle full" onClick={downloadBrief}><ArrowDownToLine size={16}/> Download evidence brief</button><button className="button subtle full" onClick={onViewEarth}><Globe2 size={16}/> View {week.year} on Earth (annual)</button></div>
    <div className="evidence-share"><ShareView url={shareUrl}/></div>
  </aside></div>;
}

function Methods({region,index}:{region:Region|null;index:Index}) {
  return <div className="methods-page"><div className="section-intro"><span className="eyebrow">OPEN METHODS</span><h2>A clearer record.<br/><em>Not a perfect one.</em></h2><p>FIRETRACE compares satellite observations on a named reference scale. Each conclusion should be traceable to a source, an assumption and a test.</p></div>
    <nav className="method-jump-nav" aria-label="Methods sections"><a href="#method-steps">Process</a><a href="#method-limitations">Limitations</a><a href="#method-sources">Data sources</a></nav>
    <div className="method-grid" id="method-steps" tabIndex={-1}><article className="panel method-card"><span className="step">01 / OBSERVE</span><h3>Keep the instruments separate</h3><p>MODIS Terra, MODIS Aqua and VIIRS S-NPP observe fire activity at different resolutions and times. Their detection counts cannot be treated as interchangeable.</p><p>Dates are assigned using local civil time. Low-confidence observations and non-vegetation sources are handled explicitly by the pipeline.</p></article>
    <article className="panel method-card"><span className="step">02 / COMPARE</span><h3>Use Aqua as a reference</h3><p>The pipeline compares a raw baseline, a single conversion ratio and stratified conversion ratios. Models are selected using validation years; held-out test years are reserved for evaluation.</p><p>Output is expressed as Aqua-reference-equivalent detections. This is not a reconstruction of the true number of fires.</p></article>
    <article className="panel method-card"><span className="step">03 / CHECK</span><h3>Let the evidence set the story</h3><p>A real trend may remain after harmonization. Simulated sensor-switch tests check behavior under known conditions and are labeled separately from real observations.</p><p>A weekly rhythm is published only when its predefined gate passes. A rest-day dip alone does not establish ignition cause.</p></article></div>
    <section className="panel limitations" id="method-limitations" tabIndex={-1}><PanelTitle eyebrow="READ BEFORE INTERPRETING" title="What the record cannot tell you"/><ul><li><strong>No detection is not “no fire.”</strong> Cloud, missed overpasses and detection limits affect the record.</li><li><strong>Intervals are conditional.</strong> Calibration uncertainty does not cover every observational or modeling error.</li><li><strong>Historical patterns are not forecasts.</strong> Calendar exports are planning context, not warnings or emergency advice.</li><li><strong>Independent instruments do not mean independent events.</strong> Sensors can observe the same fires.</li>{index.limitations.map((l,i)=><li key={i}>{l}</li>)}</ul>{region?.meta.coverage_note&&<div className="callout"><ShieldCheck size={18}/><p>{region.meta.coverage_note}</p></div>}</section>
    <section className="panel sources-panel" id="method-sources" tabIndex={-1}><PanelTitle eyebrow="PROVENANCE" title="Data sources"/>{(region?.meta.sources?.length?region.meta.sources:[{name:'NASA FIRMS — active fire data',url:'https://firms.modaps.eosdis.nasa.gov/'}]).map(s=><a key={s.url} href={s.url} target="_blank" rel="noreferrer"><Database size={18}/><span>{s.name}<small>{new URL(s.url).hostname}</small></span><ArrowUpRight size={17}/></a>)}<p>Generated: {index.generated_at?new Date(index.generated_at).toLocaleString():'not yet available'}. Source files and analysis scripts accompany the project repository.</p></section>
  </div>;
}

export default function App() {
  const [index,setIndex]=useState<Index>(BLANK_INDEX),[regionId,setRegionId]=useState(''),[region,setRegion]=useState<Region|null>(null);
  const [loading,setLoading]=useState(true),[error,setError]=useState(''),[view,setView]=useState<View>(()=>linkedView(window.location.search)),[mode,setMode]=useState<Mode>('harmonized');
  const [showGlobe,setShowGlobe]=useState(false);
  const [journeyTarget,setJourneyTarget]=useState<'calendar-panel'|'earth-panel'|null>(null);
  const [start,setStart]=useState(''),[end,setEnd]=useState(''),[cell,setCell]=useState('ALL'),[selected,setSelected]=useState<Week|null>(null),[toast,setToast]=useState('');
  const closeEvidence=useCallback(()=>setSelected(null),[]);
  const [cellData,setCellData]=useState<{key:string;rows:Daily[]}|null>(null),[cellLoading,setCellLoading]=useState(false);
  const viewRevision=useRef(0);
  const pendingLink=useRef<{search:string;revision:number}|null>({search:window.location.search,revision:0}),pendingWeek=useRef<string|null>(null);
  const [navigation,setNavigation]=useState(0),[hydrating,setHydrating]=useState(true),[linkNotices,setLinkNotices]=useState<string[]>([]);
  const [indexAttempt,setIndexAttempt]=useState(0),[cellAttempt,setCellAttempt]=useState(0);
  const sectionFocus=useRef(false);
  useEffect(()=>{if(!sectionFocus.current)return;sectionFocus.current=false;const target=document.getElementById('main');target?.focus({preventScroll:true});target?.scrollIntoView({block:'start',behavior:'auto'});},[view]);
  useEffect(()=>{const controller=new AbortController();fetch(`${import.meta.env.BASE_URL}data/index.json`,{signal:controller.signal,cache:indexAttempt?'reload':'default'}).then(r=>{if(!r.ok)throw new Error('The processed data index has not been published yet.');return r.json();}).then((data:Index)=>{if(controller.signal.aborted)return;if(!isPublishedIndex(data))throw new Error('Invalid published index');setIndex(data);const id=linkedRegion(pendingLink.current?.search||'',data.regions.map(r=>r.id),'Nepal');if(id)setRegionId(id);else{setLoading(false);setHydrating(false);}}).catch(e=>{if(e.name!=='AbortError'){setError('Processed data is not available yet. Run the data pipeline or reload once processing completes.');setLoading(false);setHydrating(false);}});return()=>controller.abort();},[indexAttempt]);
  useEffect(()=>{const onPop=()=>{setJourneyTarget(null);setView(linkedView(window.location.search));pendingLink.current={search:window.location.search,revision:++viewRevision.current};pendingWeek.current=null;setHydrating(true);setLoading(true);setSelected(null);const id=linkedRegion(window.location.search,index.regions.map(r=>r.id),'Nepal');if(id){setRegionId(id);setNavigation(n=>n+1);}else{setLoading(false);setHydrating(false);}};window.addEventListener('popstate',onPop);return()=>window.removeEventListener('popstate',onPop);},[index]);
  useEffect(()=>{
    if(!regionId)return;
    const controller=new AbortController(),entry=index.regions.find(r=>r.id===regionId),request=pendingLink.current;
    if(!entry)return;
    setLoading(true);setError('');setSelected(null);
    loadData<Region>(entry.file,controller.signal).then(data=>{
      if(controller.signal.aborted)return;
      const loaded={...data,daily:data.daily||[],cells:data.cells||[],anomalies:data.anomalies||[],eval:data.eval||[],weekly_climatology:data.weekly_climatology||[],critical_periods:data.critical_periods||[]};
      const catalog=catalogForRegion(loaded),resolved=request?resolveAppExploration(request.search,catalog):null,state=resolved?.state||defaultExploration(catalog);
      const restoreNavigation=!request||request.revision===viewRevision.current;
      setRegion(loaded);setStart(state.start);setEnd(state.end);setCell(state.cell);
      setCellLoading(state.cell!=='ALL'&&!loaded.cells.find(c=>c.id===state.cell)?.daily);
      if(resolved){if(restoreNavigation)setView(state.view);setMode(state.scale);setLinkNotices(resolved.notices);}else setLinkNotices([]);
      pendingLink.current=null;pendingWeek.current=restoreNavigation?state.evidenceWeek:null;setHydrating(!!pendingWeek.current);setLoading(false);
    }).catch(e=>{if(e.name!=='AbortError'&&!controller.signal.aborted){setError('This region has no readable processed data yet. Reload once processing completes.');setRegion(null);setLoading(false);setCellLoading(false);setHydrating(false);}});
    return()=>controller.abort();
  },[regionId,index,navigation]);
  useEffect(()=>{if(!region){setCellLoading(false);return;}if(cell==='ALL'){setCellLoading(false);setError('');return;}const item=region.cells.find(c=>c.id===cell);if(item?.daily){setCellLoading(false);setError('');return;}if(!item?.file){setError('Daily records are not published for this grid cell. Select another cell or return to the whole region.');setCellLoading(false);return;}const key=`${region.meta.region}/${cell}`,controller=new AbortController();setCellLoading(true);setError('');loadData<{daily?:Daily[];columns?:string[];rows?:unknown[][]}>(item.file,controller.signal).then(value=>{if(controller.signal.aborted)return;setCellData({key,rows:decodeCell(value)});setCellLoading(false);}).catch(e=>{if(e.name!=='AbortError'&&!controller.signal.aborted){setError('This grid cell could not be loaded. Select another cell or return to the whole region.');setCellLoading(false);}});return()=>controller.abort();},[region,cell,cellAttempt]);
  useEffect(()=>{if(!toast)return;const timer=setTimeout(()=>setToast(''),3500);return()=>clearTimeout(timer);},[toast]);
  const sourceRows=useMemo(()=>cell==='ALL'?region?.daily||[]:region?.cells.find(c=>c.id===cell)?.daily||(cellData?.key===`${region?.meta.region}/${cell}`?cellData.rows:[]),[region,cell,cellData]);
  const dateError=region?dateRangeError(start,end,region.meta.period_start,region.meta.period_end):null;
  const rows=useMemo(()=>dateError?[]:sourceRows.filter(r=>r.date>=start&&r.date.slice(0,10)<=end),[sourceRows,start,end,dateError]);
  const weeks=useMemo(()=>aggregateWeeks(rows),[rows]);
  const dailySeriesReady=!!region&&(cell==='ALL'||!!region.cells.find(c=>c.id===cell)?.daily||cellData?.key===`${region.meta.region}/${cell}`);
  useEffect(()=>{
    if(!journeyTarget||view!=='explore')return;
    if(!error&&(loading||hydrating||cellLoading||!dailySeriesReady||dateError))return;
    const target=document.getElementById(error?'data-load-error':journeyTarget);
    if(!target)return;
    target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'auto'});
    if(!error)setJourneyTarget(null);
  },[journeyTarget,view,error,loading,hydrating,cellLoading,dailySeriesReady,dateError,showGlobe]);
  useEffect(()=>{
    if(!pendingWeek.current||loading||!region)return;
    if(!dailySeriesReady){if(error){setHydrating(false);setLinkNotices(n=>n.includes(EVIDENCE_LOAD_NOTICE)?n:[...n,EVIDENCE_LOAD_NOTICE]);}return;}
    const restored=restoreEvidenceWeek(pendingWeek.current,weeks);
    pendingWeek.current=null;setSelected(restored.week);setHydrating(false);
    setLinkNotices(n=>n.filter(notice=>notice!==EVIDENCE_LOAD_NOTICE));
    if(restored.notice)setLinkNotices(n=>[...n,restored.notice!]);
  },[weeks,loading,region,dailySeriesReady,error]);
  const catalog=useMemo(()=>region?catalogForRegion(region):null,[region]);
  const currentExploration:ExplorationState={region:regionId,start,end,cell,view,scale:mode,globeYear:Number(end.slice(0,4)),globeCell:null,globeView:'earth',evidenceWeek:selected?.date||null};
  const shareUrl=!loading&&!hydrating&&dailySeriesReady&&catalog&&region?.meta.region===regionId&&canShareSelection(currentExploration,catalog)?createShareLink(window.location.href,currentExploration,catalog).url:null;
  useEffect(()=>{if(!shareUrl||pendingLink.current)return;const url=new URL(shareUrl);if(window.location.search!==url.search)window.history.replaceState(window.history.state,'',url.pathname+url.search+window.location.hash);},[shareUrl]);
  const label=region?.meta.label||index.label;
  const values=rows.map(r=>r[mode]).filter(numeric);const total=sum(values);
  const years=[...new Set(rows.map(r=>r.date.slice(0,4)))].length;
  const peak=weeks.filter(w=>numeric(w[mode])).sort((a,b)=>b[mode]!-a[mode]!)[0];
  const gate=region?.rhythm?.gate;const decision=typeof gate==='string'?gate:gate?.decision||'insufficient_data';
  const scopeName=cell==='ALL'?'Region total':`Cell ${cell}`;
  const isSynthetic=/synthetic|demo|simulat/i.test(label);
  const completeWeekKeys=new Set(weeks.filter(w=>w.week<53&&new Set(w.rows.map(r=>r.date.slice(0,10))).size===7&&w.rows.every(r=>numeric(r.harmonized))).map(w=>w.key));
  const selectedAnomalies=region?.anomalies.filter(a=>{const w=isoWeek(a.date);return completeWeekKeys.has(`${w.year}-${w.week}`);})||[];
  function openAnomaly(a:Anomaly){const {year,week}=isoWeek(a.date);const found=weeks.find(w=>w.year===year&&w.week===week);if(found)setSelected(found);}
  function navigateToView(next:View){setJourneyTarget(null);viewRevision.current++;pendingWeek.current=null;setHydrating(false);setLinkNotices(n=>n.filter(notice=>notice!==EVIDENCE_LOAD_NOTICE));setSelected(null);if(next===view){const target=document.getElementById('main');target?.focus({preventScroll:true});target?.scrollIntoView({block:'start',behavior:'auto'});}else{sectionFocus.current=true;setView(next);}}
  function retryData(){setError('');if(pendingWeek.current)setHydrating(true);if(!index.regions.length){setLoading(true);setHydrating(true);setIndexAttempt(n=>n+1);}else if(!region){const entry=index.regions.find(r=>r.id===regionId);if(entry)invalidateData(entry.file);setLoading(true);setNavigation(n=>n+1);}else{const file=region.cells.find(c=>c.id===cell)?.file;if(file)invalidateData(file);setCellLoading(true);setCellAttempt(n=>n+1);}}
  function changeRegion(id:string){if(id===regionId)return;setJourneyTarget(null);pendingLink.current=null;pendingWeek.current=null;setHydrating(false);setLoading(true);setSelected(null);setRegionId(id);}
  function selectDailyCell(id:string){if(loading)return;setJourneyTarget(null);pendingWeek.current=null;setHydrating(false);setError('');setCell(id);setSelected(null);}
  function resetSharedView(){if(!catalog)return;setJourneyTarget(null);const state=defaultExploration(catalog,regionId);pendingLink.current=null;pendingWeek.current=null;setStart(state.start);setEnd(state.end);setCell(state.cell);setView(state.view);setMode(state.scale);setSelected(null);setHydrating(false);setLinkNotices([]);}
  function compareRecord(){document.getElementById('comparison-panel')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});document.getElementById('comparison-panel')?.focus({preventScroll:true});}
  function selectGlobeYear(year:number){if(!region)return;cancelEvidenceRestore();setStart(`${year}-01-01`<region.meta.period_start?region.meta.period_start:`${year}-01-01`);setEnd(`${year}-12-31`>region.meta.period_end?region.meta.period_end:`${year}-12-31`);setSelected(null);}
  function cancelEvidenceRestore(){pendingWeek.current=null;setHydrating(false);setSelected(null);setJourneyTarget(null);setLinkNotices(n=>n.filter(notice=>notice!==EVIDENCE_LOAD_NOTICE));}
  function selectGlobeCell(id:string,year:number){selectDailyCell(id);selectGlobeYear(year);setJourneyTarget('calendar-panel');}
  function exploreGlobeRegion(id:string,year:number){
    if(!index.regions.some(r=>r.id===id))return;
    cancelEvidenceRestore();setError('');
    if(id===regionId){setCell('ALL');selectGlobeYear(year);}
    else{
      pendingLink.current={search:new URLSearchParams({region:id,start:`${year}-01-01`,end:`${year}-12-31`,view:'explore',scale:mode}).toString(),revision:++viewRevision.current};
      setLoading(true);setHydrating(true);setRegionId(id);
    }
    setJourneyTarget('calendar-panel');
  }
  function viewEvidenceOnEarth(week:Week){navigateToView('explore');selectGlobeYear(week.year);setShowGlobe(true);setJourneyTarget('earth-panel');}
  function useFullRecord(){if(!region)return;cancelEvidenceRestore();setStart(region.meta.period_start.slice(0,10));setEnd(region.meta.period_end.slice(0,10));setSelected(null);}
  function download(kind:'csv'|'ics'){if(!region)return;if(kind==='csv')exportCSV(rows,region.meta.region,label);else exportICS(region.critical_periods,Number(end.slice(0,4))||new Date().getFullYear(),region.meta.name,label);setToast(`${kind.toUpperCase()} export downloaded`);}

  return <><a className="skip-link" href="#main">Skip to content</a><header className="site-header"><a href="#" className="brand" onClick={e=>{e.preventDefault();navigateToView('explore');}}><span className="brand-symbol"><Flame size={24}/></span><span>FIRE<span className="brand-light">TRACE</span></span></a><nav aria-label="Main navigation">{(['explore','evidence','rhythm','methods'] as const).map(v=><button key={v} className={view===v?'active':''} aria-current={view===v?'page':undefined} onClick={()=>navigateToView(v)}>{v==='explore'?'Explore the record':v==='evidence'?'Evidence & validation':v==='rhythm'?'Weekly Rhythm Index':'Methods'}</button>)}</nav><a className="header-source" href="https://firms.modaps.eosdis.nasa.gov/" target="_blank" rel="noreferrer">NASA FIRMS <ArrowUpRight size={14}/></a></header>
    <div className="masthead"><div><div className="eyebrow masthead-eyebrow">Satellite fire observatory <span className="masthead-separator">/</span> MODIS × VIIRS</div><h1>Look beyond<br className="mobile-break"/> the <em>hotspots.</em></h1><p>A changing signal doesn’t always mean a changing planet.<br/>Trace fire activity across instruments, seasons and years.</p></div></div>
    <main id="main" tabIndex={-1} aria-labelledby="workspace-title"><div className="workspace-toolbar"><div className="workspace-title" id="workspace-title"><span className="live-dot"/><span>{view==='explore'?'Explore the fire record':view==='evidence'?'Inspect the evidence':view==='rhythm'?'Weekly rhythm across seven countries':'Understand the methods'}</span></div><div className="workspace-tools"><DataBadge label={label}/><ShareView url={shareUrl} disabledReason={loading||hydrating||!dailySeriesReady?'Wait for the selected observations to load.':'Choose a valid date range within the published record.'}/></div></div>
      {view==='explore'&&<div className="calendar-scale-bar"><div className="calendar-scale-control"><span className="field-label">Calendar reference scale</span><div className="segmented" role="group" aria-label="Calendar reference scale">{(['harmonized','raw'] as const).map(m=><button key={m} className={mode===m?'active':''} onClick={()=>setMode(m)} disabled={loading||hydrating||cellLoading} aria-pressed={mode===m}>{m==='harmonized'?<Layers3 size={13}/>:<Radio size={13}/>} {m==='harmonized'?'Harmonized':'Raw baseline'}</button>)}</div></div><p className="chart-note">The scale switch changes the calendar and summary totals. Earth stays on the Aqua reference scale.</p></div>}
      {linkNotices.length>0&&<div className="share-notices"><div role="status" aria-live="polite">{linkNotices.map(notice=><p key={notice}>{notice}</p>)}</div><div className="share-notice-actions"><button onClick={resetSharedView} disabled={!catalog||loading}>Reset shared view</button><button onClick={()=>setLinkNotices([])}>Dismiss</button></div></div>}
      {isSynthetic&&<div className="synthetic-banner"><FlaskIcon/><span><strong>Synthetic demonstration.</strong> These observations were generated to test the pipeline. They are not measured fire activity.</span></div>}
      {error&&<div role="alert" className="error-banner" id="data-load-error" tabIndex={-1}><CircleHelp size={20}/><div><strong>Data not available</strong><p>{error} The interface will never substitute fabricated observations.</p></div><button className="button subtle" onClick={retryData} disabled={loading||cellLoading||hydrating}>Retry loading</button></div>}
      {view==='methods'?<Methods region={region} index={index}/>:view==='rhythm'?<RhythmView><RhythmCellMap/></RhythmView>:<div className="workspace"><aside className="sidebar"><div className="sidebar-title"><SlidersHorizontal size={15}/><span>Your view</span></div>
        <label className="field-label" htmlFor="region">Region</label><div className="select-wrap region-select"><MapPin size={17}/><select id="region" value={regionId} onChange={e=>changeRegion(e.target.value)} disabled={!index.regions.length||loading}>{!index.regions.length&&<option>No processed regions</option>}{index.regions.map(r=><option key={r.id} value={r.id}>{r.name}</option>)}</select><ChevronDown size={15}/></div>
        <details className="grid-preview"><summary>Grid preview <ChevronDown size={16}/></summary><CellMap cells={region?.cells||[]} selected={cell} onSelect={selectDailyCell} name={region?.meta.name||'Region'}/></details>{region?.meta.cell_scope&&<p className="cell-scope">{region.meta.cell_scope}</p>}
        <label className="field-label" htmlFor="cell">Spatial scope</label><div className="select-wrap"><select id="cell" value={cell} disabled={loading} onChange={e=>selectDailyCell(e.target.value)}><option value="ALL">Whole region</option>{region?.cells.map(c=><option key={c.id} value={c.id}>{c.id} · {c.lat.toFixed(2)}, {c.lon.toFixed(2)}</option>)}</select><ChevronDown size={15}/></div>
        <div className="sidebar-divider"/><label className="field-label" htmlFor="start">Observation period</label><div className="date-fields"><label><span>From</span><input id="start" aria-label="Start date" type="date" value={start} aria-invalid={!!dateError} aria-describedby={dateError?'date-range-error':undefined} disabled={loading||hydrating} min={region?.meta.period_start} max={end||region?.meta.period_end} onChange={e=>{cancelEvidenceRestore();setStart(e.target.value);}}/></label><label><span>To</span><input aria-label="End date" type="date" value={end} aria-invalid={!!dateError} aria-describedby={dateError?'date-range-error':undefined} disabled={loading||hydrating} min={start||region?.meta.period_start} max={region?.meta.period_end} onChange={e=>{cancelEvidenceRestore();setEnd(e.target.value);}}/></label></div><button className="text-button" disabled={loading||hydrating} onClick={useFullRecord}>Use full available record <ArrowRight size={13}/></button>{dateError&&!loading&&!hydrating&&<p id="date-range-error" className="date-range-error" role="alert">{dateError}</p>}
        <div className="sidebar-divider"/><span className="field-label">Observation streams</span><div className="stream-list">{['Terra','Aqua','VIIRS'].map((s,i)=><div key={s}><span className={`sensor-dot ${s.toLowerCase()}`}/><span>{s}<small>{i===2?'S-NPP · VIIRS':'MODIS'}</small></span></div>)}</div><p className="sidebar-caption">Streams are analyzed separately. Available values appear in each evidence card.</p>
        <div className="sidebar-note"><ShieldCheck size={20}/><h3>Evidence before conclusions.</h3><p>A hotspot is an observation, not a distinct fire. Unknown coverage remains unknown.</p><button onClick={()=>navigateToView('methods')}>How to read this record <ArrowUpRight size={13}/></button></div>
      </aside><div className="main-column">
        {(loading||cellLoading||hydrating||(region&&!dailySeriesReady&&!error))?<div className="loading-state" role="status"><span className="loader"/><h2>Tracing the observations…</h2><p>Loading the processed record and its evidence.</p></div>:!region?<Empty title="Ready for the first observations">Run the reproducible data pipeline to publish a region. The calendar, comparisons and evidence cards will populate from its output.</Empty>:dateError?<Empty title="Choose a valid observation period">{dateError} Your entries are preserved so you can correct them, or use the full available record.</Empty>:!dailySeriesReady?<Empty title="Daily records are unavailable">Select another grid cell or choose Whole region in the spatial scope control.</Empty>:<>
          <div className="region-heading"><div><span className="eyebrow">{scopeName} <span className="heading-slash">/</span> {start&&end?`${start.slice(0,4)}–${end.slice(0,4)}`:'Available record'}</span><h2>{region.meta.name}<span className="region-coordinate">{numeric(region.meta.centroid?.[1])?`${geoCoordinate(region.meta.centroid[1],'lat')} / ${geoCoordinate(region.meta.centroid[0],'lon')}`:''}</span></h2></div><button className="button subtle" onClick={()=>download('csv')} disabled={!rows.length}><ArrowDownToLine size={15}/> Export data</button></div>
          {view==='explore'?<><section className="panel calendar-panel" id="calendar-panel" tabIndex={-1}><PanelTitle eyebrow="01 / THE LONG VIEW" title="Burning activity calendar"></PanelTitle><p className="panel-description">{mode==='harmonized'?'Each square is a week of Aqua-reference-equivalent activity. Follow a season across years, then inspect the observations behind it.':'A deliberately naive sensor-switch baseline, shown for comparison. Counts from different instruments are not directly equivalent.'}</p><Heatmap weeks={weeks} mode={mode} label={label} onSelect={setSelected}/>{showGlobe?<div id="earth-panel" tabIndex={-1}><Suspense fallback={<div className="globe-unavailable" role="status">Loading Earth explorer…</div>}><Globe regionId={regionId} year={Number(end.slice(0,4))} onYear={selectGlobeYear} onRegion={exploreGlobeRegion} onCell={selectGlobeCell} availableCells={region.cells.map(c=>c.id)}/></Suspense></div>:<button className="button subtle globe-open" onClick={()=>{setShowGlobe(true);setJourneyTarget('earth-panel');}}><Globe2 size={15}/> Open the 3D Earth view</button>}</section>
          <ComparisonJourney weeks={weeks} onInspect={setSelected} onCompare={compareRecord} onValidate={()=>navigateToView('evidence')}/><div className="metric-strip"><div><span>{mode==='harmonized'?'AQUA-REFERENCE-EQUIVALENT ACTIVITY':'RAW BASELINE ACTIVITY'}</span><strong>{compact(total)}</strong><small>Sum of available values</small></div><div><span>RECORD IN VIEW</span><strong>{years}<i>{years===1?' year':' years'}</i></strong><small>{fmt(rows.length)} day records · {scopeName.toLowerCase()}</small></div><div><span>PEAK OBSERVED WEEK</span><strong>{peak?String(peak.week).padStart(2,'0'):'—'}<i>{peak?` / ${peak.year}`:''}</i></strong><small>{peak?prettyDate(peak.date):'No estimate available'}</small>{peak&&<button className="text-button peak-jump" onClick={()=>setSelected(peak)}>Inspect peak week <ArrowUpRight size={12}/></button>}</div></div>
          <section className="panel" id="comparison-panel" tabIndex={-1}><PanelTitle eyebrow="02 / QUESTION THE CHANGE" title="Did activity change—or the instrument?"/><ComparisonChart rows={rows} mode={mode} label={label} regionId={region.meta.region} regionName={region.meta.name} cellId={cell}/></section>
          <SeasonalContext region={region} label={label} selectedYear={Number(end.slice(0,4))||new Date().getFullYear()} onExport={()=>download('ics')} cell={cell}/>
          <AnomalyPanel anomalies={selectedAnomalies} cell={cell} onSelect={openAnomaly} label={label}/>
          </>:<><section className="panel"><PanelTitle eyebrow="HELD-OUT COMPARISON" title="Let the baselines compete"/><p className="panel-description">Performance against the Aqua reference. A more complex model is useful only if it improves validation performance; test results remain visible even when they disappoint.</p><EvaluationTable rows={region.eval}/><ChartLabel label={label}/></section><section className="panel rhythm-panel"><PanelTitle eyebrow="WEEKLY RHYTHM INDEX" title="Weekly pattern: see the 7-country test"/><p className="panel-description">The weekday analysis covers seven countries, not only the regions in this calendar, so it has its own page with the official pre-specified decision, robustness checks and an exploratory per-cell map.</p><button className="text-button" onClick={()=>navigateToView('rhythm')}>Open the Weekly Rhythm Index <ArrowRight size={14}/></button></section><section className="panel"><PanelTitle eyebrow="TRACEABILITY" title="What every estimate carries"/><div className="provenance-grid"><div><Database size={19}/><h3>Source observations</h3><p>Separate Terra, Aqua and VIIRS counts, without silently treating missing records as zero.</p></div><div><Layers3 size={19}/><h3>Transformation</h3><p>The selected calibration model and whether the value was observed, converted or reconstructed.</p></div><div><ShieldCheck size={19}/><h3>Uncertainty</h3><p>Reported intervals and coverage limitations accompany the estimate.</p></div></div><button className="text-button" onClick={()=>navigateToView('explore')}>Open a calendar week to inspect evidence <ArrowRight size={14}/></button></section></>}
          <div className="bottom-note"><CircleHelp size={15}/><p>{region.meta.coverage_note||'Cloud and overpass coverage may be unknown. These observations are not a complete inventory of fires.'}</p></div>
        </>}
      </div></div>}
    </main><footer><a className="brand footer-brand" href="#" onClick={e=>{e.preventDefault();window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}}><Flame size={18}/> FIRETRACE</a><p>Built for NASA Space Apps · Bhaktapur<br/><span>NASA does not endorse this project.</span></p><button onClick={()=>navigateToView('methods')}>Sources & limitations <ArrowUpRight size={13}/></button></footer>
    {selected&&region&&<EvidenceDrawer week={selected} onClose={closeEvidence} onViewEarth={()=>viewEvidenceOnEarth(selected)} label={label} region={region} shareUrl={shareUrl} cellId={cell}/>}{toast&&<div role="status" className="toast"><Check size={16}/>{toast}</div>}
  </>;
}

function FlaskIcon(){return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M9 3h6M10 3v7L4 20h16l-6-10V3M7 15h10"/></svg>;}
