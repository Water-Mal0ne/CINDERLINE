import {useEffect,useId,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import {loadObservationIndex,loadObservationMonth,observationCountry,observationMonthLabel} from './observationDetail';
import type {ObservationIndex,ObservationMonth,ObservationPoint} from './observationDetail';
import './observation-detail.css';

export type ObservationMode='harmonized'|'observations';
export type ObservationStatus='idle'|'loading'|'ready'|'error';
export interface ObservationControlsProps {
  mode:ObservationMode;onMode:(mode:ObservationMode)=>void;month?:string;onMonth?:(month:string)=>void;regionName?:string;
  availableMonths?:string[];status?:ObservationStatus;error?:string;onRetry?:()=>void;pointCount?:number;
  display?:'grid'|'points';detailLoading?:boolean;detailError?:string;loadedPointCount?:number;detailHint?:string;
  selectedPoint?:ObservationPoint|null;onClearSelection?:()=>void;sourceUrl?:string;
  children?:ReactNode;
}

/** Cancellation plus key matching prevents the previous country's data flashing in a new selection. */
export function useObservationDetail({enabled,country,month}:{enabled:boolean;country:string;month:string}){
  const [attempt,setAttempt]=useState(0);
  const [state,setState]=useState<{key:string;status:ObservationStatus;index:ObservationIndex|null;monthData:ObservationMonth|null;error:string}>({key:'',status:'idle',index:null,monthData:null,error:''});
  const key=`${country}:${month}:${attempt}`;
  useEffect(()=>{
    if(!enabled)return;const controller=new AbortController();
    setState({key,status:'loading',index:null,monthData:null,error:''});
    (async()=>{
      const options={reload:attempt>0,baseUrl:`${import.meta.env.BASE_URL}data/`};
      const index=await loadObservationIndex(controller.signal,options);
      const monthData=await loadObservationMonth(index,country,month,controller.signal,options);
      if(!controller.signal.aborted)setState({key,status:'ready',index,monthData,error:''});
    })().catch(error=>{if(!controller.signal.aborted)setState({key,status:'error',index:null,monthData:null,error:error instanceof Error?error.message:'Detailed observations could not be loaded.'});});
    return()=>controller.abort();
  },[enabled,country,month,attempt,key]);
  const current=enabled&&state.key===key?state:{key,status:enabled?'loading':'idle',index:null,monthData:null,error:''} as typeof state;
  return {...current,availableMonths:observationCountry(current.index,country)?.months.map(m=>m.month)??[],retry:()=>setAttempt(n=>n+1)};
}

const fmt=(value:number)=>new Intl.NumberFormat('en').format(value);
const measure=(value:number|null,unit:string)=>value===null?'Unavailable':`${fmt(value)} ${unit}`;

export default function ObservationControls({mode,onMode,month='2024-04',onMonth=()=>{},regionName='',availableMonths=[],status='idle',error,onRetry=()=>{},pointCount,display='grid',detailLoading=false,detailError,loadedPointCount,detailHint,selectedPoint,onClearSelection,sourceUrl,children}:ObservationControlsProps){
  const id=useId(),months=availableMonths.length?availableMonths:Array.from({length:12},(_,i)=>`2024-${String(i+1).padStart(2,'0')}`);
  const selectedEvidence=useRef<HTMLElement>(null),monthControl=useRef<HTMLSelectElement>(null);
  useEffect(()=>{
    if(mode==='observations'&&selectedPoint){
      selectedEvidence.current?.focus({preventScroll:true});
      selectedEvidence.current?.scrollIntoView({block:'nearest'});
    }
  },[mode,selectedPoint?.id]);
  const clearSelection=()=>{onClearSelection?.();monthControl.current?.focus({preventScroll:true});};
  return <div className="observation-controls">
    <div className="observation-mode" role="group" aria-label="Earth data layer">
      <button type="button" aria-pressed={mode==='harmonized'} onClick={()=>onMode('harmonized')}>Harmonized overview</button>
      <button type="button" aria-pressed={mode==='observations'} onClick={()=>onMode('observations')}>Satellite observations</button>
    </div>
    {mode==='observations'&&<div className="observation-context">
      <div className="observation-context-row"><div><strong>Observed VIIRS detections · not harmonized · UTC dates</strong><p>VIIRS S-NPP · {regionName} · {observationMonthLabel(month)}</p></div><label htmlFor={`${id}-month`}>Observation month<select ref={monthControl} id={`${id}-month`} value={month} onChange={e=>onMonth(e.target.value)}>{months.map(m=><option key={m} value={m}>{observationMonthLabel(m)}</option>)}</select></label></div>
      <p className="observation-scope">2024 detail only; this month is independent of the historical calendar. UTC records include detections on calendar-excluded dates, so totals differ.</p>
      {status==='loading'&&<p className="observation-status" role="status">Loading this month’s observed detections…</p>}
      {status==='error'&&<div className="observation-error" role="alert"><p>{error||'Detailed observations could not be loaded.'}</p><button type="button" className="chart-scale-button" onClick={onRetry}>Retry observations</button></div>}
      {children}
      {status==='ready'&&<div className="observation-status" role="status">{pointCount===0?<p>No qualifying archived detections in this month. This does not establish that no fires occurred.</p>:<><p><strong>{fmt(pointCount??0)}</strong> qualifying archived detections in this country and month. {display==='grid'?'The grid groups them into 0.05° cells; zoom closer to inspect individual detections.':`${fmt(loadedPointCount??0)} detections loaded in nearby tiles. Markers are schematic pixel centres, not fire boundaries.`}</p>{detailHint&&<p>{detailHint}</p>}</>}{detailLoading&&<p>Loading detections for this view…</p>}</div>}
      {detailError&&<div className="observation-error" role="alert"><p>{detailError}</p><button type="button" className="chart-scale-button" onClick={onRetry}>Retry observations</button></div>}
      {selectedPoint&&<section ref={selectedEvidence} tabIndex={-1} className="observation-selection" aria-label="Selected satellite observation"><div className="observation-selection-heading"><h4>Observed hotspot</h4>{onClearSelection&&<button type="button" className="text-button" onClick={clearSelection}>Clear observation</button>}</div><p>{selectedPoint.lat.toFixed(5)}°, {selectedPoint.lon.toFixed(5)}° · pixel centre</p><dl><div><dt>Satellite</dt><dd>VIIRS S-NPP</dd></div><div><dt>Acquired (UTC)</dt><dd>{selectedPoint.utc.replace('T',' ').replace(/:00(?:\.000)?Z$/,' UTC')}</dd></div><div><dt>Confidence</dt><dd>{selectedPoint.confidence==='h'?'High':'Nominal'}</dd></div><div><dt>Day / night</dt><dd>{selectedPoint.daynight==='D'?'Day':selectedPoint.daynight==='N'?'Night':'Unknown'}</dd></div><div><dt>Scan × track</dt><dd>{measure(selectedPoint.scan,'km')} × {measure(selectedPoint.track,'km')}</dd></div><div><dt>Observed radiative power</dt><dd>{measure(selectedPoint.frp,'MW')}</dd></div></dl><p className="observation-scope">Radiative power is not energy, burned area or fire severity. Marker size does not represent fire size.</p></section>}
      <details className="observation-limits"><summary>How these observations differ from the calendar</summary><p>This layer retains detections on calendar-excluded dates; totals differ from the local-date, outage-masked calendar. It uses UTC acquisition dates and separate observed VIIRS S-NPP records, with no harmonization or gap filling.</p><p>A hotspot marks the centre of a satellite pixel containing a thermal anomaly, not an exact ignition, a distinct fire, or burned area. VIIRS pixels are nominally 375 m; their reported scan and track dimensions vary. Multiple overpasses may detect the same fire.</p><p>Only presumed vegetation detections with nominal or high confidence are shown. Cloud and overpass coverage remain unknown. Scan and track describe footprint dimensions, not an exact north-aligned boundary.</p><p><a href="https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html" target="_blank" rel="noreferrer">NASA’s VIIRS field definitions</a>{sourceUrl&&/^https:\/\/[^/]*nasa\.gov\//.test(sourceUrl)&&<> · <a href={sourceUrl} target="_blank" rel="noreferrer">Original country archive</a></>}</p></details>
    </div>}
  </div>;
}
