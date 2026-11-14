import type {Week} from './types';
import {isCivilDate} from './explorationState';

/** Dates typed into native controls can still be empty or outside their min/max. */
export function dateRangeError(start:string,end:string,first:string,last:string):string|null {
  if(!isCivilDate(start)||!isCivilDate(end)) return 'Enter both a valid start date and end date.';
  if(start>end) return 'The start date must be on or before the end date.';
  if(start<first||end>last) return `Choose dates within the published record: ${first} to ${last}.`;
  return null;
}

/** Calendar bins start January 1; the last bin ends December 31, not in January. */
export function weekCoverage(week:Week,mode:'raw'|'harmonized') {
  const start=Date.parse(week.date+'T00:00:00Z');
  const end=Math.min(start+6*86_400_000,Date.UTC(week.year+1,0,1)-86_400_000);
  const dates=[...new Set(week.rows.map(row=>row.date.slice(0,10)))].sort();
  const available=new Set(week.rows.filter(row=>typeof row[mode]==='number'&&Number.isFinite(row[mode])).map(row=>row.date.slice(0,10)));
  const expectedDays=Math.round((end-start)/86_400_000)+1;
  return {start:week.date,end:new Date(end).toISOString().slice(0,10),firstRecord:dates[0],lastRecord:dates[dates.length-1],expectedDays,recordDays:dates.length,availableDays:available.size,partial:dates.length<expectedDays};
}
