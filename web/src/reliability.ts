import type {Daily, Evaluation} from './types';

export type ReliabilityScope = 'national' | 'cell' | 'area' | 'annual';
export const EVALUATION_END = '2024-12-31';
const DAY = 86_400_000;

function civilDay(value: string | undefined): number | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const time = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(time) && new Date(time).toISOString().slice(0, 10) === value ? time : null;
}

function finiteCount(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0;
}

/** The release names its chosen conversion in meta.model, e.g. "Aqua reference / M1". */
export function selectedConversion(model: string | undefined): 'B1' | 'M1' | null {
  const matches = new Set((model || '').match(/\b(?:B1|M1)\b/g));
  return matches.size === 1 ? [...matches][0] as 'B1' | 'M1' : null;
}

/** National test evidence must never be borrowed from a different country or candidate. */
export function nationalEvaluation(rows: readonly Evaluation[], model: string | undefined, regionId: string | undefined): Evaluation | null {
  const selected = selectedConversion(model);
  if (!selected || !regionId) return null;
  const matches = rows.filter(row => row.region === regionId && row.model === selected && row.split === 'test' && row.aggregation === 'weekly');
  return matches.length === 1 ? matches[0] : null;
}

export interface RecordAvailability {
  status: 'known' | 'not-supplied' | 'invalid-range';
  expectedDays: number | null;
  recordDays: number;
  availableDays: number;
  unavailableDays: number;
  missingDays: number | null;
  zeroDays: number;
  invalidDateRows: number;
  duplicateDays: number;
  conflictingDays: number;
  convertedDays: number;
  missingIntervalDays: number;
}

/** Counts published daily values, never clear-sky exposure. Duplicate dates cannot inflate coverage. */
export function recordAvailability(rows: readonly Daily[] | undefined, start?: string, end?: string, mode: 'harmonized' | 'raw' = 'harmonized'): RecordAvailability {
  const result: RecordAvailability = {status: 'not-supplied', expectedDays: null, recordDays: 0, availableDays: 0, unavailableDays: 0, missingDays: null, zeroDays: 0, invalidDateRows: 0, duplicateDays: 0, conflictingDays: 0, convertedDays: 0, missingIntervalDays: 0};
  const startTime = civilDay(start), endTime = civilDay(end);
  if ((start !== undefined && startTime === null) || (end !== undefined && endTime === null) || (startTime !== null && endTime !== null && startTime > endTime)) {
    return {...result, status: 'invalid-range'};
  }
  if (rows === undefined) return result;
  const byDay = new Map<number, Daily[]>();
  for (const row of rows) {
    const day = civilDay(row.date);
    if (day === null) { result.invalidDateRows++; continue; }
    if ((startTime !== null && day < startTime) || (endTime !== null && day > endTime)) continue;
    const values = byDay.get(day) || [];
    values.push(row);
    byDay.set(day, values);
  }
  const days = [...byDay.keys()].sort((a, b) => a - b);
  const first = startTime ?? days[0], last = endTime ?? days[days.length - 1];
  result.status = 'known';
  result.expectedDays = first === undefined || last === undefined ? null : Math.floor((last - first) / DAY) + 1;
  result.recordDays = days.length;
  result.missingDays = result.expectedDays === null ? null : Math.max(0, result.expectedDays - result.recordDays);
  for (const records of byDay.values()) {
    if (records.length > 1) result.duplicateDays++;
    const values = records.map(row => row[mode]);
    const comparable = values.every(finiteCount) && new Set(values).size === 1;
    if (!comparable) {
      result.unavailableDays++;
      if (records.length > 1 && new Set(values).size > 1) result.conflictingDays++;
      continue;
    }
    result.availableDays++;
    if (values[0] === 0) result.zeroDays++;
    const converted = records.filter(row => /converted|VIIRS/i.test(row.source) && !/observed Aqua/i.test(row.source));
    if (mode === 'harmonized' && converted.length) {
      result.convertedDays++;
      if (converted.some(row => !finiteCount(row.lo) || !finiteCount(row.hi) || row.lo > row.hi)) result.missingIntervalDays++;
    }
  }
  return result;
}

export function includesUnevaluatedYears(start?: string, end?: string): boolean {
  const limit = civilDay(EVALUATION_END)!;
  const first = civilDay(start), last = civilDay(end);
  if ((start !== undefined && first === null) || (end !== undefined && last === null) || (first !== null && last !== null && first > last)) return false;
  return (last ?? first ?? limit) > limit;
}
