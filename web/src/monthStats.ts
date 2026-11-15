import type {Daily, Nullable} from './types';
import {numeric} from './utils';

/** Month x year view of the published daily series. Pure display arithmetic: sums of existing daily values, no model. */
export type MonthMode = 'raw' | 'harmonized';
export type MonthStatus = 'ok' | 'partial' | 'no-observation' | 'missing';
export interface MonthCell {
  key: string; year: number; month: number; value: Nullable; status: MonthStatus;
  recordDays: number; availableDays: number; calendarDays: number;
}
export interface YearTotal {year: number; total: Nullable; complete: boolean}
export interface MonthMatrix {
  mode: MonthMode; years: number[]; cells: Map<string, MonthCell>; yearTotals: YearTotal[];
  busiestMonth: MonthCell | null; busiestYear: YearTotal | null; max: number;
}
export interface MonthHistory {
  year: number; month: number; value: Nullable; status: MonthStatus | 'absent';
  median: Nullable; p10: Nullable; p90: Nullable; years: number; relation: string;
}

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
/** Viridis, 7 steps: perceptually ordered and distinguishable with common colour-vision deficiencies. */
export const RAMP = ['#440154', '#443983', '#31688e', '#21918c', '#35b779', '#90d743', '#fde725'];
export const HISTORY_NOTE = 'Historical comparison, not a forecast: the selected month is set against the same month in the other years of this record.';

const daysIn = (year: number, month: number) => new Date(Date.UTC(year, month, 0)).getUTCDate();
export const monthKey = (year: number, month: number) => `${year}-${String(month).padStart(2, '0')}`;

/**
 * A month that contains a "no observation" day (documented satellite outage or all-country no-data day) is shown as
 * no observation, never as a low or zero value, matching the weekly calendar. A month whose records do not cover every
 * calendar day (date-range edge) is partial and is not used for highlights or historical comparison.
 */
export function monthMatrix(rows: Daily[], mode: MonthMode): MonthMatrix {
  const groups = new Map<string, Daily[]>();
  for (const row of rows) {
    const key = row.date.slice(0, 7);
    const list = groups.get(key);
    if (list) list.push(row); else groups.set(key, [row]);
  }
  const cells = new Map<string, MonthCell>();
  for (const [key, list] of groups) {
    const year = Number(key.slice(0, 4)), month = Number(key.slice(5, 7));
    const values = list.map(row => row[mode]).filter(numeric);
    const calendarDays = daysIn(year, month);
    const recordDays = new Set(list.map(row => row.date.slice(0, 10))).size;
    let status: MonthStatus = 'ok';
    if (list.some(row => row.source === 'no observation')) status = 'no-observation';
    else if (!values.length) status = 'missing';
    else if (recordDays < calendarDays) status = 'partial';
    const value = status === 'no-observation' || status === 'missing' ? null : values.reduce((a, b) => a + b, 0);
    cells.set(key, {key, year, month, value, status, recordDays, availableDays: values.length, calendarDays});
  }
  return finalize(cells, mode);
}

/** Build the matrix from monthly totals already summed elsewhere (area of interest). Index 0 = January of firstYear. */
export function monthMatrixFromMonthly(values: ArrayLike<number>, firstYear: number, outageMonths: readonly string[], mode: MonthMode): MonthMatrix {
  const outage = new Set(outageMonths), cells = new Map<string, MonthCell>();
  for (let i = 0; i < values.length; i++) {
    const year = firstYear + Math.floor(i / 12), month = i % 12 + 1, key = monthKey(year, month), calendarDays = daysIn(year, month);
    const blocked = outage.has(key);
    cells.set(key, {key, year, month, value: blocked ? null : values[i], status: blocked ? 'no-observation' : 'ok',
      recordDays: calendarDays, availableDays: blocked ? 0 : calendarDays, calendarDays});
  }
  return finalize(cells, mode);
}

function finalize(cells: Map<string, MonthCell>, mode: MonthMode): MonthMatrix {
  const years = [...new Set([...cells.values()].map(cell => cell.year))].sort((a, b) => a - b);
  const yearTotals = years.map(year => {
    const months = Array.from({length: 12}, (_, i) => cells.get(monthKey(year, i + 1)));
    const complete = months.every(cell => cell?.status === 'ok');
    const known = months.filter((cell): cell is MonthCell => !!cell && numeric(cell.value));
    return {year, complete, total: known.length ? known.reduce((a, cell) => a + (cell.value as number), 0) : null};
  });
  const full = [...cells.values()].filter(cell => cell.status === 'ok' && numeric(cell.value));
  const busiestMonth = full.reduce<MonthCell | null>((best, cell) => !best || (cell.value as number) > (best.value as number) ? cell : best, null);
  const busiestYear = yearTotals.filter(y => y.complete && numeric(y.total))
    .reduce<YearTotal | null>((best, y) => !best || (y.total as number) > (best.total as number) ? y : best, null);
  const max = Math.max(0, ...[...cells.values()].map(cell => cell.value).filter(numeric));
  return {mode, years, cells, yearTotals, busiestMonth, busiestYear, max};
}

