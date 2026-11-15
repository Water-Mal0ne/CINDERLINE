import {useEffect, useId, useMemo, useState} from 'react';
import type {KeyboardEvent} from 'react';
import {ArrowDownToLine, CalendarDays, ChevronLeft, ChevronRight, Info, Waves} from 'lucide-react';
import type {Region} from './types';
import {compact, fmt, numeric} from './utils';
import './seasonal.css';

interface Props {region: Region; label: string; selectedYear: number; onExport: () => void; cell: string}
const W=760, H=245, L=54, R=20, T=22, B=37;
const DAY=86400000;

function dateSpan(year:number,startWeek:number,endWeek=startWeek) {
  const first=Date.UTC(year,0,1),last=Date.UTC(year,11,31);
  const start=new Date(Math.min(first+(startWeek-1)*7*DAY,last));
  const end=new Date(Math.min(first+(endWeek*7-1)*DAY,last));
  const f=new Intl.DateTimeFormat('en',{month:'short',day:'numeric',timeZone:'UTC'});
  return `${f.format(start)}–${f.format(end)}, ${year}`;
}

function contiguous<T>(rows:T[],ok:(row:T)=>boolean):T[][] {
  const segments:T[][]=[];
  let current:T[]=[];
  for(const row of rows){if(ok(row)){current.push(row);}else if(current.length){segments.push(current);current=[];}}
  if(current.length)segments.push(current);
  return segments;
}

