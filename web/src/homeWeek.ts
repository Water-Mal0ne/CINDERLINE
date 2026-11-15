import type {Week} from './types';
import {comparisonWeek} from './utils';

/** Explicit choices never silently fall back to a different, busier week. */
export function homeWeekSelection(weeks: Week[], date?: string): Week | undefined {
  if (date) return weeks.find(week => week.date === date);
  return comparisonWeek(weeks.filter(week => !week.rows.some(row => row.source === 'no observation')))?.week ?? weeks[weeks.length - 1];
}
