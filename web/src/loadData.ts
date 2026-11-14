import type {Daily} from './types';
const cache=new Map<string,unknown>();
export async function loadData<T>(file:string,signal?:AbortSignal):Promise<T>{
  const key=`${import.meta.env.BASE_URL}data/${file}`;
  if(cache.has(key))return cache.get(key) as T;
  const response=await fetch(key,{signal});if(!response.ok)throw new Error('Processed data unavailable');
  const value=normalizePublishedData<T>(await response.json());cache.set(key,value);
  // Bound memory while keeping the last few region and cell views instantaneous.
  if(cache.size>18)cache.delete(cache.keys().next().value!);
  return value as T;
}
const record=(value:unknown):value is Record<string,unknown>=>value!==null&&typeof value==='object'&&!Array.isArray(value);
/** Decode lossless dictionary columns while retaining the older published formats. */
export function decodeCell(value:unknown):Daily[]{
  if(!record(value))throw new Error('Invalid cell data');
  if(value.encoding!==undefined&&value.encoding!=='column-dictionary-v1')throw new Error('Invalid cell encoding');
  if(Array.isArray(value.daily))return value.daily as Daily[];
  if(!Array.isArray(value.columns)||!Array.isArray(value.rows))throw new Error('Invalid cell data');
  const columns=value.columns;
  if(!columns.every(c=>typeof c==='string')||new Set(columns).size!==columns.length)throw new Error('Invalid cell columns');
  const dictionaries=value.dictionaries??{};
  if(!record(dictionaries)||Object.keys(dictionaries).some(key=>!columns.includes(key)||!Array.isArray(dictionaries[key])))throw new Error('Invalid cell dictionaries');
  if(Object.keys(dictionaries).length&&value.encoding!=='column-dictionary-v1')throw new Error('Invalid cell encoding');
  return value.rows.map(row=>{
    if(!Array.isArray(row)||row.length!==columns.length)throw new Error('Invalid cell row');
    return Object.fromEntries(columns.map((key,i)=>{
      if(!Object.prototype.hasOwnProperty.call(dictionaries,key))return [key,row[i]];
      const dictionary=dictionaries[key] as unknown[],index=row[i];
      if(!Number.isSafeInteger(index)||index<0||index>=dictionary.length)throw new Error('Invalid cell dictionary index');
      return [key,dictionary[index]];
    })) as unknown as Daily;
  });
}
/** National and cell series share a codec; the rest of the region contract is unchanged. */
export function normalizePublishedData<T>(value:unknown):T {
  if(record(value)&&Object.prototype.hasOwnProperty.call(value,'daily_compact')){
    if(value.daily!==undefined)throw new Error('Ambiguous daily data');
    const {daily_compact,...region}=value;
    return {...region,daily:decodeCell(daily_compact)} as T;
  }
  return value as T;
}
