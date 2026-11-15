import {ArrowRight, ChevronLeft, ChevronRight} from 'lucide-react';
import {useMemo} from 'react';
import type {Index,Week} from './types';
import ComparisonJourney from './ComparisonJourney';
import {homeWeekSelection} from './homeWeek';
import {weekCoverage} from './calendarView';
import {fmt, numeric, prettyDate} from './utils';
import {MONTHS, monthKey, monthMatrix} from './monthStats';
import './introduction.css';

interface Props {
  weeks: Week[];
  context: string;
  loading: boolean;
  unavailable: boolean;
  countries: Index['regions'];
  country: string;
  onCountry: (id: string) => void;
  selectedDate?: string;
  onWeek: (date: string) => void;
  onExplore: (week?: Week) => void;
  onInspect: (week: Week) => void;
  onCompare: () => void;
  onValidate: () => void;
}

export default function HarmonizationIntro({weeks,context,loading,unavailable,countries,country,selectedDate,onWeek,onCountry,onExplore,onInspect,onCompare,onValidate}:Props) {
  const countryName=countries.find(item=>item.id===country)?.name||'the selected country';
  const selected=useMemo(()=>homeWeekSelection(weeks,selectedDate),[weeks,selectedDate]);
  const years=useMemo(()=>[...new Set(weeks.map(week=>week.year))].sort((a,b)=>b-a),[weeks]);
  const year=selected?.year??Number(selectedDate?.slice(0,4));
  const yearWeeks=weeks.filter(week=>week.year===year);
  const position=weeks.findIndex(week=>week===selected);
  const preview=useMemo(()=>monthMatrix(weeks.filter(week=>week.year===year).flatMap(week=>week.rows),'harmonized'),[weeks,year]);
  const max=preview.max;
  const hasYear=years.includes(year);
  const busy=loading||unavailable||!weeks.length;
  const weekLabel=(week:Week)=>`Week ${week.week} · ${prettyDate(week.date).replace(/,? \d{4}$/, '')} – ${prettyDate(weekCoverage(week,'harmonized').end).replace(/,? \d{4}$/, '')}`;
  function chooseYear(value:string){const candidates=weeks.filter(week=>week.year===Number(value));const next=candidates.find(week=>week.week===selected?.week)??candidates[0];if(next)onWeek(next.date);}
  return <div className="home-page">
    <header className="home-opening">
      <p className="home-kicker">Harmonizing MODIS &amp; VIIRS</p>
      <h1 id="workspace-title">Fire history, on a common scale.</h1>
      <div className="home-summary">
        <p>MODIS and VIIRS observe fire at different resolutions. Their hotspot counts cannot be compared directly. CINDERLINE converts VIIRS observations to the Aqua MODIS reference scale, creating a calendar for exploring historical burning activity.</p>
        <button className="home-explore" onClick={()=>onExplore(selected)}>Explore the calendar <ArrowRight size={18} aria-hidden="true"/></button>
      </div>
    </header>
    <section className="home-example" aria-labelledby="home-example-title">
      <div className="home-example-header">
        <h2 id="home-example-title">Harmonization, in numbers</h2>
        <div className="home-country"><label htmlFor="home-country">Country</label><select id="home-country" value={country} onChange={event=>onCountry(event.target.value)} disabled={loading||!countries.length}>{!countries.length&&<option value="">Loading countries…</option>}{countries.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></div>
      </div>
      <div className="home-week-picker" role="group" aria-label="Choose a calendar week">
        <div className="home-year"><label htmlFor="home-year">Year</label><select id="home-year" value={hasYear?year:''} disabled={busy} onChange={event=>chooseYear(event.target.value)}>{!hasYear&&<option value="">Choose year</option>}{years.map(value=><option key={value} value={value}>{value}</option>)}</select></div>
        <div className="home-week"><label htmlFor="home-week">Week</label><select id="home-week" value={selected?.date??''} disabled={busy||!yearWeeks.length} onChange={event=>onWeek(event.target.value)}>{!selected&&<option value="">Choose week</option>}{yearWeeks.map(week=><option key={week.key} value={week.date}>{weekLabel(week)}</option>)}</select></div>
        <div className="home-week-arrows"><button aria-label="Previous week" disabled={busy||position<=0} onClick={()=>onWeek(weeks[position-1].date)}><ChevronLeft size={18} aria-hidden="true"/></button><button aria-label="Next week" disabled={busy||position<0||position===weeks.length-1} onClick={()=>onWeek(weeks[position+1].date)}><ChevronRight size={18} aria-hidden="true"/></button></div>
        <span className="home-week-help">7-day bins, starting January 1</span>
      </div>
      <div className="home-example-body" aria-busy={loading}>
        {loading?<div className="home-example-state" role="status">Loading {countryName} observations…</div>:unavailable?<div className="home-example-state"><p>This example is unavailable. Retry loading above or choose another country.</p></div>:<>
          <p className="sr-only" role="status">{selected?`${countryName}, week ${selected.week}, ${selected.year} selected.`:'Choose a week available in this selection.'}</p>
          {selectedDate&&!selected&&<p className="home-selection-notice">The saved week is outside this selection. Choose a year and week above.</p>}
          {selected?.rows.some(row=>/beyond the validation period/i.test(row.source))&&<details className="validation-disclosure"><summary>2025: converted VIIRS, beyond the validation period.</summary><p>Harmonized values use the frozen model with no refitting; no calibration interval is shown for 2025, and seasonal statistics and anomaly flags still use 2003–2024.</p></details>}
          <ComparisonJourney weeks={weeks} context={context} introduction selectedWeek={selected} chosen={!!selectedDate} onInspect={onInspect} onCompare={onCompare} onValidate={onValidate}/>
        </>}
      </div>
    </section>
    {!busy&&selected&&<section className="home-calendar-preview" aria-labelledby="home-calendar-title">
      <div className="home-calendar-heading"><div><h2 id="home-calendar-title">One week is a starting point.</h2><p>See where it sits in {countryName}’s fire history. Open the calendar to compare years, explore an area, and inspect the observations.</p></div><button className="home-explore" onClick={()=>onExplore(selected)}>View this week in the calendar <ArrowRight size={18} aria-hidden="true"/></button></div>
      <figure className="home-month-preview"><figcaption>{year} · {context}<span>Aqua-reference-equivalent activity by month</span></figcaption>
        <ol className="home-months">{MONTHS.map((name,index)=>{const item=preview.cells.get(monthKey(year,index+1));const known=numeric(item?.value);const selectedMonth=Number(selected.date.slice(5,7))===index+1;return <li key={name} className={`${known?'':'is-missing'} ${selectedMonth?'is-selected':''}`}>
          <span className="home-month-name">{name}{selectedMonth&&<span className="sr-only">, selected week starts here</span>}</span>
          <span className="home-month-bar" aria-hidden="true"><i style={{height:known&&max?`${item!.value!/max*100}%`:'0%'}}/></span>
          <span className="home-month-value">{known?fmt(item!.value):'—'}</span><small>{item?.status==='partial'?'Partial':known?'':item?.status==='no-observation'?'Outage':'No data'}</small>
        </li>;})}</ol>
        <p className="home-preview-note">The outline marks where the selected week starts. Hatched months have no usable total. Historical context, not a forecast.</p>
      </figure>
    </section>}
  </div>;
}
