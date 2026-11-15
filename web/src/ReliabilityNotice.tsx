import {useMemo} from 'react';
import {ArrowUpRight, Info} from 'lucide-react';
import type {Daily, Evaluation} from './types';
import {includesUnevaluatedYears, nationalEvaluation, recordAvailability} from './reliability';
import type {ReliabilityScope} from './reliability';
import './reliability.css';

export interface ReliabilityNoticeProps {
  regionName: string;
  regionId?: string;
  cellId?: string;
  scope?: ReliabilityScope;
  model?: string;
  evaluations?: readonly Evaluation[];
  rows?: readonly Daily[];
  start?: string;
  end?: string;
  mode?: 'harmonized' | 'raw';
  showPeriodNote?: boolean;
  onValidation?: () => void;
}

const number = (value: number | null | undefined, digits = 1) => typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('en', {maximumFractionDigits: digits, minimumFractionDigits: digits}).format(value) : 'Unavailable';
const count = (value: number) => new Intl.NumberFormat('en').format(value);

export default function ReliabilityNotice({regionName, regionId, cellId = 'ALL', scope, model, evaluations = [], rows, start, end, mode = 'harmonized', showPeriodNote = true, onValidation}: ReliabilityNoticeProps) {
  const effectiveScope = scope ?? (cellId === 'ALL' ? 'national' : 'cell');
  const national = effectiveScope === 'national';
  const evaluation = useMemo(() => nationalEvaluation(evaluations, model, regionId), [evaluations, model, regionId]);
  const availability = useMemo(() => recordAvailability(rows, start, end, mode), [rows, start, end, mode]);
  const beyondTest = includesUnevaluatedYears(start, end);
  const title = national ? 'National comparison; observation coverage remains unknown' : 'Local accuracy is not established';
  return <aside className="reliability-notice" aria-label={`Interpretation and reliability for ${regionName}`}>
    <div className="reliability-heading"><Info size={16} aria-hidden="true"/><p><strong>{title}</strong>{!national && <span>{mode === 'raw' ? 'This raw baseline mixes instrument scales.' : 'Converted values use a national calibration; direct Aqua observations have no conversion step.'} Agreement for {regionName} as a whole does not establish local agreement.</span>}</p></div>
    {beyondTest && showPeriodNote && <p className="reliability-period">This selection includes dates after 2024. The published test covers 2020–2024; later dates have not been evaluated in that test.</p>}
    <details className="reliability-details">
      <summary>Read the evidence limits</summary>
      <div className="reliability-body">
        {mode === 'raw' ? <p>The raw baseline switches from Aqua to VIIRS. Its counts are not on a common instrument scale.</p> : <p>Values use Aqua’s detection scale, not the true number of fires. Direct Aqua observations have no conversion step.</p>}
        {national && evaluation && mode === 'harmonized' ? <div className="reliability-evaluation"><p><strong>{evaluation.model} · national weekly test, 2020–2024</strong><span>Agreement with archived Aqua, not ground truth. These are fixed test results, not recalculated for this selection.</span></p><dl>
          <div><dt>Mean absolute error</dt><dd>{number(evaluation.mae)} <small>detections/week</small></dd></div>
          <div><dt>Total-count bias</dt><dd>{number(evaluation.bias_pct)}{typeof evaluation.bias_pct === 'number' && Number.isFinite(evaluation.bias_pct) ? '%' : ''}</dd></div>
          <div><dt>Mean peak-week error</dt><dd>{number(evaluation.peak_week_error)} <small>weeks</small></dd></div>
        </dl><p>Peak-week error compares the single highest week in each year; it does not measure a shift of the entire season.</p></div> : <p>{!national ? 'National test metrics are not local error estimates. This view does not supply a validated error bound for the selected area.' : mode === 'raw' ? 'Selected-conversion metrics apply to the harmonized series, not this raw baseline. Open national evaluation to compare both.' : 'A uniquely matched national test result is not supplied for this selection.'}</p>}
        {availability.status === 'known' ? <div className="reliability-availability"><p><strong>{count(availability.availableDays)} available daily values{availability.expectedDays !== null ? ` / ${count(availability.expectedDays)} calendar days` : ''}</strong></p><p>{count(availability.unavailableDays)} recorded days have no usable value{availability.missingDays !== null ? `; ${count(availability.missingDays)} days have no record in this selection` : ''}. Recorded zero values are kept separate from unavailable values.</p>
          {(availability.invalidDateRows > 0 || availability.conflictingDays > 0) && <p>Malformed dates or conflicting duplicate dates were excluded from this availability summary; inspect the source records before interpreting the total.</p>}
          {availability.missingIntervalDays > 0 && <p>{count(availability.missingIntervalDays)} converted days have no valid calibration interval supplied.</p>}
        </div> : <p>{availability.status === 'invalid-range' ? 'Daily availability cannot be summarized for this date range.' : 'Daily availability is not supplied in this view; an annual or monthly total does not establish daily observation coverage.'}</p>}
        <p>Available values do not prove cloud-free observations. Conversion intervals describe variation in the fitted ratio; they omit cloud and overpass uncertainty, day-to-day conversion error and spatial model error.</p>
        {onValidation && <button type="button" className="reliability-link" onClick={onValidation}>Open national evaluation <ArrowUpRight size={13} aria-hidden="true"/></button>}
      </div>
    </details>
  </aside>;
}
