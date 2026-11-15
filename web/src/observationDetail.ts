/** Observed satellite records. Nothing here converts or interpolates detections. */
export const OBSERVATION_SCHEMA='observations-v1';
export const OBSERVATION_SENSOR='VIIRS S-NPP';
export const OBSERVATION_COLUMNS=['lat','lon','utc','confidence','scan','track','frp','daynight'] as const;
export type ObservationBounds=[west:number,south:number,east:number,north:number];
export type ObservationGridCell=[latIndex:number,lonIndex:number,count:number];
export interface ObservationFile {file:string;sha256:string;count:number}
export interface ObservationMonthRef extends ObservationFile {month:string}
export interface ObservationCountry {id:string;name:string;source:{url:string;sha256:string;rows:number};months:ObservationMonthRef[]}
export interface ObservationIndex {schema:typeof OBSERVATION_SCHEMA;sensor:typeof OBSERVATION_SENSOR;year:2024;time_basis:'UTC';grid_size:number;columns:string[];countries:ObservationCountry[]}
export interface ObservationTile extends ObservationFile {id:string;bounds:ObservationBounds}
export interface ObservationMonth {schema:typeof OBSERVATION_SCHEMA;sensor:typeof OBSERVATION_SENSOR;country:string;month:string;time_basis:'UTC';source_sha256:string;grid_size:number;count:number;grid:ObservationGridCell[];tiles:ObservationTile[]}
export interface ObservationPoint {id:string;lat:number;lon:number;utc:string;confidence:'n'|'h';scan:number|null;track:number|null;frp:number|null;daynight:'D'|'N'|'?'}
export interface ObservationLoadOptions {reload?:boolean;baseUrl?:string;fetcher?:typeof fetch}
const record=(v:unknown):v is Record<string,unknown>=>!!v&&typeof v==='object'&&!Array.isArray(v);
const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v);
const count=(v:unknown):v is number=>Number.isSafeInteger(v)&&Number(v)>=0;
const hash=(v:unknown):v is string=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const month=(v:unknown):v is string=>typeof v==='string'&&/^2024-(0[1-9]|1[0-2])$/.test(v);
const path=(v:unknown):v is string=>typeof v==='string'&&/^observations\/[A-Za-z0-9_\/-]+\.json$/.test(v)&&!v.includes('//');
const file=(v:unknown):v is ObservationFile=>record(v)&&path(v.file)&&hash(v.sha256)&&count(v.count);
const fail=()=>{throw new Error('The detailed observation data did not pass validation.');};
function requireActive(signal?:AbortSignal){if(signal?.aborted)throw new DOMException('Observation request cancelled.','AbortError');}
const sameColumns=(v:unknown)=>Array.isArray(v)&&v.length===OBSERVATION_COLUMNS.length&&v.every((c,i)=>c===OBSERVATION_COLUMNS[i]);
const header=(v:unknown):v is Record<string,unknown>=>record(v)&&v.schema===OBSERVATION_SCHEMA&&v.sensor===OBSERVATION_SENSOR;

export function decodeObservationIndex(value:unknown):ObservationIndex {
  if(!header(value)||value.year!==2024||value.time_basis!=='UTC'||value.grid_size!==.05||!sameColumns(value.columns)||!Array.isArray(value.countries)||!value.countries.length)return fail();
  const ids=new Set<string>();
  for(const country of value.countries){
    if(!record(country)||typeof country.id!=='string'||!country.id||ids.has(country.id)||typeof country.name!=='string'||!country.name||!record(country.source)||typeof country.source.url!=='string'||!country.source.url.startsWith('https://')||!hash(country.source.sha256)||!count(country.source.rows)||!Array.isArray(country.months)||!country.months.length)return fail();
    ids.add(country.id);const months=new Set<string>();
    for(const item of country.months){if(!file(item)||!record(item)||!month(item.month)||months.has(item.month))return fail();months.add(item.month);}
  }
  return value as unknown as ObservationIndex;
}

export function decodeObservationMonth(value:unknown,country:string,expected:ObservationMonthRef):ObservationMonth {
  if(!header(value)||value.country!==country||value.month!==expected.month||value.time_basis!=='UTC'||!hash(value.source_sha256)||value.grid_size!==.05||value.count!==expected.count||!Array.isArray(value.grid)||!Array.isArray(value.tiles))return fail();
  let gridCount=0,tileCount=0;const cells=new Set<string>(),tiles=new Set<string>(),paths=new Set<string>();
  for(const cell of value.grid){
    if(!Array.isArray(cell)||cell.length!==3||!Number.isSafeInteger(cell[0])||!Number.isSafeInteger(cell[1])||cell[0]<-1800||cell[0]>=1800||cell[1]<-3600||cell[1]>=3600||!count(cell[2])||cell[2]===0)return fail();
    const key=`${cell[0]}:${cell[1]}`;if(cells.has(key))return fail();cells.add(key);gridCount+=cell[2];
  }
  for(const tile of value.tiles){
    if(!file(tile)||!record(tile)||typeof tile.id!=='string'||!tile.id||tiles.has(tile.id)||paths.has(tile.file)||tile.count===0||tile.count>10000||!Array.isArray(tile.bounds)||tile.bounds.length!==4||!tile.bounds.every(finite))return fail();
    const [w,s,e,n]=tile.bounds as number[];if(w< -180||e>180||s< -90||n>90||w>=e||s>=n)return fail();
    tiles.add(tile.id);paths.add(tile.file);tileCount+=tile.count;
  }
  if(!Number.isSafeInteger(gridCount)||gridCount!==expected.count||tileCount!==expected.count)return fail();
  return value as unknown as ObservationMonth;
}

