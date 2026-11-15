import type {Daily, Week, Critical} from './types';

export const numeric = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
export const fmt = (value: unknown, digits = 0) => numeric(value) ? new Intl.NumberFormat('en', {maximumFractionDigits: digits}).format(value) : '—';
export const compact = (value: unknown) => numeric(value) ? new Intl.NumberFormat('en', {notation: 'compact', maximumFractionDigits: 1}).format(value) : '—';
export const sum = (values: unknown[]): number | null => {const nums = values.filter(numeric); return nums.length ? nums.reduce((a, b) => a + b, 0) : null;};
export const prettyDate = (date: string) => new Date(date.slice(0,10) + 'T12:00:00Z').toLocaleDateString('en', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'});

export function isoWeek(date: string) {
  const d = new Date(date.slice(0,10) + 'T00:00:00Z');
  const year = d.getUTCFullYear();
  // Matches pipeline/calendar.py: seven-day bins anchored on January 1.
  const week = Math.floor((d.getTime() - Date.UTC(year, 0, 1)) / 86400000 / 7) + 1;
  return {year, week};
}
export function weekStart(year: number, week: number) {
  const d = new Date(Math.min(Date.UTC(year, 0, 1 + (week-1)*7),Date.UTC(year+1,0,1)));
  return d.toISOString().slice(0,10);
}
export function aggregateWeeks(rows: Daily[]): Week[] {
  const map = new Map<string, Daily[]>();
  for (const row of rows) {const {year, week} = isoWeek(row.date); const key = `${year}-${week}`; const bucket=map.get(key); if(bucket)bucket.push(row);else map.set(key,[row]);}
  return [...map.entries()].map(([key, list]) => {
    const {year, week} = isoWeek(list[0].date);
    // A week containing a satellite-outage / no-data day is shown as no observation, not as low activity.
    const noObservation = list.some(d => d.source === 'no observation');
    return {key, year, week, date: weekStart(year, week), rows: list, raw: noObservation ? null : sum(list.map(d => d.raw)), harmonized: noObservation ? null : sum(list.map(d => d.harmonized))};
  }).sort((a, b) => a.date.localeCompare(b.date));
}
export function monthly(rows: Daily[]) {
  const map = new Map<string, Daily[]>();
  rows.forEach(row => {const key = row.date.slice(0,7);const bucket=map.get(key);if(bucket)bucket.push(row);else map.set(key,[row]);});
  return [...map.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([date, list]) => ({date, raw: sum(list.map(d => d.raw)), harmonized: sum(list.map(d => d.harmonized)), aqua: sum(list.map(d=>d.raw_aqua)), days:list.length, rawDays:list.filter(d=>numeric(d.raw)).length, harmonizedDays:list.filter(d=>numeric(d.harmonized)).length, aquaDays:list.filter(d=>numeric(d.raw_aqua)).length}));
}

/** An illustrative peak, never a model-performance selection. Same calendar days only. */
export function comparisonWeek(weeks: Week[]) {
  const candidates=weeks.map(week=>{
    const paired=week.rows.filter(d=>/converted.*viirs/i.test(d.source||'')&&numeric(d.raw_viirs)&&numeric(d.raw_aqua)&&numeric(d.harmonized));
    return {week,paired,viirs:sum(paired.map(d=>d.raw_viirs)),converted:sum(paired.map(d=>d.harmonized)),aqua:sum(paired.map(d=>d.raw_aqua))};
  }).filter(c=>c.paired.length>0);
  return candidates.sort((a,b)=>(b.converted??0)-(a.converted??0)||a.week.date.localeCompare(b.week.date))[0]||null;
}

export function sourcePeriods(rows: Daily[]) {
  const observed=rows.filter(d=>/observed aqua/i.test(d.source||'')).map(d=>d.date).sort();
  const converted=rows.filter(d=>/converted.*viirs/i.test(d.source||'')).map(d=>d.date).sort();
  return {observed:observed.length?{start:observed[0],end:observed[observed.length-1]}:null,converted:converted.length?{start:converted[0],end:converted[converted.length-1]}:null};
}

export function geoCoordinate(value:number,axis:'lat'|'lon') {
  return `${Math.abs(value).toFixed(1)}° ${axis==='lat'?(value<0?'S':'N'):(value<0?'W':'E')}`;
}
export function saveFile(filename: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const csvCell = (value: unknown) => '"' + String(value ?? '').replaceAll('"', '""') + '"';
export function exportCSV(rows: Daily[], region: string, label: string) {
  const columns: (keyof Daily)[] = ['date','cell_id','raw_terra','raw_aqua','raw_viirs','raw','harmonized','lo','hi','coverage','source','model'];
  const lines = [['data_label','region',...columns].map(csvCell).join(','), ...rows.map(r => [label, region, ...columns.map(k => r[k])].map(csvCell).join(','))];
  saveFile(`CINDERLINE_${region}.csv`, '\uFEFF' + lines.join('\r\n'), 'text/csv;charset=utf-8');
}
export function exportICS(periods: Critical[], year: number, region: string, label: string) {
  const escape = (s: string) => s.replaceAll('\\','\\\\').replaceAll('\n','\\n').replaceAll(';','\\;').replaceAll(',','\\,');
  const events = periods.map((p, i) => {
    const start = weekStart(year, p.start_week).replaceAll('-','');
    const end = weekStart(year, p.end_week + 1).replaceAll('-','');
    return ['BEGIN:VEVENT', `UID:firetrace-${region}-${year}-${i}@firetrace.local`, `DTSTAMP:${new Date().toISOString().replaceAll('-','').replaceAll(':','').split('.')[0]}Z`, `DTSTART;VALUE=DATE:${start}`, `DTEND;VALUE=DATE:${end}`, `SUMMARY:${escape(`${region}: historical high-activity period`)}`, `DESCRIPTION:${escape(`${label}. ${p.label}. Based on historical seasonal patterns; this is not a forecast or emergency alert.`)}`, 'END:VEVENT'].join('\r\n');
  });
  saveFile(`CINDERLINE_${region}_${year}.ics`, ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//CINDERLINE//Historical Fire Calendar//EN','CALSCALE:GREGORIAN',...events,'END:VCALENDAR'].join('\r\n'), 'text/calendar;charset=utf-8');
}
