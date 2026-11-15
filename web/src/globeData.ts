export interface GlobeCell {id:string;region:string;lat:number;lon:number;values:(number|null)[]}
export interface GlobeData {years:number[];cell_size:number;label:string;reference:string;coverage_regions:{id:string;name:string;sources?:string[]}[];cells:GlobeCell[]}

const record=(value:unknown):value is Record<string,unknown>=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const finite=(value:unknown):value is number=>typeof value==='number'&&Number.isFinite(value);

/** Validate render inputs without coercing, filling or recomputing any observations. */
export function validGlobeData(value:unknown):value is GlobeData {
  if(!record(value)||typeof value.label!=='string'||typeof value.reference!=='string'||
    !finite(value.cell_size)||value.cell_size<=0||value.cell_size>180||
    !Array.isArray(value.years)||!value.years.length||
    !value.years.every((year,i,years)=>Number.isSafeInteger(year)&&(i===0||year>years[i-1]))||
    !Array.isArray(value.coverage_regions)||!Array.isArray(value.cells))return false;
  const regions=new Set<string>();
  for(const region of value.coverage_regions){
    if(!record(region)||typeof region.id!=='string'||!region.id||regions.has(region.id)||typeof region.name!=='string'||
      (region.sources!==undefined&&(!Array.isArray(region.sources)||!region.sources.every(source=>typeof source==='string'))))return false;
    regions.add(region.id);
  }
  const ids=new Set<string>();
  for(const cell of value.cells){
    if(!record(cell)||typeof cell.id!=='string'||!cell.id||ids.has(cell.id)||
      typeof cell.region!=='string'||!regions.has(cell.region)||
      !finite(cell.lat)||Math.abs(cell.lat)>90||!finite(cell.lon)||Math.abs(cell.lon)>180||
      !Array.isArray(cell.values)||cell.values.length!==value.years.length||
      !cell.values.every(observation=>observation===null||finite(observation)))return false;
    ids.add(cell.id);
  }
  return true;
}
