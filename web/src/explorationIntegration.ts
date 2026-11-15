import {createShareLink, isCivilDate, resolveExploration} from './explorationState';
import type {ExplorationCatalog, ExplorationState} from './explorationState';
import type {Index, Region, Week} from './types';

/** Reject unusable catalogs before they replace the recoverable loading state. */
export function isPublishedIndex(value:unknown):value is Index {
  if(!value||typeof value!=='object')return false;
  const index=value as Partial<Index>;
  return typeof index.label==='string'&&typeof index.generated_at==='string'&&
    Array.isArray(index.limitations)&&index.limitations.every(note=>typeof note==='string')&&
    Array.isArray(index.regions)&&index.regions.every(region=>region&&
      typeof region.id==='string'&&region.id.length>0&&typeof region.name==='string'&&
      typeof region.file==='string'&&region.file.length>0)&&
    new Set(index.regions.map(region=>region.id)).size===index.regions.length;
}

/** Validate only against the country that was loaded from the published index. */
export function catalogForRegion(region: Region): ExplorationCatalog {
  const start=region.meta.period_start.slice(0,10),end=region.meta.period_end.slice(0,10);
  if(!isCivilDate(start)||!isCivilDate(end)||start>end) throw new Error('Invalid published region dates.');
  return {regions:[{id:region.meta.region,start,end,dailyCellIds:region.cells.map(c=>c.id),
    globeYears:Array.from({length:Number(end.slice(0,4))-Number(start.slice(0,4))+1},(_,i)=>Number(start.slice(0,4))+i)}],
    defaultRegionId:region.meta.region,globeCellIds:[]};
}

/** The annual globe selection and Earth/table display are not controlled by App. */
export function resolveAppExploration(search:string,catalog:ExplorationCatalog) {
  const result=resolveExploration(search,catalog);
  result.notices=result.notices.map(notice=>notice==='That annual grid cell is not published. The globe selection was cleared.'?'Annual globe-cell selection is not restored by this release. Use the globe to select a cell.':notice);
  if(result.state.globeView!=='earth') result.notices.push('The Earth/table display preference is not restored by this release.');
  result.state.globeView='earth';
  result.state.globeCell=null;
  const clean=createShareLink('https://firetrace.invalid/',result.state,catalog);
  return {...result,canonicalQuery:clean.canonicalQuery};
}

export function canShareSelection(state:ExplorationState,catalog:ExplorationCatalog):boolean {
  const region=catalog.regions.find(r=>r.id===state.region);
  return !!region&&isCivilDate(state.start)&&isCivilDate(state.end)&&state.start<=state.end&&
    state.start>=region.start&&state.end<=region.end&&
    (state.cell==='ALL'||region.dailyCellIds.includes(state.cell));
}

/** A syntactically valid week is still unavailable without actual loaded rows. */
export function restoreEvidenceWeek(date:string,weeks:Week[]):{week:Week|null;notice:string|null} {
  const week=weeks.find(w=>w.date===date&&w.rows.length>0)??null;
  return {week,notice:week?null:'The linked evidence week has no observations in this selection. Its panel was closed.'};
}
