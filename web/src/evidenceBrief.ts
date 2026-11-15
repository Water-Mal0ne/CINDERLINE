import type {Region, Week} from './types';
import {weekCoverage} from './calendarView';
import {fmt, geoCoordinate, numeric, sum} from './utils';
import type {MonthHistory} from './monthStats';

export interface EvidenceBriefInput {
  week: Week;
  region: Region;
  label: string;
  cellId: string;
  shareUrl: string | null;
  /** The current drawer's caveats, including any applicable spatial caveat. */
  caveats: readonly string[];
  /** Optional comparison of the month containing the week's first day with the same month in other years. */
  monthHistory?: MonthHistory | null;
}

/** Escape supplied prose as Markdown text, including within table cells. */
const text = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/\\/g, '\\\\').replace(/([`*_{}\[\]()#+!|~])/g, '\\$1').replace(/\r\n?|\n/g, ' ')
  .replace(/^(-|\d+\.)\s/, '\\$1 ');
const number = (value: unknown) => numeric(value) ? String(value) : 'Unavailable';
const display = (value: unknown, digits = 0) => numeric(value) ? fmt(value, digits) : 'Unavailable';
const unique = (values: string[], fallback: string) => [...new Set(values.filter(Boolean))].join('; ') || fallback;
const safeName = (value: string) => value.replace(/[^A-Za-z0-9._-]/g, '_').slice(0, 100) || 'unknown';

function publicLink(value: string): string | null {
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return null;
    // Angle brackets make parentheses in HTTP(S) URLs safe in Markdown links.
    return url.href.replace(/</g, '%3C').replace(/>/g, '%3E');
  } catch { return null; }
}

/** A portable rendering of existing evidence; it does not calculate new analyses. */
export function buildEvidenceBrief({week, region, label, cellId, shareUrl, caveats, monthHistory}: EvidenceBriefInput) {
  const days = weekCoverage(week, 'harmonized');
  const rawDays = weekCoverage(week, 'raw');
  const cell = region.cells.find(item => item.id === cellId);
  const scope = cellId === 'ALL' ? 'Whole region' : `Cell ${cellId}${cell ? ` · ${geoCoordinate(cell.lat, 'lat')}, ${geoCoordinate(cell.lon, 'lon')}` : ''}`;
  const models = unique(week.rows.map(row => row.model), region.meta.model || 'Not supplied');
  const sources = unique(week.rows.map(row => row.source), 'Not supplied');
  const coverage = unique(week.rows.map(row => row.coverage), 'Unknown');
  const recordPeriod = days.firstRecord && days.lastRecord ? `${days.firstRecord} to ${days.lastRecord}` : 'Unavailable';
  const fields = (values: string[]) => `| ${values.map(text).join(' | ')} |`;
  const lines = [
    '# FIRETRACE weekly evidence brief',
    '',
    `Data label: ${text(label)}`,
    '',
    '## Scope and period',
    '',
    `- Country / region: ${text(region.meta.name)} (${text(region.meta.region)})`,
    `- Spatial scope: ${text(scope)}`,
    `- Reference scale: ${text(region.meta.reference || 'Not supplied')}`,
    `- Calendar week: ${week.week}, ${week.year}`,
    `- Calendar period: ${days.start} to ${days.end}`,
    `- Records in this view: ${recordPeriod}`,
    `- Calendar records: ${days.recordDays} of ${days.expectedDays} calendar days`,
    `- Available raw days: ${rawDays.availableDays} of ${days.expectedDays} calendar days`,
    `- Available Aqua-reference-equivalent days: ${days.availableDays} of ${days.expectedDays} calendar days`,
    ...(days.partial ? ['', 'Partial week in this view. Totals include only these records.'] : []),
    '',
    '## Selected-week values',
    '',
    '| Quantity | Value |',
    '| --- | --- |',
    fields(['Raw baseline', display(week.raw, 1)]),
    fields(['Aqua-reference-equivalent activity', display(week.harmonized, 1)]),
    fields(['Terra observations', display(sum(week.rows.map(row => row.raw_terra)))]),
    fields(['Aqua observations', display(sum(week.rows.map(row => row.raw_aqua)))]),
    fields(['VIIRS observations', display(sum(week.rows.map(row => row.raw_viirs)))]),
    '',
    `Available daily estimates: ${week.rows.filter(row => numeric(row.harmonized)).length}`,
    '',
    '## How this estimate was made',
    '',
    `- Model: ${text(models)}`,
    `- Source: ${text(sources)}`,
    `- Coverage: ${text(coverage)}`,
    '',
    ...(monthHistory ? [
      '## Month vs history',
      '',
      'Historical comparison, not a forecast. The month containing the first day of this week is compared with the same month in the other fully observed years of this view (Aqua-reference-equivalent detections). Outage, partial and missing months are excluded.',
      '',
      '| Quantity | Value |',
      '| --- | --- |',
      fields(['Month', `${monthHistory.year}-${String(monthHistory.month).padStart(2, '0')}`]),
      fields(['Month total', display(monthHistory.value, 1)]),
      fields(['Median of the same month, other years', display(monthHistory.median, 1)]),
      fields(['10th-90th percentile, other years', numeric(monthHistory.p10) && numeric(monthHistory.p90) ? `${display(monthHistory.p10, 1)} to ${display(monthHistory.p90, 1)}` : 'Unavailable']),
      fields(['Other years compared', String(monthHistory.years)]),
      fields(['Comparison', monthHistory.relation]),
      '',
    ] : []),
    '## Caveats from the evidence card',
    '',
    ...caveats.flatMap(caveat => [text(caveat), '']),
    '## Daily records in this view',
    '',
    'Daily numbers retain their supplied precision. Unavailable values are not recorded zeros.',
    '',
    '| Date | Terra | Aqua | VIIRS | Raw baseline | Aqua-reference-equivalent activity | Calibration interval | Model | Source | Coverage |',
    '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |',
    ...week.rows.map(row => fields([
      row.date, number(row.raw_terra), number(row.raw_aqua), number(row.raw_viirs), number(row.raw), number(row.harmonized),
      /observed aqua/i.test(row.source) ? 'Not applicable' : numeric(row.lo) && numeric(row.hi) ? `${number(row.lo)}–${number(row.hi)}` : 'Not available',
      row.model || region.meta.model || 'Not supplied', row.source || 'Not supplied', row.coverage || 'Unknown',
    ])),
    ...(!week.rows.length ? ['', 'No daily records in this view.'] : []),
    '',
    '## Data sources',
    '',
  ];
  const links = region.meta.sources.flatMap(source => {
    const url = publicLink(source.url);
    return url ? [`- [${text(source.name)}](<${url}>)`] : [];
  });
  lines.push(...(links.length ? links : ['Not supplied.']), '', '## Share this view', '');
  const share = shareUrl ? publicLink(shareUrl) : null;
  lines.push(share ? `[Open this view](<${share}>)` : 'Share URL unavailable.', '');
  const location = cellId === 'ALL' ? 'whole-region' : `cell_${safeName(cellId)}`;
  return {
    filename: `FIRETRACE_${safeName(region.meta.region)}_${location}_${safeName(week.date)}_week-${week.week}_evidence.md`,
    content: lines.join('\n'),
  };
}
