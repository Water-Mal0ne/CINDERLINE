import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import ts from 'typescript';

if(!globalThis.crypto)globalThis.crypto=webcrypto;
const source=readFileSync(new URL('../src/calendarAlignment.ts',import.meta.url),'utf8');
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const {applyCalendarAlignment,annualCalendarCoverage,globeAlignmentIdentity,validCalendarAlignment}=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'));
const fingerprint='1'.repeat(64);
const fixture={years:[2023,2024],cell_size:.25,label:'fixture',reference:'Aqua',archive_manifest_fingerprint:fingerprint,
  coverage_regions:[{id:'A',name:'A'}],cells:[{id:'A:0:0',region:'A',lat:.125,lon:.125,values:[0,10]},{id:'A:1:1',region:'A',lat:1.125,lon:1.125,values:[null,5]}]};
const payload={revision:'calendar-dates-v1',encoding:'indexed-deduction-dictionary-v1',years:[2023,2024],countries:['A'],cell_count:2,
  source:{globe_sha256:fingerprint,globe_view_sha256:await globeAlignmentIdentity(fixture),model_sha256:fingerprint,archive_manifest_fingerprint:fingerprint},
  coverage:{2023:{calendar_dates:365,excluded_dates:[],retained_dates:365},2024:{calendar_dates:366,excluded_dates:['2024-07-09'],retained_dates:365}},
  deductions:[2],corrections:{2024:[[0,0]]},coverage_note:'Retained dates, not observed clear-sky days.',area_monthly_note:'Different month mask.'};

test('alignment preserves original values, nulls and zero, and marks retained dates',async()=>{
  const before=structuredClone(fixture);
  const aligned=await applyCalendarAlignment(fixture,payload);
  assert.deepEqual(fixture,before);
  assert.deepEqual(aligned.cells.map(c=>c.values),[[0,8],[null,5]]);
  assert.notEqual(aligned.cells[1].values,fixture.cells[1].values);
  assert.deepEqual(annualCalendarCoverage(aligned,'A',2024),payload.coverage[2024]);
  assert.equal(annualCalendarCoverage(aligned,'A',2025),null);
  assert.equal(annualCalendarCoverage(aligned,'missing',2024),null);
  assert.equal(annualCalendarCoverage(fixture,'A',2024),null);
  await assert.rejects(applyCalendarAlignment(aligned,payload),/invalid|different release/);
});

test('invalid references, duplicate corrections, negative deductions and bad date support fail closed',async()=>{
  const cases=[p=>p.corrections[2024].push([0,0]),p=>p.corrections[2024]=[[5,0]],p=>p.corrections[2024]=[[0,5]],
    p=>p.corrections['02024']=[[0,0]],p=>p.corrections['2024.0']=[[0,0]],
    p=>p.deductions=[-1],p=>p.deductions=[11],p=>p.corrections[2023]=[[1,0]],
    p=>p.coverage[2024].retained_dates=366,p=>p.coverage[2024].excluded_dates=['2024-02-30'],
    p=>p.coverage[2024].excluded_dates=['2024-07-09','2024-07-09'],p=>p.years=[2023,2025],
    p=>p.source.archive_manifest_fingerprint='2'.repeat(64),p=>p.countries=['B'],p=>p.cell_count=3];
  for(const change of cases){const bad=structuredClone(payload);change(bad);assert.equal(validCalendarAlignment(bad,fixture),false);await assert.rejects(applyCalendarAlignment(fixture,bad));}
});

test('same geometry but changed scientific values cannot receive a stale correction',async()=>{
  const changed=structuredClone(fixture);changed.cells[0].values[1]=11;
  await assert.rejects(applyCalendarAlignment(changed,payload),/Annual data changed/);
  const reordered=structuredClone(fixture);reordered.cells.reverse();
  await assert.rejects(applyCalendarAlignment(reordered,payload),/Annual data changed/);
});

