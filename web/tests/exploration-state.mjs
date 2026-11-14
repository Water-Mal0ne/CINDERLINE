import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../package.json',import.meta.url));
const ts=require('typescript');
const source=readFileSync(new URL('../src/explorationState.ts',import.meta.url),'utf8');
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const api=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'));
const years=Array.from({length:22},(_,i)=>2003+i);
const catalog={regions:[
  {id:'Nepal',start:'2003-01-01',end:'2024-12-31',dailyCellIds:['27.25:84.75','28.25:81.50'],globeYears:years},
  {id:'United_States',start:'2003-01-01',end:'2024-12-31',dailyCellIds:['37.00:-120.50'],globeYears:years}
],defaultRegionId:'Nepal',globeCellIds:['Nepal:27.25:84.75','Nepal:28.25:81.50','United_States:37.00:-120.50'],dataVersion:'fixture-build-1'};

test('exact valid state round-trips through an HTTPS share link',()=>{
  const state={region:'United_States',start:'2020-03-01',end:'2020-12-31',cell:'37.00:-120.50',view:'evidence',scale:'raw',globeYear:2020,globeCell:'United_States:37.00:-120.50',globeView:'table',evidenceWeek:'2020-03-04'};
  const link=api.createShareLink('https://firetrace.example/app/',state,catalog);
  assert.equal(link.notices.length,0);
  const restored=api.resolveExploration(new URL(link.url).search,catalog);
  assert.deepEqual(restored.state,state);
  assert.equal(restored.canonicalQuery,link.canonicalQuery);
});
test('civil dates reject rollovers, locale forms and timestamps',()=>{
  assert.equal(api.isCivilDate('2024-02-29'),true);
  for(const date of ['2023-02-29','2024-04-31','2024-13-01','24-02-29','02/29/2024','2024-02-29T23:00:00Z','2024-2-29','0000-01-01']) assert.equal(api.isCivilDate(date),false,date);
  const r=api.resolveExploration('?start=2023-02-29&end=2024-04-31',catalog);
  assert.equal(r.state.start,'2003-01-01');assert.equal(r.state.end,'2024-12-31');assert.ok(r.notices.length);
});
test('unknown country does not silently carry its cell and date assumptions to Nepal',()=>{
  const r=api.resolveExploration('?region=Atlantis&start=2020-01-01&cell=27.25%3A84.75&globeCell=Nepal%3A27.25%3A84.75',catalog);
  assert.equal(r.state.region,'Nepal');assert.equal(r.state.start,'2003-01-01');assert.equal(r.state.cell,'ALL');assert.equal(r.state.globeCell,null);
  assert.match(r.notices[0],/not published/);
});
test('dates outside coverage clamp to actual published bounds',()=>{
  const r=api.resolveExploration('?start=1900-01-01&end=2099-12-31',catalog);
  assert.equal(r.state.start,'2003-01-01');assert.equal(r.state.end,'2024-12-31');assert.ok(r.notices.some(n=>n.includes('limited')));
});
test('reversed range restores full range instead of swapping user meaning',()=>{
  const r=api.resolveExploration('?start=2024-01-01&end=2020-12-31',catalog);
  assert.equal(r.state.start,'2003-01-01');assert.equal(r.state.end,'2024-12-31');assert.ok(r.notices.some(n=>n.includes('start date followed')));
});
test('daily cells are checked against the selected region',()=>{
  const r=api.resolveExploration('?region=United_States&cell=27.25%3A84.75',catalog);
  assert.equal(r.state.cell,'ALL');assert.ok(r.notices.some(n=>n.includes('daily grid cell')));
});
test('globe cells require exact published membership, not merely plausible coordinates',()=>{
  const missing=api.resolveExploration('?globeCell=Nepal%3A27.00%3A84.00',catalog);
  assert.equal(missing.state.globeCell,null);assert.ok(missing.notices.length);
  const foreign=api.resolveExploration('?globeCell=United_States%3A37.00%3A-120.50',catalog);
  assert.equal(foreign.state.globeCell,'United_States:37.00:-120.50');
});
test('calendar end year owns the globe year, preventing contradictory views',()=>{
  const r=api.resolveExploration('?start=2018-01-01&end=2020-12-31&globeYear=2024',catalog);
  assert.equal(r.state.globeYear,2020);assert.ok(r.notices.some(n=>n.includes('aligned')));
  const invalid=api.resolveExploration('?globeYear=2024.5',catalog);
  assert.equal(invalid.state.globeYear,2024);assert.ok(invalid.notices.length);
});
test('week uses January-1 bins, accepts partially visible week, rejects unrelated week',()=>{
  const valid=api.resolveExploration('?start=2020-03-05&end=2020-03-10&week=2020-03-04',catalog);
  assert.equal(valid.state.evidenceWeek,'2020-03-04');
  for(const week of ['2020-03-05','2020-01-01','2021-01-01','2020-02-30']){
    const r=api.resolveExploration('?start=2020-03-05&end=2020-03-10&week='+week,catalog);
    assert.equal(r.state.evidenceWeek,null,week);assert.ok(r.notices.length);
  }
});
test('year-end week53 remains a valid evidence selection despite excluded anomaly statistics',()=>{
  const r=api.resolveExploration('?start=2024-12-31&end=2024-12-31&week=2024-12-30',catalog);
  assert.equal(r.state.evidenceWeek,'2024-12-30');
});
test('unrecognized display settings recover with fixed safe messages',()=>{
  const r=api.resolveExploration('?view=%3Cscript%3E&scale=truefires&globeView=stereo',catalog);
  assert.equal(r.state.view,'explore');assert.equal(r.state.scale,'harmonized');assert.equal(r.state.globeView,'earth');
  assert.ok(r.notices.every(n=>!n.includes('<script>')));
});
test('duplicate state settings are not interpreted ambiguously',()=>{
  const r=api.resolveExploration('?region=Nepal&region=United_States&start=2020-01-01&start=2024-01-01',catalog);
  assert.equal(r.state.region,'Nepal');assert.equal(r.state.start,'2003-01-01');assert.ok(r.notices.some(n=>n.includes('repeated')));
});
test('version mismatch restores defaults and data-version mismatch stays explicit',()=>{
  const future=api.resolveExploration('?v=99&region=United_States&scale=raw',catalog);
  assert.deepEqual(future.state,api.defaultExploration(catalog));assert.match(future.notices[0],/unsupported format/);
  const old=api.resolveExploration('?v=1&data=old-build&start=2020-01-01',catalog);
  assert.equal(old.state.start,'2020-01-01');assert.ok(old.notices.some(n=>n.includes('values may differ')));
});
test('oversized query recovers without interpreting its state',()=>{
  const r=api.resolveExploration('?region=United_States&x='+'a'.repeat(2200),catalog);
  assert.deepEqual(r.state,api.defaultExploration(catalog));assert.ok(r.notices.some(n=>n.includes('too long')));
});
test('share links exclude unrelated params, fragments and accidental secrets',()=>{
  const state=api.defaultExploration(catalog);
  const r=api.createShareLink('https://firetrace.example/app/?token=private&redirect=https://elsewhere.example#secret',state,catalog);
  const url=new URL(r.url);
  assert.equal(url.origin,'https://firetrace.example');assert.equal(url.pathname,'/app/');assert.equal(url.hash,'');
  assert.equal(url.searchParams.has('token'),false);assert.equal(url.searchParams.has('redirect'),false);
  assert.ok(!r.url.includes('private'));assert.ok(!r.url.includes('secret'));
  assert.throws(()=>api.createShareLink('https://user:password@firetrace.example/',state,catalog),/credentials/);
  assert.throws(()=>api.createShareLink('javascript:alert(1)',state,catalog),/HTTP/);
});
test('region hint is small and only returns an allow-listed index ID',()=>{
  assert.equal(api.linkedRegion('?v=1&region=United_States',['Nepal','United_States'],'Nepal'),'United_States');
  assert.equal(api.linkedRegion('?region=https://example.org',['Nepal','United_States'],'Nepal'),'Nepal');
  assert.equal(api.linkedRegion('?region=Nepal&region=United_States',['Nepal','United_States'],'Nepal'),'Nepal');
  assert.equal(api.linkedRegion('?v=2&region=United_States',['Nepal','United_States'],'Nepal'),'Nepal');
  assert.equal(api.linkedRegion('?region=Nepal',[]),null);
});
test('unknown ordinary query parameters do not pretend to be exploration state',()=>{
  const r=api.resolveExploration('?utm_source=demo&secret=unused',catalog);
  assert.equal(r.hasSharedState,false);assert.equal(r.notices.length,0);
});
test('bad publisher catalog is a data error, not a fabricated default',()=>{
  assert.throws(()=>api.resolveExploration('',{...catalog,regions:[]}),/No published regions/);
  assert.throws(()=>api.resolveExploration('',{...catalog,regions:[{...catalog.regions[0],end:'2024-02-30'}]}),/Invalid/);
  assert.throws(()=>api.resolveExploration('',{...catalog,regions:[{...catalog.regions[0],globeYears:[]}]}),/supported years/);
});
