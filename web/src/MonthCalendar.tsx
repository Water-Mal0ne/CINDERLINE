import {useEffect, useId, useMemo, useRef, useState} from 'react';
import type {KeyboardEvent} from 'react';
import {ArrowDownToLine, Star} from 'lucide-react';
import type {Daily} from './types';
import {binEdges, colorBin, HISTORY_NOTE, MONTH_NAMES, MONTHS, monthCalendarCSV, monthHistory, monthKey, monthMatrix, RAMP} from './monthStats';
import type {MonthCell, MonthMatrix, MonthMode} from './monthStats';
import {compact, fmt, numeric, saveFile} from './utils';
import './monthCalendar.css';

interface Props {rows?: Daily[]; matrix?: MonthMatrix; mode: MonthMode; label: string; regionId: string; regionName: string; scopeName: string; scopeId: string; fileScope?: string}

const unit = (mode: MonthMode) => mode === 'raw' ? 'raw baseline detections' : 'Aqua-reference-equivalent detections';
const statusText: Record<MonthCell['status'], string> = {
  ok: '', partial: 'partial month in the selected range', 'no-observation': 'no observation (satellite outage)', missing: 'no available estimate',
};

export default function MonthCalendar({rows, matrix: supplied, mode, label, regionId, regionName, scopeName, scopeId, fileScope}: Props) {
  const matrix = useMemo(() => supplied ?? monthMatrix(rows ?? [], mode), [supplied, rows, mode]);
  const captionId = useId(), monthId = useId(), yearId = useId();
  const defaultCell = useMemo(() => {const ordered=[...matrix.cells.values()].sort((a,b)=>b.key.localeCompare(a.key));return ordered.find(c=>c.status==='ok')??ordered[0]??null;}, [matrix]);
  const [picked, setPicked] = useState<{year: number; month: number} | null>(null);
  const [focusKey, setFocusKey] = useState('');
  const detailRef=useRef<HTMLElement>(null);
  useEffect(() => { setPicked(null); setFocusKey(''); }, [regionId, scopeId]);
  const year = picked && matrix.years.includes(picked.year) ? picked.year : defaultCell?.year ?? matrix.years[matrix.years.length - 1];
  const month = picked ? picked.month : defaultCell?.month ?? 1;
  const history = year ? monthHistory(matrix, year, month) : null;
  const edges = binEdges(matrix.max);
  const years = [...matrix.years].reverse();
  const pickedKey=year?monthKey(year,month):'';
  const activeKey = matrix.cells.has(focusKey) ? focusKey : matrix.cells.has(pickedKey)?pickedKey:defaultCell?.key??'';
  function choose(year:number,month:number,fromGrid=false){
    setPicked({year,month});setFocusKey(monthKey(year,month));
    if(fromGrid){detailRef.current?.focus({preventScroll:true});detailRef.current?.scrollIntoView({block:'nearest',behavior:'auto'});}
  }

  if (!matrix.years.length) return <p className="panel-description">No monthly records in this range.</p>;

  function move(event: KeyboardEvent<HTMLButtonElement>) {
    const step = ({ArrowLeft: -1, ArrowRight: 1, ArrowUp: -12, ArrowDown: 12} as Record<string, number>)[event.key];
    if (!step) return;
    event.preventDefault();
    const cells = Array.from(event.currentTarget.closest('table')?.querySelectorAll<HTMLTableCellElement>('tbody td') || []);
    let next = cells.indexOf(event.currentTarget.closest('td')!) + step;
    while (next >= 0 && next < cells.length) {
      const button=cells[next].querySelector<HTMLButtonElement>('button.month-cell');
      if(button&&!button.disabled){button.focus();break;}
      next+=step;
    }
  }
  function download() {
    const safe = regionId.replace(/[^A-Za-z0-9_-]/g, '_'), scope = fileScope ?? (scopeId === 'ALL' ? 'whole-region' : `cell_${scopeId.replace(/[^A-Za-z0-9._-]/g, '_')}`);
    saveFile(`CINDERLINE_${safe}_${scope}_month-calendar_${mode}.csv`, monthCalendarCSV(matrix, regionId, scopeName, label), 'text/csv;charset=utf-8');
  }

  const position = (value: number | null) => numeric(value) && matrix.max > 0 ? `${Math.min(100, value / matrix.max * 100)}%` : '0%';
  const span = history && numeric(history.p10) && numeric(history.p90) ? {left: position(history.p10), width: `calc(${position(history.p90)} - ${position(history.p10)})`} : null;

  return <div className="month-calendar">
    <div className="calendar-overview-label"><span>Rows are years. Select a month to compare it with other years.</span><div className="month-quick-legend" aria-label="Monthly activity colour scale"><span>Low</span>{RAMP.map(color=><i key={color} style={{backgroundColor:color}} aria-hidden="true"/>)}<span>High</span><i className="month-swatch no-observation" aria-hidden="true"/><span>Outage, not zero</span></div></div>
    <div className="month-calendar-columns">
    <div className="month-overview">
    <div className="month-highlights">
      <div><span>BUSIEST MONTH</span><strong>{matrix.busiestMonth ? `${MONTHS[matrix.busiestMonth.month - 1]} ${matrix.busiestMonth.year}` : '—'}</strong><small>{matrix.busiestMonth ? `${fmt(matrix.busiestMonth.value, 0)} ${unit(mode)}` : 'No fully observed month'}</small></div>
      <div><span>BUSIEST FULLY OBSERVED YEAR</span><strong>{matrix.busiestYear ? matrix.busiestYear.year : '—'}</strong><small>{matrix.busiestYear ? `${compact(matrix.busiestYear.total)} ${unit(mode)}; years with an outage month are not ranked` : 'No year with all 12 months observed'}</small></div>
    </div>
    <p className="month-caption" aria-hidden="true">Monthly {unit(mode)}, {regionName} · {scopeName}. Select a month to compare it with the same month in other years.</p>
    <div className="calendar-scroller calendar-overview-scroll" role="region" aria-label="Monthly fire activity calendar, scroll across months and down years" tabIndex={0}><table className="month-table" aria-labelledby={captionId}>
      <caption id={captionId} className="sr-only">Monthly {unit(mode)}, {regionName} · {scopeName}. Rows are years, columns are months. Select a month to compare it with the same month in other years.</caption>
      <thead><tr><th scope="col">Year</th>{MONTHS.map(m => <th scope="col" key={m}>{m}</th>)}</tr></thead>
      <tbody>{years.map(y => {
        const busiestYear = matrix.busiestYear?.year === y;
        return <tr key={y} className={busiestYear ? 'busiest-year' : ''}><th scope="row">{busiestYear && <Star size={9} aria-hidden="true"/>}{y}{busiestYear && <span className="sr-only"> (busiest fully observed year)</span>}</th>
          {MONTHS.map((m, i) => {
            const cell = matrix.cells.get(monthKey(y, i + 1));
            if (!cell) return <td key={m}><span className="month-cell empty" aria-label={`${m} ${y}: no records in this range`}/></td>;
            const known = numeric(cell.value);
            const busiest = matrix.busiestMonth?.key === cell.key, selected = y === year && i + 1 === month;
            const description = `${MONTH_NAMES[i]} ${y}: ${known ? `${fmt(cell.value, 0)} ${unit(mode)}` : statusText[cell.status]}${cell.status === 'partial' ? `, ${statusText.partial}` : ''}${busiest ? ', busiest month' : ''}`;
            return <td key={m}><button type="button" className={`month-cell ${cell.status} ${busiest ? 'busiest' : ''} ${selected ? 'selected' : ''}`}
              style={{backgroundColor: known && cell.status !== 'partial' ? RAMP[colorBin(cell.value as number, matrix.max)] : undefined}}
              aria-label={description} aria-pressed={selected} title={description} tabIndex={cell.key === activeKey ? 0 : -1}
              onFocus={() => setFocusKey(cell.key)} onKeyDown={move} onClick={() => choose(y,i+1,true)}>
              {busiest && <Star size={9} aria-hidden="true"/>}
            </button></td>;
          })}</tr>;
      })}</tbody>
    </table></div>
    <p className="calendar-scroll-help">Scroll down for earlier years. On a narrow screen, scroll across for later months.</p>
    <details className="calendar-legend-details"><summary>Colour values &amp; symbols</summary><div className="month-legend" aria-label="Colour legend">
      <span>{mode === 'raw' ? 'Raw baseline' : 'Aqua-reference-equivalent'} per month</span>
      <div className="month-ramp">{RAMP.map((color, i) => <span key={color}><i style={{backgroundColor: color}}/><small>{i === 0 ? '0' : `≥${compact(edges[i])}`}</small></span>)}</div>
      <span className="month-key"><i className="month-swatch no-observation"/>No observation (outage month, not zero)</span>
      <span className="month-key"><i className="month-swatch partial"/>Partial month in range</span>
      <span className="month-key"><Star size={9} aria-hidden="true"/>Busiest month / fully observed year</span>
    </div></details>

    </div>
    <div className="month-detail">
    <section className="month-history" aria-labelledby={`${captionId}-history`} tabIndex={-1} ref={detailRef}>
      <h3 id={`${captionId}-history`}>Month vs history</h3>
      <div className="month-history-controls">
        <label htmlFor={monthId}>Month<select id={monthId} value={month} onChange={e => choose(year ?? matrix.years[0],Number(e.target.value))}>{MONTH_NAMES.map((name, i) => <option key={name} value={i + 1}>{name}</option>)}</select></label>
        <label htmlFor={yearId}>Year<select id={yearId} value={year} onChange={e => choose(Number(e.target.value),month)}>{years.map(y => <option key={y} value={y}>{y}</option>)}</select></label>
      </div>
      {history && <div className="month-history-result" aria-live="polite">
        <dl>
          <div><dt>{MONTH_NAMES[month - 1]} {year}</dt><dd>{numeric(history.value) ? fmt(history.value, 0) : '—'}</dd></div>
          <div><dt>Median, other years</dt><dd>{fmt(history.median, 0)}</dd></div>
          <div><dt>10th–90th percentile</dt><dd>{numeric(history.p10) ? `${fmt(history.p10, 0)}–${fmt(history.p90, 0)}` : '—'}</dd></div>
          <div><dt>Years compared</dt><dd>{history.years}</dd></div>
        </dl>
        {span && <div className="month-range" aria-hidden="true"><span className="band" style={span}/><span className="median" style={{left: position(history.median)}}/>{numeric(history.value) && <span className="value" style={{left: position(history.value)}}/>}</div>}
        <p className="month-relation">{history.relation}</p>
        <details className="month-comparison-help"><summary>How this comparison works</summary><p className="chart-note">{HISTORY_NOTE}</p><p className="chart-note">Values are {unit(mode)}. Other years exclude outage, partial and missing months.</p><p className="chart-note">On the range bar: the dot marks the selected value, the line marks the median, and the band shows the 10th–90th percentile.</p></details>
      </div>}
    </section>
    <button type="button" className="button subtle" onClick={download}><ArrowDownToLine size={14}/> Download month calendar CSV</button>
    </div>
    </div>
  </div>;
}