test('a completely excluded year is unavailable, including cells previously recorded as zero',async()=>{
  const full=structuredClone(payload);
  full.coverage[2024].excluded_dates=Array.from({length:366},(_,i)=>new Date(Date.UTC(2024,0,1+i)).toISOString().slice(0,10));
  full.coverage[2024].retained_dates=0;
  const aligned=await applyCalendarAlignment(fixture,full);
  assert.deepEqual(aligned.cells.map(c=>c.values[1]),[null,null]);
});

const dataRoot=new URL('../public/data/',import.meta.url);
const actual=JSON.parse(readFileSync(new URL('globe.json',dataRoot),'utf8'));
const actualPayload=JSON.parse(readFileSync(new URL('calendar-alignment.json',dataRoot),'utf8'));
let actualAligned;
test('actual Python-generated source identity agrees with browser decoder and all-grid overlay',async()=>{
  assert.equal(await globeAlignmentIdentity(actual),actualPayload.source.globe_view_sha256);
  actualAligned=await applyCalendarAlignment(actual,actualPayload);
  let affected=0;
  for(let ci=0;ci<actual.cells.length;ci++)for(let yi=0;yi<actual.years.length;yi++){
    const old=actual.cells[ci].values[yi],value=actualAligned.cells[ci].values[yi];
    if(old!==value)affected++;
    if(old===null)assert.equal(value,null);else assert.ok(value>=0&&value<=old+1e-8);
  }
  assert.equal(affected,Object.values(actualPayload.corrections).reduce((n,r)=>n+r.length,0));
  assert.ok(affected>84,'all-grid derivation is not restricted to published daily cells');
});

function decode(payload){
  const t=payload.daily_compact??payload;
  return t.rows.map(r=>Object.fromEntries(t.columns.map((c,i)=>[c,t.dictionaries?.[c]?t.dictionaries[c][r[i]]:r[i]])));
}
test('actual 154 national and 1848 detailed cell annual sums agree with all available daily values',async()=>{
  const aligned=actualAligned??await applyCalendarAlignment(actual,actualPayload);
  const cells=new Map(aligned.cells.map(c=>[c.id,c]));
  let nationalChecks=0,cellChecks=0;
  const tolerance=366*.000005+1e-8;
  for(const region of aligned.coverage_regions){
    const country=JSON.parse(readFileSync(new URL(region.id+'.json',dataRoot),'utf8'));
    const sums=new Map(aligned.years.map(y=>[y,0]));
    for(const r of decode(country)){const y=Number(r.date.slice(0,4));if(r.cell_id==='ALL'&&sums.has(y)&&typeof r.harmonized==='number')sums.set(y,sums.get(y)+r.harmonized);}
    for(let yi=0;yi<aligned.years.length;yi++){
      const total=aligned.cells.filter(c=>c.region===region.id).reduce((s,c)=>s+(c.values[yi]??0),0);
      assert.ok(Math.abs(total-sums.get(aligned.years[yi]))<=tolerance,`${region.id}/${aligned.years[yi]}`);nationalChecks++;
    }
    for(const c of country.cells){
      const rows=decode(JSON.parse(readFileSync(new URL(c.file,dataRoot),'utf8')));
      const annual=new Map(aligned.years.map(y=>[y,0]));
      for(const r of rows){const y=Number(r.date.slice(0,4));if(annual.has(y)&&typeof r.harmonized==='number')annual.set(y,annual.get(y)+r.harmonized);}
      for(let yi=0;yi<aligned.years.length;yi++){
        assert.ok(Math.abs(cells.get(`${region.id}:${c.id}`).values[yi]-annual.get(aligned.years[yi]))<=tolerance,`${region.id}/${c.id}/${aligned.years[yi]}`);cellChecks++;
      }
    }
  }
  assert.equal(nationalChecks,154);assert.equal(cellChecks,1848);
});
