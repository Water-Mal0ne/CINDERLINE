import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../package.json',import.meta.url));
const ts=require('typescript');
const compile=name=>ts.transpileModule(readFileSync(new URL('../src/'+name,import.meta.url),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const dataUrl=text=>'data:text/javascript;base64,'+Buffer.from(text).toString('base64');
const source=compile('calendarView.ts').replace("'./explorationState'",JSON.stringify(dataUrl(compile('explorationState.ts'))));
const {dateRangeError,weekCoverage}=await import(dataUrl(source));

test('manual date range rejects empty, reversed, impossible and out-of-record dates',()=>{
  const check=(start,end)=>dateRangeError(start,end,'2003-01-01','2024-12-31');
  assert.match(check('2024-01-01',''),/both/);
  assert.match(check('','2024-12-31'),/both/);
  assert.match(check('2024-04-31','2024-12-31'),/valid/);
  assert.match(check('2024-03-01','2024-02-29'),/on or before/);
  assert.match(check('2002-12-31','2024-12-31'),/published/);
  assert.match(check('2024-01-01','2025-01-01'),/published/);
  assert.equal(check('2003-01-01','2024-12-31'),null);
  assert.equal(check('2024-02-29','2024-02-29'),null);
});

test('partial filter counts calendar records separately from available estimates and zero',()=>{
  const coverage=weekCoverage({year:2020,week:40,date:'2020-09-30',rows:[
    {date:'2020-10-02',raw:0,harmonized:0},
    {date:'2020-10-03',raw:3,harmonized:null},
    {date:'2020-10-04',raw:4,harmonized:1.5}
  ]},'harmonized');
  assert.deepEqual(coverage,{start:'2020-09-30',end:'2020-10-06',firstRecord:'2020-10-02',lastRecord:'2020-10-04',expectedDays:7,recordDays:3,availableDays:2,partial:true});
});

test('year-end bins are complete at one or two days, never extrapolated to seven',()=>{
  for(const [year,dates] of [[2023,['2023-12-31']],[2024,['2024-12-30','2024-12-31']]]) {
    const coverage=weekCoverage({year,week:53,date:dates[0],rows:dates.map(date=>({date,raw:1,harmonized:1}))},'raw');
    assert.equal(coverage.end,`${year}-12-31`);
    assert.equal(coverage.expectedDays,dates.length);
    assert.equal(coverage.partial,false);
  }
});

test('missing estimates do not count as missing calendar records or recorded zero',()=>{
  const rows=Array.from({length:7},(_,i)=>({date:`2024-01-0${i+1}`,raw:0,harmonized:null}));
  const coverage=weekCoverage({year:2024,week:1,date:'2024-01-01',rows},'harmonized');
  assert.equal(coverage.recordDays,7);
  assert.equal(coverage.availableDays,0);
  assert.equal(coverage.partial,false);
  assert.equal(weekCoverage({year:2024,week:1,date:'2024-01-01',rows},'raw').availableDays,7);
});