/** Linear-interpolation percentile (the numpy default), q in [0, 1]. */
export function percentile(values: number[], q: number): Nullable {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const position = (sorted.length - 1) * q, low = Math.floor(position), high = Math.ceil(position);
  return sorted[low] + (sorted[high] - sorted[low]) * (position - low);
}

/** The selected month against the same calendar month in every OTHER fully observed year of the matrix. */
export function monthHistory(matrix: MonthMatrix, year: number, month: number): MonthHistory {
  const cell = matrix.cells.get(monthKey(year, month));
  const others = matrix.years.filter(y => y !== year).map(y => matrix.cells.get(monthKey(y, month)))
    .filter((c): c is MonthCell => !!c && c.status === 'ok' && numeric(c.value)).map(c => c.value as number);
  const median = percentile(others, .5), p10 = percentile(others, .1), p90 = percentile(others, .9);
  const value = cell?.status === 'ok' ? cell.value : null;
  let relation = 'No comparison available.';
  if (!cell) relation = 'No records for this month in the selected range.';
  else if (cell.status === 'no-observation') relation = 'No observation: this month contains a satellite outage, so it is not compared.';
  else if (cell.status === 'partial') relation = 'Partial month in the selected range, so it is not compared.';
  else if (cell.status === 'missing') relation = 'No available estimate for this month.';
  else if (others.length < 3) relation = 'Too few other fully observed years for a historical range.';
  else if (numeric(value) && numeric(p90) && value > p90) relation = 'Above the 10th–90th percentile range of the same month in other years.';
  else if (numeric(value) && numeric(p10) && value < p10) relation = 'Below the 10th–90th percentile range of the same month in other years.';
  else relation = 'Within the 10th–90th percentile range of the same month in other years.';
  return {year, month, value, status: cell?.status ?? 'absent', median, p10, p90, years: others.length, relation};
}

/** Colour bin 0-6 on a square-root scale of the matrix maximum, matching the weekly calendar's scaling. */
export function colorBin(value: number, max: number) {
  return max > 0 ? Math.min(RAMP.length - 1, Math.floor(Math.sqrt(Math.max(value, 0) / max) * (RAMP.length - 1))) : 0;
}
/** Lower edge of each colour bin, for the legend. */
export function binEdges(max: number) {
  return RAMP.map((_, i) => max * (i / (RAMP.length - 1)) ** 2);
}

const csvCell = (value: unknown) => '"' + String(value ?? '').replaceAll('"', '""') + '"';
const round = (value: Nullable) => numeric(value) ? Math.round(value * 1000) / 1000 : '';

/** Month calendar plus, for every month, its comparison with the same month in the other years. */
export function monthCalendarCSV(matrix: MonthMatrix, region: string, scope: string, label: string) {
  const scale = matrix.mode === 'raw' ? 'raw baseline detections' : 'Aqua-reference-equivalent detections';
  const header = ['data_label', 'region', 'spatial_scope', 'scale', 'year', 'month', 'value', 'status', 'record_days', 'available_days', 'calendar_days',
    'same_month_other_years_median', 'same_month_other_years_p10', 'same_month_other_years_p90', 'same_month_other_years_n', 'comparison',
    'busiest_month', 'busiest_fully_observed_year', 'note'];
  const lines = [header.map(csvCell).join(',')];
  for (const year of matrix.years) for (let month = 1; month <= 12; month++) {
    const cell = matrix.cells.get(monthKey(year, month));
    if (!cell) continue;
    const history = monthHistory(matrix, year, month);
    lines.push([label, region, scope, scale, year, month, round(cell.value), cell.status, cell.recordDays, cell.availableDays, cell.calendarDays,
      round(history.median), round(history.p10), round(history.p90), history.years, history.relation,
      matrix.busiestMonth?.key === cell.key ? 'yes' : '', matrix.busiestYear?.year === year ? 'yes' : '',
      'Historical comparison, not a forecast. No-observation months contain a documented satellite outage and are not zero.'].map(csvCell).join(','));
  }
  return '﻿' + lines.join('\r\n');
}
