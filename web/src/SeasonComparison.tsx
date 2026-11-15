import {useEffect,useId,useMemo,useState} from 'react';
import {loadData,invalidateData} from './loadData';
import {seasonKeys,summarizeSeason,validateSeasonPayload} from './seasonComparisonData';
import type {SeasonPayload,SeasonMask} from './seasonComparisonData';
import './season-comparison.css';

const MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const NAMES=['Observed Aqua','Raw VIIRS','Simple conversion (B1)','Selected conversion'];
const COLORS=['#b9dce8','#8c979c','#c2b897','#ed9562'];
const show=(n:number|null,digits=1)=>n===null?'Unavailable':n.toLocaleString('en',{maximumFractionDigits:digits,minimumFractionDigits:digits});

export default function SeasonComparison({regionId,regionName,cellId='ALL'}:{regionId:string;regionName:string;cellId?:string}){
  const id=useId();
  const [data,setData]=useState<SeasonPayload|null>(null),[error,setError]=useState(false),[attempt,setAttempt]=useState(0);
  const [year,setYear]=useState(0),[mask,setMask]=useState<SeasonMask>('primary'),[view,setView]=useState<'shares'|'counts'>('shares');
  useEffect(()=>{
    const controller=new AbortController();setError(false);
    loadData<unknown>('season-comparison.json',controller.signal).then(v=>{if(!controller.signal.aborted)setData(validateSeasonPayload(v));}).catch(e=>{if(e.name!=='AbortError'&&!controller.signal.aborted)setError(true);});
    return()=>controller.abort();
  },[attempt]);
  const country=data?.countries[regionId];
  const summary=useMemo(()=>country?summarizeSeason(country.masks[mask],year):null,[country,mask,year]);
  const title=<><div className="season-compare-heading"><span className="season-compare-kicker">Retrospective national comparison · 2020–2024</span><h2 id={`${id}-title`}>Does the conversion preserve the season?</h2></div><p className="season-compare-intro">Compare total-count agreement with the distribution of activity across months. A better total can still hide a less faithful seasonal pattern.</p></>;
  if(error)return <section className="panel season-compare" aria-labelledby={`${id}-title`}>{title}<p role="alert">The seasonal comparison could not be loaded.</p><button className="button subtle" onClick={()=>{invalidateData('season-comparison.json');setData(null);setAttempt(n=>n+1);}}>Retry seasonal comparison</button></section>;
  if(!data)return <section className="panel season-compare" aria-labelledby={`${id}-title`}>{title}<p role="status">Loading the verified seasonal comparison…</p></section>;
  if(!country||!summary)return <section className="panel season-compare" aria-labelledby={`${id}-title`}>{title}<p>No verified seasonal comparison is available for this country.</p></section>;
  const values=view==='shares'?summary.shares:summary.counts;
  const W=720,H=240,L=54,R=16,T=16,B=36;
  const maximum=Math.max(1,...values.flat().filter((v):v is number=>v!==null));
  const x=(m:number)=>L+m*(W-L-R)/11,y=(v:number)=>T+(1-v/maximum)*(H-T-B);
  const period=year===0?'2020–2024 equal-year average':String(year);
  const retained=year===0?`${show(summary.retainedDays)} retained dates per year on average`:`${show(summary.retainedDays,0)} retained dates`;
  return <section className="panel season-compare" id="season-comparison-panel" aria-labelledby={`${id}-title`}>
    {title}
    <p className="season-compare-scope"><strong>{regionName} national totals</strong> · {period}. {retained}.</p>
    <p className="chart-note">This study has its own year, scale and outage controls. Calendar dates, raw/harmonized mode and selected grid cells do not change it. {cellId!=='ALL'?'Your selected grid cell is not evaluated here. ':''}The 2025 calendar extension is outside this study.</p>
    <div className="season-compare-controls">
      <label htmlFor={`${id}-year`}>Study period<select id={`${id}-year`} value={year} onChange={e=>setYear(Number(e.target.value))}><option value={0}>All five years</option>{data.years.map(v=><option key={v} value={v}>{v}</option>)}</select></label>
      <label htmlFor={`${id}-mask`}>Common retained dates<select id={`${id}-mask`} value={mask} onChange={e=>setMask(e.target.value as SeasonMask)}><option value="primary">Primary exclusions</option><option value="padded">Exclusions padded ±1 day</option></select></label>
      <div className="season-compare-switch" role="group" aria-label="Seasonal chart measure"><button type="button" aria-pressed={view==='shares'} onClick={()=>setView('shares')}>Monthly share</button><button type="button" aria-pressed={view==='counts'} onClick={()=>setView('counts')}>Detection counts</button></div>
    </div>
    <div className="season-compare-legend">{seasonKeys.map((key,s)=><span key={key}><i style={{backgroundColor:COLORS[s]}}/>{s===3?`Selected ${country.model}`:NAMES[s]}</span>)}</div>
    <p className="season-compare-axis-label">{view==='shares'?'Share of each series’ retained-year total (%)':'Recorded counts / Aqua-reference-equivalent estimates'}{year===0?' · mean across five years':''}</p>
    <div className="season-compare-plot" tabIndex={0} role="region" aria-label="Scrollable monthly comparison chart"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby={`${id}-chart-title ${id}-chart-desc`}>
      <title id={`${id}-chart-title`}>{regionName}: {view==='shares'?'monthly activity shares':'monthly counts'}, {period}</title><desc id={`${id}-chart-desc`}>Four series on the same retained dates. Exact monthly values are in the expandable table below. Lines may overlap when a simple ratio preserves monthly shares.</desc>
      {[0,.5,1].map(f=><g key={f}><line x1={L} x2={W-R} y1={y(maximum*f)} y2={y(maximum*f)} className="season-compare-grid"/><text x={L-8} y={y(maximum*f)+4} textAnchor="end">{maximum*f>=1000?`${show(maximum*f/1000,0)}k`:show(maximum*f,0)}</text></g>)}
      {values.map((series,s)=>series.every(v=>v!==null)&&<path key={s} d={series.map((v,m)=>`${m?'L':'M'}${x(m)},${y(v!)}`).join(' ')} fill="none" stroke={COLORS[s]} strokeWidth={s===3?3:2} strokeDasharray={s===1?'3 5':s===2?'8 4':undefined}/>)}
      {MONTHS.map((m,i)=><text key={m} x={x(i)} y={H-10} textAnchor="middle">{m}</text>)}
    </svg></div>
    <p className="chart-note">For a whole-year conversion, one constant ratio changes the total but cannot change monthly shares: raw VIIRS and B1 overlap in that view.{country.model==='B1'?' The selected model is B1, so those two conversions also coincide.':''}</p>
    <div className="table-scroll season-compare-table" tabIndex={0} role="region" aria-label="Count and seasonal-pattern agreement"><table><caption>{year===0?'Mean of the five yearly errors; lower is closer to Aqua.':'Errors for the selected year; lower is closer to Aqua.'}</caption><thead><tr><th scope="col">VIIRS alternative</th><th scope="col">Absolute total-count error</th><th scope="col">Monthly-pattern disagreement</th></tr></thead><tbody>{[1,2,3].map(s=><tr key={s}><th scope="row">{s===3?`Selected ${country.model}`:NAMES[s]}</th><td>{show(summary.countError[s])}{summary.countError[s]!==null?'%':''}</td><td>{show(summary.patternError[s])}{summary.patternError[s]!==null?' points':''}</td></tr>)}</tbody></table></div>
    <p className="chart-note">Total-count error compares totals over retained dates. Pattern disagreement is total variation × 100 between the twelve monthly shares; it ranges from 0 to 100 points and is not a percentage of actual fires. {year===0&&(view==='shares'?'The five-year chart averages each year’s monthly shares separately; its smooth appearance can hide differences between years.':'The five-year chart averages the monthly counts across years; this can hide differences between years.')}</p>
    <details className="season-compare-details"><summary>Inspect monthly values and retained dates</summary><div className="table-scroll" tabIndex={0} role="region" aria-label="Monthly seasonal comparison values"><table><caption>{view==='shares'?'Monthly shares (%)':'Monthly counts / reference-equivalent estimates'} · {period}. {year===0?'Retained dates are averaged by month.':''}</caption><thead><tr><th scope="col">Month</th><th scope="col">Retained dates</th>{NAMES.map((name,s)=><th scope="col" key={name}>{s===3?`Selected ${country.model}`:name}</th>)}</tr></thead><tbody>{MONTHS.map((m,i)=><tr key={m}><th scope="row">{m}</th><td>{show((year===0?country.masks[mask]:country.masks[mask].filter(f=>f.year===year)).reduce((n,f)=>n+f.months[i][0],0)/summary.years)}</td>{values.map((series,s)=><td key={s}>{show(series[i],2)}</td>)}</tr>)}</tbody></table></div></details>
    <details className="season-compare-details"><summary>Study limits and source</summary><p>The same excluded dates are removed from Aqua and every VIIRS alternative: {data.mask_days[mask]} dates across 2020–2024 with the {mask==='primary'?'primary':'padded'} mask. Retained dates do not establish cloud-free observation coverage. Totals are not extrapolated to fill gaps.</p><p>This is a retrospective comparison of previously examined years using frozen models, not a new untouched test. Aqua is an instrument reference, not ground truth. These results do not establish local accuracy, ignition cause or a forecast.</p><p>Source: independently verified whole-year replacement controls. <a href={`${import.meta.env.BASE_URL}data/season-comparison.json`} target="_blank" rel="noreferrer">Open values and provenance</a>.</p></details>
  </section>;
}
