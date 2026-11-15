import {useEffect, useId, useMemo, useRef, useState} from 'react';
import {ArrowDown, ArrowUp, ArrowUpRight, ChevronDown, CircleHelp, ListFilter, MapPin} from 'lucide-react';
import type {Anomaly} from './types';
import {fmt, numeric, prettyDate} from './utils';
import './anomalies.css';

export type AnomalyFilter = 'all' | 'high' | 'low';
export type AnomalySort = 'latest' | 'oldest' | 'strongest';

export function anomalyDirection(anomaly: Anomaly): 'high' | 'low' | 'other' {
  const status = anomaly.status.toLowerCase();
  return status === 'high' || status === 'low' ? status : 'other';
}

export function selectAnomalies(anomalies: Anomaly[], filter: AnomalyFilter, sort: AnomalySort): Anomaly[] {
  const selected = anomalies.filter(a => filter === 'all' || anomalyDirection(a) === filter);
  return selected.sort((a, b) => {
    if (sort === 'strongest') {
      const aKnown = typeof a.z_score === 'number' && Number.isFinite(a.z_score);
      const bKnown = typeof b.z_score === 'number' && Number.isFinite(b.z_score);
      if (aKnown !== bKnown) return aKnown ? -1 : 1;
      if (aKnown && bKnown) {
        const difference = Math.abs(b.z_score!) - Math.abs(a.z_score!);
        if (difference !== 0) return difference;
      }
    }
    return sort === 'oldest' ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date);
  });
}

interface AnomalyPanelProps {
  anomalies: Anomaly[];
  cell: string;
  onSelect: (anomaly: Anomaly) => void;
  label: string;
}

