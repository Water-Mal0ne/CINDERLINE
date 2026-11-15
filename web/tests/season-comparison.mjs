import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const source=readFileSync(new URL('../src/seasonComparisonData.ts',import.meta.url),'utf8');
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const {validateSeasonPayload,summarizeSeason}=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
const payload=JSON.parse(readFileSync(new URL('../public/data/season-comparison.json',import.meta.url),'utf8'));
const close=(a,b)=>assert.ok(Math.abs(a-b)<=1e-7*Math.max(1,Math.abs(b)),`${a} differs from ${b}`);

test('all country/mask five-year summaries reproduce independently verified study',()=>{
  validateSeasonPayload(payload);
  const [header,...lines]=readFileSync(new URL('../../reports/review/season/whole_year_comparison.csv',import.meta.url),'utf8').trim().split(/\r?\n/).map(line=>line.split(','));
  let checked=0;
  for(const fields of lines){
    const r=Object.fromEntries(header.map((key,i)=>[key,fields[i]]));
    if(r.mask==='unmasked')continue;
    const summary=summarizeSeason(payload.countries[r.country].masks[r.mask],0);
    const series={raw:1,B1:2,selected:3}[r.alternative];
    close(summary.countError[series],Number(r.mean_abs_annual_error)*100);
    close(summary.patternError[series],Number(r.mean_tv)*100);
    checked+=2;
  }
  assert.equal(checked,84);
});

test('yearly monthly shares sum to 100 and B1 preserves raw shape',()=>{
  for(const country of Object.values(payload.countries))for(const frames of Object.values(country.masks))for(const year of [0,...payload.years]){
    const s=summarizeSeason(frames,year);
    for(const shares of s.shares)close(shares.reduce((a,b)=>a+b,0),100);
    close(s.patternError[1],s.patternError[2]);
    if(country.model==='B1'){
      close(s.countError[2],s.countError[3]);close(s.patternError[2],s.patternError[3]);
    }
    close(s.patternError[0],0);close(s.countError[0],0);
  }
});

test('the five-year view averages yearly errors instead of hiding cancellation',()=>{
  const frames=[{year:2020,months:Array.from({length:12},()=>[28,1,2,2,2])},{year:2021,months:Array.from({length:12},()=>[28,1,0,0,0])}];
  const s=summarizeSeason(frames,0);
  close(s.total[0],s.total[1]);
  close(s.countError[1],100);
  assert.equal(s.patternError[1],null,'a zero-total year has undefined shape');
  assert.ok(s.shares[1].every(v=>v===null));
});

test('2025 and unavailable country-year data cannot leak into the research view',()=>{
  assert.equal(summarizeSeason(payload.countries.Nepal.masks.primary,2025),null);
  assert.equal(summarizeSeason([],0),null);
  const changed=structuredClone(payload);changed.years.push(2025);
  assert.throws(()=>validateSeasonPayload(changed));
});

test('malformed or incomplete month support is rejected rather than charted as zero',()=>{
  for(const mutate of [
    p=>p.countries.Nepal.masks.primary[0].months.splice(0,1),
    p=>p.countries.Nepal.masks.primary[0].months[0][0]=0,
    p=>p.countries.Nepal.masks.primary[0].months[0][1]=-1,
    p=>p.countries.Nepal.masks.primary[0].months[0][1]=NaN,
    p=>p.countries.Nepal.masks.primary[0].months[0][0]=32,
    p=>p.countries.Nepal.masks.primary[0].year=2025,
    p=>p.mask_days.padded=73,
    p=>p.countries={},
  ]){const changed=structuredClone(payload);mutate(changed);assert.throws(()=>validateSeasonPayload(changed));}
});
