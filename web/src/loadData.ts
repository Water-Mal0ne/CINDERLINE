import type {Daily} from './types';
const cache=new Map<string,unknown>();
export async function loadData<T>(file:string,signal?:AbortSignal):Promise<T>{
  const key=`${import.meta.env.BASE_URL}data/${file}`;
  if(cache.has(key))return cache.get(key) as T;
  const response=await fetch(key,{signal});if(!response.ok)throw new Error('Processed data unavailable');
  const value=await response.json();cache.set(key,value);
  // Bound memory while keeping the last few region and cell views instantaneous.
  if(cache.size>18)cache.delete(cache.keys().next().value!);
  return value as T;
}
export function decodeCell(value:{daily?:Daily[];columns?:string[];rows?:unknown[][]}):Daily[]{
  if(Array.isArray(value.daily))return value.daily;
  if(Array.isArray(value.columns)&&Array.isArray(value.rows))return value.rows.map(row=>Object.fromEntries(value.columns!.map((key,i)=>[key,row[i]])) as unknown as Daily);
  throw new Error('Invalid cell data');
}