export default function SeasonalContext({region,label,selectedYear,onExport,cell}:Props) {
  const weekControlId=useId();
  const points=useMemo(()=>{
    const byWeek=new Map(region.weekly_climatology.map(p=>[p.week,p]));
    return Array.from({length:52},(_,i)=>byWeek.get(i+1)||{week:i+1,median:null,p10:null,p90:null,critical:false});
  },[region]);
  const peak=useMemo(()=>points.filter(p=>numeric(p.median)&&p.median>0).sort((a,b)=>b.median!-a.median!||a.week-b.week)[0],[points]);
  const [selected,setSelected]=useState<number>(peak?.week||1);
  const [hover,setHover]=useState<number|null>(null);
  useEffect(()=>{setSelected(peak?.week||1);setHover(null);},[region.meta.region,peak?.week]);
  const active=points[(hover??selected)-1];
  const hasData=points.some(p=>numeric(p.median));
  const periods=region.critical_periods.filter(p=>Number.isInteger(p.start_week)&&p.start_week>=1&&p.start_week<=52&&p.end_week>=p.start_week)
    .map(p=>({...p,end_week:Math.min(p.end_week,52)}));
  const max=Math.max(1,...points.flatMap(p=>[p.p90,p.median]).filter(numeric))*1.08;
  const x=(week:number)=>L+(week-1)/51*(W-L-R);
  const y=(value:number)=>H-B-value/max*(H-T-B);
  const select=(week:number)=>{setHover(null);setSelected(Math.max(1,Math.min(52,week)));};
  const keyboard=(event:KeyboardEvent<SVGSVGElement>)=>{
    if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){
      event.preventDefault();select(event.key==='Home'?1:event.key==='End'?52:selected+(event.key==='ArrowLeft'?-1:1));
    }
  };
  const lineSegments=contiguous(points,p=>numeric(p.median));
  const bandSegments=contiguous(points,p=>numeric(p.p10)&&numeric(p.p90));
  return <section className="seasonal-context" id="seasonal-context" aria-labelledby="seasonal-title">
    <div className="seasonal-intro"><div><span className="eyebrow">03 / SEASONAL CONTEXT</span><h2 id="seasonal-title">The season behind the signal.</h2>
      <p>Explore when activity has typically been highest across {region.meta.name}. These patterns describe the historical record.</p></div>
      <span className="seasonal-scope"><Waves size={14}/> National baseline · {region.meta.period_start.slice(0,4)}–{region.meta.period_end.slice(0,4)}</span></div>
    {cell!=='ALL'&&<p className="seasonal-national"><Info size={15}/><span>The map is focused on a grid cell. This section continues to show <strong>{region.meta.name} national patterns</strong>.</span></p>}
    <div className="seasonal-grid"><div className="seasonal-chart-card">
      <div className="seasonal-chart-heading"><div><span className="seasonal-kicker">TYPICAL WEEKLY ACTIVITY</span><h3>{peak?<>Peak around <span>{dateSpan(selectedYear,peak.week)}</span></>:'Seasonal pattern'}</h3></div>
        {peak&&<div className="seasonal-peak"><strong>{compact(peak.median)}</strong><span>median detections / week</span></div>}</div>
      <div className="seasonal-legend"><span><i/>Median</span><span><i className="seasonal-band-key"/>10th–90th percentile</span><span className="seasonal-units">Aqua-reference-equivalent scale</span></div>
      {hasData?<><div className="seasonal-plot-scroller"><svg className="seasonal-chart" viewBox={`0 0 ${W} ${H}`} tabIndex={0} role="group" aria-label={`${region.meta.name} national historical weekly activity`} aria-describedby="seasonal-instructions" onKeyDown={keyboard}
        onMouseLeave={()=>setHover(null)} onMouseMove={event=>{const box=event.currentTarget.getBoundingClientRect();const week=Math.round(((event.clientX-box.left)/box.width*W-L)/(W-L-R)*51)+1;setHover(Math.max(1,Math.min(52,week)));}}
        onClick={()=>hover!==null&&select(hover)}>
        {[0,.5,1].map(f=><g key={f}><line x1={L} x2={W-R} y1={y(max*f)} y2={y(max*f)} className="seasonal-gridline"/><text x={L-10} y={y(max*f)+4} textAnchor="end" className="seasonal-axis">{compact(max*f)}</text></g>)}
        {points.filter(p=>p.critical).map(p=><rect key={p.week} x={x(p.week)-5} y={T} width={(W-L-R)/52+1} height={H-T-B} className="seasonal-critical-shade"/>)}
        {bandSegments.map((segment,i)=><path key={i} d={segment.map((p,j)=>`${j?'L':'M'}${x(p.week)},${y(p.p90!)}`).join(' ')+[...segment].reverse().map(p=>`L${x(p.week)},${y(p.p10!)}`).join(' ')+' Z'} className="seasonal-band"/>)}
        {lineSegments.map((segment,i)=><path key={i} d={segment.map((p,j)=>`${j?'L':'M'}${x(p.week)},${y(p.median!)}`).join(' ')} className="seasonal-median"/>)}
        {lineSegments.filter(segment=>segment.length===1&&segment[0].week!==active.week).map(([p])=><circle key={p.week} cx={x(p.week)} cy={y(p.median!)} r={3} className="seasonal-point seasonal-isolated-point"/>)}
        {[1,14,27,40,52].map(week=><text key={week} x={x(week)} y={H-9} textAnchor="middle" className="seasonal-axis">{new Date(Date.UTC(selectedYear,0,1+(week-1)*7)).toLocaleDateString('en',{month:'short',timeZone:'UTC'}).toUpperCase()}</text>)}
        <line x1={x(active.week)} x2={x(active.week)} y1={T} y2={H-B} className="seasonal-cursor"/>
        {numeric(active.median)&&<circle cx={x(active.week)} cy={y(active.median)} r={5} className="seasonal-point"/>}
        {hover!==null&&<g className="seasonal-tooltip" transform={`translate(${Math.max(L,Math.min(W-236,x(active.week)+14))},${T+7})`} aria-hidden="true">
          <rect width={216} height={60} rx={5}/><text x={12} y={20}>{dateSpan(selectedYear,active.week)}</text>
          <text x={12} y={42}>Median {fmt(active.median,1)} · Week {active.week}</text>
        </g>}
      </svg></div><div className="seasonal-readout" aria-live="polite" aria-atomic="true"><div><span>WEEK {String(active.week).padStart(2,'0')}</span><strong>{dateSpan(selectedYear,active.week)}</strong></div>
        <div><span>HISTORICAL MEDIAN</span><strong>{fmt(active.median,1)}</strong></div><div><span>10TH–90TH PERCENTILE</span><strong>{numeric(active.p10)&&numeric(active.p90)?`${fmt(active.p10,1)}–${fmt(active.p90,1)}`:'Unavailable'}</strong></div>
        <div className="seasonal-steppers"><button type="button" aria-label="Previous week" onClick={()=>select(selected-1)} disabled={selected<=1}><ChevronLeft size={16}/></button><button type="button" aria-label="Next week" onClick={()=>select(selected+1)} disabled={selected>=52}><ChevronRight size={16}/></button></div></div>
      <div className="seasonal-week-control"><label htmlFor={weekControlId}>Explore a historical week <strong>{String(selected).padStart(2,'0')} / 52</strong></label><input id={weekControlId} type="range" min={1} max={52} step={1} value={selected} onChange={event=>select(Number(event.target.value))} aria-valuetext={`Week ${selected}, ${dateSpan(selectedYear,selected)}, historical median ${fmt(points[selected-1].median,1)} Aqua-reference-equivalent detections`} aria-describedby="seasonal-instructions"/><div aria-hidden="true"><span>January</span><span>December</span></div></div>
      <p className="seasonal-instructions" id="seasonal-instructions">Drag the week slider or use arrow keys to explore; Home and End jump to either edge. Hover over the chart for a quick preview.</p></>:
      <div className="seasonal-empty"><Waves size={28}/><h3>No complete seasonal baseline</h3><p>Historical week estimates will appear when sufficient complete observations are available.</p></div>}
      <p className="seasonal-method-note">Seven-day periods begin January 1. Only complete periods contribute; the final partial period is omitted. Shading marks historically high-activity weeks, not a forecast.</p>
      <span className={`seasonal-data-label ${/synthetic/i.test(label)?'is-synthetic':''}`}>{label}</span>
    </div><aside className="seasonal-period-card" aria-labelledby="seasonal-period-title"><div className="seasonal-period-heading"><CalendarDays size={19}/><span>{selectedYear} DATE GUIDE</span></div>
      <h3 id="seasonal-period-title">Historical high-activity periods</h3><p>Seasonal windows translated into dates for the selected year.</p>
      <div className="seasonal-period-list">{periods.length?periods.map((period,i)=><button type="button" key={`${period.start_week}-${period.end_week}`} onClick={()=>select(period.start_week)} aria-pressed={selected>=period.start_week&&selected<=period.end_week} className={active.week>=period.start_week&&active.week<=period.end_week?'is-selected':''}>
        <span className="seasonal-period-number">{String(i+1).padStart(2,'0')}</span><span><strong>{dateSpan(selectedYear,period.start_week,period.end_week)}</strong><small>Weeks {period.start_week}–{period.end_week} · historical threshold</small></span><ChevronRight size={15}/>
      </button>):<div className="seasonal-no-periods">No high-activity periods meet the historical threshold for this region.</div>}</div>
      <button type="button" className="seasonal-export" onClick={onExport} disabled={!periods.length}><ArrowDownToLine size={16}/> Add historical periods to calendar</button>
      <p className="seasonal-export-note">Exports an .ics file for {selectedYear}. This is a historical planning reference, not an alert or prediction.</p>
    </aside></div>
  </section>;
}
