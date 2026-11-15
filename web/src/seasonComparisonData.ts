export type SeasonMask = 'primary' | 'padded';
export type SeasonKey = 'Aqua' | 'raw' | 'B1' | 'selected';
export const seasonKeys: SeasonKey[] = ['Aqua','raw','B1','selected'];
export interface SeasonFrame { year:number; months:number[][] }
export interface SeasonPayload {
  version:1; years:number[]; columns:string[]; mask_days:Record<SeasonMask,number>;
  countries:Record<string,{model:'B1'|'M1';masks:Record<SeasonMask,SeasonFrame[]>}>;
  provenance:{scope:string;checked_summary_values:number};
}
const obj=(v:unknown):v is Record<string,unknown>=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
export function validateSeasonPayload(value:unknown):SeasonPayload {
  if(!obj(value)||value.version!==1||JSON.stringify(value.years)!=='[2020,2021,2022,2023,2024]'||JSON.stringify(value.columns)!=='["retained_days","Aqua","raw","B1","selected"]'||!obj(value.countries)||!obj(value.mask_days)||value.mask_days.primary!==73||value.mask_days.padded!==87||!obj(value.provenance))throw new Error('Invalid seasonal comparison');
  if(!Object.keys(value.countries).length)throw new Error('Empty seasonal comparison');
  for(const country of Object.values(value.countries)){
    if(!obj(country)||!['B1','M1'].includes(String(country.model))||!obj(country.masks))throw new Error('Invalid seasonal country');
    for(const mask of ['primary','padded']){
      const frames=country.masks[mask];
      if(!Array.isArray(frames)||frames.length!==5)throw new Error('Missing seasonal years');
      frames.forEach((f,i)=>{
        if(!obj(f)||f.year!==2020+i||!Array.isArray(f.months)||f.months.length!==12)throw new Error('Invalid seasonal year');
        f.months.forEach((row,m)=>{if(!Array.isArray(row)||row.length!==5||!row.every(finite)||!Number.isInteger(row[0])||row[0]<1||row[0]>new Date(Date.UTC(2020+i,m+1,0)).getUTCDate())throw new Error('Invalid seasonal month');});
      });
    }
  }
  return value as unknown as SeasonPayload;
}
export interface SeasonSummary {counts:number[][];shares:(number|null)[][];total:number[];countError:(number|null)[];patternError:(number|null)[];retainedDays:number;years:number}
/** Equal-year means preserve the original study's estimand; no pooling of shares. */
export function summarizeSeason(frames:SeasonFrame[],year:number):SeasonSummary|null {
  const chosen=year===0?frames:frames.filter(f=>f.year===year);
  if(!chosen.length)return null;
  const totals=chosen.map(f=>seasonKeys.map((_,s)=>f.months.reduce((n,r)=>n+r[s+1],0)));
  const countError=seasonKeys.map((_,s)=>totals.every(t=>t[0]>0)?totals.reduce((n,t)=>n+Math.abs(t[s]-t[0])/t[0]*100,0)/chosen.length:null);
  const patternError=seasonKeys.map((_,s)=>totals.every(t=>t[0]>0&&t[s]>0)?chosen.reduce((n,f,i)=>n+50*f.months.reduce((v,r)=>v+Math.abs(r[1]/totals[i][0]-r[s+1]/totals[i][s]),0),0)/chosen.length:null);
  return {counts:seasonKeys.map((_,s)=>Array.from({length:12},(_,m)=>chosen.reduce((n,f)=>n+f.months[m][s+1],0)/chosen.length)),
    shares:seasonKeys.map((_,s)=>Array.from({length:12},(_,m)=>totals.every(t=>t[s]>0)?chosen.reduce((n,f,i)=>n+100*f.months[m][s+1]/totals[i][s],0)/chosen.length:null)),
    total:seasonKeys.map((_,s)=>totals.reduce((n,t)=>n+t[s],0)/chosen.length),countError,patternError,
    retainedDays:chosen.reduce((n,f)=>n+f.months.reduce((v,r)=>v+r[0],0),0)/chosen.length,years:chosen.length};
}
