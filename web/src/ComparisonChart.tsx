import {useId,useMemo,useState} from 'react';
import {ArrowDownToLine,ChevronLeft,ChevronRight,Table2} from 'lucide-react';
import type {Daily} from './types';
import {compact,fmt,monthly,numeric,saveFile,sourcePeriods} from './utils';
import './comparison.css';

type Series='raw'|'harmonized'|'aqua';
export default function ComparisonChart({rows,mode,label}:{rows:Daily[];mode:'raw'|'harmonized';label:string}) {
  const points=useMemo(()=>monthly(rows),[rows]);
  const periods=useMemo(()=>sourcePeriods(rows),[rows]);
  const [active,setActive]=useState(0),[referenceOnly,setReferenceOnly]=useState(false),[showTable,setShowTable]=useState(false);
  const sliderId=useId();
  if(!points.length)return <p className="muted">No observations are available for this comparison.</p>;
  const selected=Math.min(active,points.length-1),point=points[selected];
  const monthParts=point.date.split('-').map(Number);
  const expectedDays=new Date(Date.UTC(monthParts[0],monthParts[1],0)).getUTCDate();
  const partial=[point.rawDays,point.harmonizedDays,point.aquaDays].some(days=>days!==expectedDays);
  const exportMonths=()=>{
    const fields=['month','raw_sensor_switch_detections','aqua_equivalent_detections','observed_aqua_detections','raw_days','harmonized_days','aqua_days','data_label'];
    const quote=(v:unknown)=>`"${String(v??'').replaceAll('"','""')}"`;
    const values=points.map(p=>[p.date,p.raw,p.harmonized,p.aqua,p.rawDays,p.harmonizedDays,p.aquaDays,label].map(quote).join(','));
    saveFile('FIRETRACE_monthly_comparison.csv','\uFEFF'+[fields.join(','),...values].join('\r\n'),'text/csv;charset=utf-8');
  };
  const W=850,H=230,L=55,R=15,T=22,B=33;
  const series:Series[]=referenceOnly?['harmonized','aqua']:['raw','harmonized','aqua'];
  const max=Math.max(1,...points.flatMap(p=>series.map(s=>p[s])).filter(numeric))*1.06;
  const x=(i:number)=>L+i/Math.max(points.length-1,1)*(W-L-R);
  const y=(v:number)=>H-B-v/max*(H-T-B);
  const path=(key:Series)=>{let prior=false;return points.map((p,i)=>{if(!numeric(p[key])){prior=false;return '';}const cmd=prior?'L':'M';prior=true;return `${cmd}${x(i)},${y(p[key]!)}`;}).join(' ');};
  const ticks=[0,Math.floor((points.length-1)/3),Math.floor((points.length-1)*2/3),points.length-1].filter((n,i,a)=>a.indexOf(n)===i);
  return <><div className="comparison-controls"><div className="trace-legend"><span><i className="line-key orange"/>Aqua-reference-equivalent record</span><span><i className="line-key aqua"/>Aqua observed</span>{!referenceOnly&&<span><i className="line-key dashed"/>Raw sensor-switch baseline</span>}</div><button className="chart-scale-button" aria-pressed={referenceOnly} onClick={()=>setReferenceOnly(v=>!v)}>{referenceOnly?'Show raw baseline':'Focus on the Aqua scale'}</button></div>
    <div className="svg-chart"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Monthly comparison of raw sensor-switch baseline, Aqua-reference-equivalent record and observed Aqua reference" onPointerMove={e=>{const r=e.currentTarget.getBoundingClientRect();setActive(Math.min(points.length-1,Math.max(0,Math.round(((e.clientX-r.left)/r.width*W-L)/(W-L-R)*(points.length-1)))));}}>
      {[0,1,2,3].map(i=><g key={i}><line x1={L} x2={W-R} y1={y(max*i/3)} y2={y(max*i/3)} stroke="#334147" strokeDasharray="3 5"/><text x={L-9} y={y(max*i/3)+4} textAnchor="end" className="svg-axis">{compact(max*i/3)}</text></g>)}
      {ticks.map(i=><text key={i} x={x(i)} y={H-6} textAnchor={i===0?'start':i===points.length-1?'end':'middle'} className="svg-axis">{points[i].date}</text>)}
      {!referenceOnly&&<path d={path('raw')} stroke="#92a2a8" strokeWidth={mode==='raw'?2.3:1.5} strokeDasharray="5 4" fill="none" opacity=".65"/>}
      <path d={path('harmonized')} stroke="#f79963" strokeWidth="2.7" fill="none"/>
      <path d={path('aqua')} stroke="#8fc8d2" strokeWidth="1.8" strokeDasharray="2 3" fill="none"/>
      <line x1={x(selected)} x2={x(selected)} y1={T} y2={H-B} stroke="#e4e6d9" opacity=".4"/>
      {series.map(s=>numeric(point[s])&&<circle key={s} cx={x(selected)} cy={y(point[s]!)} r="3" fill={s==='aqua'?'#8fc8d2':s==='harmonized'?'#f79963':'#bac5c7'}/>)}
    </svg></div><div className="month-inspector"><div className="month-navigation"><label htmlFor={sliderId}>Inspect month <strong>{point.date}</strong></label><div><button type="button" className="icon-button" aria-label="Previous month" disabled={selected===0} onClick={()=>setActive(selected-1)}><ChevronLeft size={18}/></button><button type="button" className="icon-button" aria-label="Next month" disabled={selected===points.length-1} onClick={()=>setActive(selected+1)}><ChevronRight size={18}/></button></div></div><input id={sliderId} type="range" min="0" max={points.length-1} step="1" value={selected} onChange={e=>setActive(Number(e.target.value))} aria-valuetext={`${point.date}, raw ${fmt(point.raw,1)}, Aqua-reference-equivalent ${fmt(point.harmonized,1)}, Aqua observed ${fmt(point.aqua,1)}`}/><div className="month-readout" aria-live="polite"><span>Raw <strong>{fmt(point.raw,1)}</strong><small>{point.rawDays} of {expectedDays} days</small></span><span>Reference scale <strong>{fmt(point.harmonized,1)}</strong><small>{point.harmonizedDays} of {expectedDays} days</small></span><span>Aqua observed <strong>{fmt(point.aqua,1)}</strong><small>{point.aquaDays} of {expectedDays} days</small></span></div>{partial&&<p className="comparison-partial">This month includes a partial date selection or missing values. Totals can represent different numbers of days.</p>}</div>
    <div className="comparison-actions"><button className="button subtle" type="button" onClick={()=>setShowTable(v=>!v)} aria-expanded={showTable}><Table2 size={15}/>{showTable?'Hide monthly table':'View monthly table'}</button><button className="button subtle" type="button" onClick={exportMonths}><ArrowDownToLine size={15}/>Export comparison</button></div>
    {showTable&&<div className="table-scroll comparison-table" tabIndex={0} aria-label="Monthly comparison values"><table><caption>Monthly totals and number of available daily values in the selected date range</caption><thead><tr><th scope="col">Month</th><th scope="col">Raw</th><th scope="col">Aqua-reference-equivalent</th><th scope="col">Observed Aqua</th><th scope="col">Days: raw / converted / Aqua</th></tr></thead><tbody>{points.map(p=><tr key={p.date}><th scope="row">{p.date}</th><td>{fmt(p.raw,1)}</td><td>{fmt(p.harmonized,1)}</td><td>{fmt(p.aqua,1)}</td><td>{p.rawDays} / {p.harmonizedDays} / {p.aquaDays}</td></tr>)}</tbody></table></div>}
    <div className="source-timeline">{periods.observed&&<span><i className="sensor-dot aqua"/><strong>{periods.observed.start.slice(0,4)}–{periods.observed.end.slice(0,4)}</strong> Direct Aqua observations; no conversion</span>}{periods.converted&&<span><i className="sensor-dot viirs"/><strong>{periods.converted.start.slice(0,4)}–{periods.converted.end.slice(0,4)}</strong> VIIRS converted to the Aqua scale</span>}</div><p className="chart-note">Monthly sums of available values; compare day counts before interpreting differences. Early direct-Aqua agreement is an identity, not independent evidence of model skill. No line is ground truth.</p><span className="chart-label">{label}</span>
  </>;
}