function timestamp(value:unknown,expectedMonth:string):value is string {
  if(typeof value!=='string'||!/^2024-\d{2}-\d{2}T\d{2}:\d{2}:00(?:\.000)?Z$/.test(value)||!value.startsWith(expectedMonth+'-'))return false;
  const date=new Date(value);return Number.isFinite(date.valueOf())&&date.toISOString()===value.replace(/:00Z$/,':00.000Z');
}
export function decodeObservationTile(value:unknown,context:Pick<ObservationMonth,'country'|'month'>,tile:ObservationTile):ObservationPoint[] {
  if(!header(value)||value.country!==context.country||value.month!==context.month||value.time_basis!=='UTC'||value.id!==tile.id||!sameColumns(value.columns)||!Array.isArray(value.rows)||value.rows.length!==tile.count||(value.count!==undefined&&value.count!==tile.count)||(value.bounds!==undefined&&JSON.stringify(value.bounds)!==JSON.stringify(tile.bounds)))return fail();
  return value.rows.map((row,index)=>{
    if(!Array.isArray(row)||row.length!==8)return fail();
    const [lat,lon,utc,confidence,scan,track,frp,daynight]=row;
    if(!finite(lat)||!finite(lon)||lat< -90||lat>90||lon< -180||lon>180||lat<tile.bounds[1]||lat>tile.bounds[3]||lon<tile.bounds[0]||lon>tile.bounds[2]||!timestamp(utc,context.month)||(confidence!=='n'&&confidence!=='h')||![scan,track].every(v=>v===null||finite(v)&&v>0)||!(frp===null||finite(frp)&&frp>=0)||!['D','N','?'].includes(daynight))return fail();
    return {id:`${context.country}:${context.month}:${tile.id}:${index}`,lat,lon,utc,confidence,scan,track,frp,daynight} as ObservationPoint;
  });
}

export function observationMonthLabel(value:string):string {
  if(!month(value))return '2024';
  return new Intl.DateTimeFormat('en',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(value+'-01T00:00:00Z'));
}
export function observationCountry(index:ObservationIndex|null,country:string){return index?.countries.find(c=>c.id===country)??null;}

async function fetchJson(fileName:string,sha256:string|undefined,signal:AbortSignal|undefined,options:ObservationLoadOptions):Promise<unknown>{
  if(!path(fileName))return fail();requireActive(signal);
  const response=await (options.fetcher??fetch)(`${options.baseUrl??'/data/'}${fileName}`,{signal,cache:options.reload?'reload':'default'});
  if(!response.ok)throw new Error('Detailed observations could not be downloaded.');
  const bytes=await response.arrayBuffer();requireActive(signal);
  if(sha256){
    const digest=await crypto.subtle.digest('SHA-256',bytes);
    const actual=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
    if(actual!==sha256)throw new Error('Detailed observations do not match their published source manifest.');
  }
  requireActive(signal);return JSON.parse(new TextDecoder().decode(bytes));
}
export async function loadObservationIndex(signal?:AbortSignal,options:ObservationLoadOptions={}):Promise<ObservationIndex>{return decodeObservationIndex(await fetchJson('observations/index.json',undefined,signal,options));}
export async function loadObservationMonth(index:ObservationIndex,country:string,selectedMonth:string,signal?:AbortSignal,options:ObservationLoadOptions={}):Promise<ObservationMonth>{
  const source=observationCountry(index,country),ref=source?.months.find(m=>m.month===selectedMonth);
  if(!ref)throw new Error('Detailed observations are not published for this country and month.');
  const data=decodeObservationMonth(await fetchJson(ref.file,ref.sha256,signal,options),country,ref);
  if(data.source_sha256!==source!.source.sha256)return fail();return data;
}
/** Two bounded downloads at a time; aborted selections can never publish a result. */
export async function loadObservationTiles(context:ObservationMonth,tiles:readonly ObservationTile[],signal?:AbortSignal,options:ObservationLoadOptions={}):Promise<ObservationPoint[]>{
  const approved=new Map(context.tiles.map(t=>[t.id,t])),seen=new Set<string>();
  for(const tile of tiles){const expected=approved.get(tile.id);if(!expected||expected.file!==tile.file||expected.sha256!==tile.sha256||expected.count!==tile.count||JSON.stringify(expected.bounds)!==JSON.stringify(tile.bounds)||seen.has(tile.id))return fail();seen.add(tile.id);}
  const results:ObservationPoint[][]=new Array(tiles.length);let next=0,failed=false;
  async function worker(){try{while(next<tiles.length&&!failed){requireActive(signal);const i=next++,tile=tiles[i];results[i]=decodeObservationTile(await fetchJson(tile.file,tile.sha256,signal,options),context,tile);}}catch(error){failed=true;throw error;}}
  await Promise.all(Array.from({length:Math.min(2,tiles.length)},worker));requireActive(signal);return results.flat();
}
