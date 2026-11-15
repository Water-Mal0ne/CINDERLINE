import type {GlobeData} from './globeData';

export interface AlignmentCoverage {
  calendar_dates:number;
  excluded_dates:string[];
  retained_dates:number;
}
export interface CalendarAlignment {
  revision:'calendar-dates-v1';
  encoding:'indexed-deduction-dictionary-v1';
  years:number[];
  countries:string[];
  cell_count:number;
  source:{globe_sha256:string;globe_view_sha256:string;model_sha256:string;archive_manifest_fingerprint:string};
  coverage:Record<string,AlignmentCoverage>;
  deductions:number[];
  corrections:Record<string,[number,number][]>;
  coverage_note:string;
  area_monthly_note:string;
}
export type AlignedGlobeData=GlobeData & {calendar_alignment:CalendarAlignment};

const record=(value:unknown):value is Record<string,unknown>=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const finite=(value:unknown):value is number=>typeof value==='number'&&Number.isFinite(value);
const hex=(value:unknown)=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const same=(a:unknown,b:unknown)=>JSON.stringify(a)===JSON.stringify(b);
const yearDays=(year:number)=>(year%4===0&&year%100!==0)||year%400===0?366:365;

/** A mismatched correction file must never silently fall back to old annual totals. */
export function validCalendarAlignment(value:unknown,globe:GlobeData):value is CalendarAlignment {
  const original=globe as GlobeData & {archive_manifest_fingerprint?:unknown;calendar_alignment?:unknown};
  if(original.calendar_alignment||!record(value)||value.revision!=='calendar-dates-v1'||
    value.encoding!=='indexed-deduction-dictionary-v1'||!same(value.years,globe.years)||
    !same(value.countries,globe.coverage_regions.map(r=>r.id))||value.cell_count!==globe.cells.length||
    !record(value.source)||!hex(value.source.globe_sha256)||!hex(value.source.globe_view_sha256)||
    !hex(value.source.model_sha256)||value.source.archive_manifest_fingerprint!==original.archive_manifest_fingerprint||
    !hex(value.source.archive_manifest_fingerprint)||!record(value.coverage)||!record(value.corrections)||
    typeof value.coverage_note!=='string'||typeof value.area_monthly_note!=='string'||
    !Array.isArray(value.deductions)||!value.deductions.every(v=>finite(v)&&v>0))return false;
  if(!same(Object.keys(value.coverage).sort(),globe.years.map(String).sort()))return false;
  for(const year of globe.years){
    const c=value.coverage[String(year)];
    if(!record(c)||c.calendar_dates!==yearDays(year)||!Array.isArray(c.excluded_dates)||
      !c.excluded_dates.every(d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d)&&d.startsWith(`${year}-`)&&
        Number.isFinite(Date.parse(`${d}T00:00:00Z`))&&new Date(`${d}T00:00:00Z`).toISOString().slice(0,10)===d)||
      new Set(c.excluded_dates).size!==c.excluded_dates.length||c.retained_dates!==yearDays(year)-c.excluded_dates.length)return false;
  }
  for(const [year,rows] of Object.entries(value.corrections)){
    if(String(Number(year))!==year||!globe.years.includes(Number(year))||!Array.isArray(rows))return false;
    const coverage=value.coverage[year] as unknown as AlignmentCoverage;
    if(!coverage.excluded_dates.length)return false;
    const used=new Set<number>(),yi=globe.years.indexOf(Number(year));
    for(const row of rows){
      if(!Array.isArray(row)||row.length!==2||!row.every(Number.isSafeInteger))return false;
      const [ci,di]=row;
      if(ci<0||ci>=globe.cells.length||di<0||di>=value.deductions.length||used.has(ci))return false;
      used.add(ci);
      const annual=globe.cells[ci].values[yi],removed=value.deductions[di];
      if(!finite(annual)||!finite(removed)||removed>annual+1e-8)return false;
    }
  }
  return true;
}

/** The same IEEE-754 byte contract as the producer, independent of JSON spelling. */
export async function globeAlignmentIdentity(globe:GlobeData):Promise<string> {
  const source=globe as GlobeData & {archive_manifest_fingerprint?:string};
  if(typeof source.archive_manifest_fingerprint!=='string'||!globalThis.crypto?.subtle)throw new Error('Annual-source identity cannot be verified.');
  const encoder=new TextEncoder();
  const prefix=encoder.encode('calendar-alignment-v1\0'),manifest=encoder.encode(source.archive_manifest_fingerprint+'\0');
  const ids=globe.cells.map(cell=>encoder.encode(cell.id+'\0'));
  const size=prefix.length+4+globe.years.length*4+manifest.length+ids.reduce((n,id)=>n+id.length,0)+globe.cells.length*globe.years.length*9;
  const bytes=new Uint8Array(size),view=new DataView(bytes.buffer);
  let position=0;
  bytes.set(prefix,position);position+=prefix.length;
  view.setUint32(position,globe.years.length,true);position+=4;
  for(const year of globe.years){view.setUint32(position,year,true);position+=4;}
  bytes.set(manifest,position);position+=manifest.length;
  for(let i=0;i<globe.cells.length;i++){
    bytes.set(ids[i],position);position+=ids[i].length;
    const values=globe.cells[i].values;
    if(values.length!==globe.years.length)throw new Error('Annual series has an invalid length.');
    for(const value of values){
      if(value!==null&&(!finite(value)||value<0))throw new Error('Annual series has an invalid value.');
      view.setUint8(position,value===null?0:1);position++;
      view.setFloat64(position,value===null?0:value,true);position+=8;
    }
  }
  const digest=await crypto.subtle.digest('SHA-256',bytes);
  return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
}

/** Return a derived copy. Original cells, nulls and frozen source values survive. */
export async function applyCalendarAlignment<T extends GlobeData>(globe:T,payload:unknown):Promise<T & AlignedGlobeData> {
  if(!validCalendarAlignment(payload,globe))throw new Error('Annual calendar alignment is invalid or belongs to a different release.');
  if(await globeAlignmentIdentity(globe)!==payload.source.globe_view_sha256)throw new Error('Annual data changed; calendar alignment cannot be applied.');
  const cells=globe.cells.map(cell=>({...cell,values:[...cell.values]}));
  for(const [year,rows] of Object.entries(payload.corrections)){
    const yi=globe.years.indexOf(Number(year));
    for(const [ci,di] of rows)cells[ci].values[yi]=Math.max(0,(cells[ci].values[yi] as number)-payload.deductions[di]);
  }
  for(const year of globe.years){
    if(payload.coverage[String(year)].retained_dates===0){
      const yi=globe.years.indexOf(year);
      for(const cell of cells)cell.values[yi]=null;
    }
  }
  return {...globe,cells,calendar_alignment:payload};
}

/** Coverage counts are retained calendar dates, never claims of clear-sky coverage. */
export function annualCalendarCoverage(data:GlobeData,region:string,year:number):AlignmentCoverage|null {
  const aligned=data as Partial<AlignedGlobeData>;
  if(!data.coverage_regions.some(r=>r.id===region)||!data.years.includes(year))return null;
  return aligned.calendar_alignment?.coverage[String(year)]??null;
}
