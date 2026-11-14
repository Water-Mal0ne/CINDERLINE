import {ArrowRight, ScanLine, ShieldCheck} from 'lucide-react';
import {useMemo} from 'react';
import type {Week} from './types';
import {comparisonWeek,fmt,prettyDate} from './utils';

export default function ComparisonJourney({weeks,onInspect,onCompare,onValidate}:{weeks:Week[];onInspect:(week:Week)=>void;onCompare:()=>void;onValidate:()=>void}) {
  const example=useMemo(()=>comparisonWeek(weeks),[weeks]);
  return <section className="comparison-journey" aria-labelledby="journey-title">
    <div className="journey-heading"><div><span className="eyebrow">START WITH ONE OBSERVED WEEK</span><h2 id="journey-title">One landscape. Two instruments. Different counts.</h2></div><span className="journey-duration">A 60-SECOND EVIDENCE TRAIL</span></div>
    {example?<><p className="journey-context">Week {example.week.week}, {example.week.year} · starting {prettyDate(example.week.date)} · {example.paired.length} shared calendar days</p><div className="journey-values"><div><span>VIIRS OBSERVED</span><strong>{fmt(example.viirs)}</strong><small>Original detections</small></div><ArrowRight size={18}/><div><span>VIIRS CONVERTED</span><strong>{fmt(example.converted,1)}</strong><small>Aqua-reference-equivalent estimate</small></div><div className="journey-reference"><span>AQUA OBSERVED</span><strong>{fmt(example.aqua)}</strong><small>The reference, not ground truth</small></div></div><p className="journey-caveat">Illustrative highest-activity week among comparable days in this selection; not a performance test. These are the same dates, not guaranteed matching overpasses.</p></>:<p className="journey-context">This selection has no comparable converted-VIIRS and Aqua week. Earlier observed-Aqua records are shown directly, without a conversion.</p>}
    <div className="journey-actions"><button onClick={onCompare}><span>01</span> Compare the full record <ArrowRight size={13}/></button><button onClick={()=>example&&onInspect(example.week)} disabled={!example}><span>02</span> Inspect this week <ScanLine size={14}/></button><button onClick={onValidate}><span>03</span> Check held-out results <ShieldCheck size={14}/></button></div>
  </section>;
}