export default function AnomalyPanel({anomalies, cell, onSelect, label}: AnomalyPanelProps) {
  const [filter, setFilter] = useState<AnomalyFilter>('all');
  const [sort, setSort] = useState<AnomalySort>('latest');
  const [limit, setLimit] = useState(8);
  const id = useId();
  const resultList = useRef<HTMLUListElement>(null);
  const pendingBatchFocus = useRef<{selection: string; index: number} | null>(null);
  const selected = useMemo(() => selectAnomalies(anomalies, filter, sort), [anomalies, filter, sort]);
  const selectionKey = selected.map(a => `${a.date}/${a.week}/${a.status}`).join('|');
  useEffect(() => setLimit(8), [selectionKey, filter, sort, cell]);
  useEffect(() => {
    const pending = pendingBatchFocus.current;
    if (!pending) return;
    pendingBatchFocus.current = null;
    if (pending.selection === selectionKey) resultList.current?.querySelectorAll<HTMLButtonElement>('button.ft-anomaly-result')[pending.index]?.focus();
  }, [limit, selectionKey]);
  const highCount = anomalies.filter(a => anomalyDirection(a) === 'high').length;
  const lowCount = anomalies.filter(a => anomalyDirection(a) === 'low').length;
  const visible = selected.slice(0, limit);
  const hasUnknownZ = selected.some(a => !numeric(a.z_score));

  return <section className="panel ft-anomalies" aria-labelledby={`${id}-heading`}>
    <div className="panel-heading">
      <div><span className="eyebrow">04 / LOOK CLOSER</span><h2 id={`${id}-heading`}>Unusual observations</h2></div>
      {cell === 'ALL' && <span className="count-badge">{fmt(anomalies.length)} flagged weeks in range</span>}
    </div>
    {cell !== 'ALL' ? <div className="ft-anomaly-empty ft-anomaly-scope">
      <MapPin size={25} aria-hidden="true"/>
      <div><h3>This comparison is for the whole region.</h3><p>Select “Whole region” in Spatial scope to inspect regional anomalies. A regional flag is not a finding about cell {cell}.</p></div>
    </div> : <>
      <p className="ft-anomaly-intro">Find complete weeks above or below their historical 10th–90th percentile range. Each comparison excludes its own year. These are observations to inspect, not fire warnings.</p>
      <div className="ft-anomaly-controls">
        <div className="ft-anomaly-filters" role="group" aria-label="Filter unusual observations">
          {([['all', 'All', anomalies.length], ['high', 'Higher activity', highCount], ['low', 'Lower activity', lowCount]] as const).map(([value, title, count]) =>
            <button type="button" key={value} aria-pressed={filter === value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>
              {value === 'high' ? <ArrowUp size={13} aria-hidden="true"/> : value === 'low' ? <ArrowDown size={13} aria-hidden="true"/> : <ListFilter size={13} aria-hidden="true"/>}
              <span>{title}</span><span className="ft-anomaly-filter-count" aria-label={`${count} weeks`}>{fmt(count)}</span>
            </button>)}
        </div>
        <label className="ft-anomaly-sort" htmlFor={`${id}-sort`}><span>Sort</span>
          <select id={`${id}-sort`} aria-label="Sort unusual observations" value={sort} onChange={event => setSort(event.target.value as AnomalySort)}>
            <option value="latest">Newest first</option><option value="oldest">Oldest first</option><option value="strongest">Largest |z-score|</option>
          </select><ChevronDown size={13} aria-hidden="true"/>
        </label>
      </div>
      <p className="ft-anomaly-result-count" role="status" aria-live="polite" aria-atomic="true">{selected.length ? `Showing ${Math.min(limit, selected.length)} of ${fmt(selected.length)} ${filter === 'all' ? 'flagged' : filter === 'high' ? 'higher-activity' : 'lower-activity'} weeks.` : `No ${filter === 'all' ? 'flagged' : filter === 'high' ? 'higher-activity' : 'lower-activity'} weeks in this selection.`}</p>
      {visible.length ? <ul className="ft-anomaly-results" ref={resultList}>{visible.map(anomaly => {
        const direction = anomalyDirection(anomaly);
        const directionText = direction === 'high' ? 'Higher than historical range' : direction === 'low' ? 'Lower than historical range' : 'Flagged observation';
        const signedZ = numeric(anomaly.z_score) ? `${anomaly.z_score >= 0 ? '+' : ''}${fmt(anomaly.z_score, 2)}` : null;
        return <li key={`${anomaly.date}-${anomaly.week}-${anomaly.status}`}>
          <button type="button" className={`ft-anomaly-result ${direction}`} onClick={() => onSelect(anomaly)} aria-label={`${directionText}, week ${anomaly.week}, starting ${prettyDate(anomaly.date)}. ${fmt(anomaly.value, 1)} Aqua-reference-equivalent detections. Open weekly evidence.`}>
            <span className="ft-anomaly-direction" aria-hidden="true">{direction === 'low' ? <ArrowDown size={19}/> : <ArrowUp size={19}/>}</span>
            <span className="ft-anomaly-date"><strong>{prettyDate(anomaly.date)}</strong><small>Week {String(anomaly.week).padStart(2, '0')} · {directionText}</small></span>
            <span className="ft-anomaly-value"><strong>{fmt(anomaly.value, 1)}</strong><small>{signedZ !== null ? `z ${signedZ}` : 'z unavailable'}</small></span>
            <ArrowUpRight className="ft-anomaly-open" size={17} aria-hidden="true"/>
          </button>
        </li>;
      })}</ul> : <div className="ft-anomaly-empty"><CircleHelp size={25} aria-hidden="true"/><div><h3>{anomalies.length ? 'No weeks match this filter.' : 'No flagged weeks in the selected dates.'}</h3><p>Missing or incomplete records cannot establish normal conditions. The one- or two-day year-end bin is excluded from weekly anomaly comparisons.</p></div></div>}
      {selected.length > limit && <button type="button" className="button subtle ft-anomaly-more" onClick={() => {pendingBatchFocus.current = {selection: selectionKey, index: visible.length};setLimit(current => current + 8);}}><ChevronDown size={15} aria-hidden="true"/> Show {Math.min(8, selected.length - limit)} more weeks</button>}
      <div className="ft-anomaly-explainer"><CircleHelp size={14} aria-hidden="true"/><p>Values are weekly Aqua-reference-equivalent detections, not distinct fires. {sort === 'strongest' ? 'Largest |z-score| ranks standardized deviations, not hazard severity. ' : ''}{hasUnknownZ ? 'Unavailable z-scores stay last in that sort and are never treated as zero; a reference with no variation can still produce a percentile flag. ' : ''}Cloud and overpass coverage remain unknown.</p></div>
    </>}
    <span className="chart-label">{label}</span>
  </section>;
}
