import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript');
const compiled=name=>ts.transpileModule(readFileSync(new URL(`../src/${name}.ts`,import.meta.url),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const moduleUrl=source=>'data:text/javascript;base64,'+Buffer.from(source).toString('base64');
const parserUrl=moduleUrl(compiled('explorationState'));
const parser=await import(parserUrl);
const api=await import(moduleUrl(compiled('explorationIntegration').replace("'./explorationState'",JSON.stringify(parserUrl))));
const utils=await import(moduleUrl(compiled('utils')));
const loader=await import(moduleUrl(compiled('loadData')));
const index=JSON.parse(readFileSync(new URL('../public/data/index.json',import.meta.url),'utf8'));
const regions=index.regions.map(entry=>loader.normalizePublishedData(JSON.parse(readFileSync(new URL(`../public/data/${entry.file}`,import.meta.url),'utf8'))));

test('index failures stay recoverable instead of publishing unusable render state',()=>{
  assert.equal(api.isPublishedIndex(index),true);
  assert.equal(api.isPublishedIndex({...index,regions:[]}),true);
  for(const malformed of [null,{}, {...index,regions:null}, {...index,regions:[null]},
    {...index,regions:[{id:'Nepal',name:'Nepal'}]}, {...index,limitations:null},
    {...index,limitations:[{}]}, {...index,label:{}},
    {...index,regions:[index.regions[0],index.regions[0]]}]){
    assert.equal(api.isPublishedIndex(malformed),false);
  }
});

test('published country catalogs expose only real detailed cells and actual record bounds',()=>{
  for(const region of regions){
    const catalog=api.catalogForRegion(region),available=catalog.regions[0];
    assert.equal(available.id,region.meta.region);
    assert.equal(available.start,region.meta.period_start.slice(0,10));
    assert.equal(available.end,region.meta.period_end.slice(0,10));
    assert.deepEqual(available.dailyCellIds,region.cells.map(cell=>cell.id));
    assert.deepEqual(catalog.globeCellIds,[]);
    assert.equal(catalog.dataVersion,undefined,'a generated-at timestamp is not an immutable data release');
  }
});

test('share and reopen preserve all supported App settings for each published country',()=>{
  for(const region of regions){
    const catalog=api.catalogForRegion(region),state={...parser.defaultExploration(catalog),start:'2020-03-05',end:'2020-12-31',cell:region.cells[0].id,view:'evidence',scale:'raw',globeYear:2020,evidenceWeek:'2020-03-04'};
    const shared=parser.createShareLink('https://firetrace.example/?token=unused#old',state,catalog);
    const target=parser.linkedRegion(new URL(shared.url).search,index.regions.map(r=>r.id),'Nepal');
    assert.equal(target,region.meta.region);
    const restored=api.resolveAppExploration(new URL(shared.url).search,catalog);
    assert.deepEqual(restored.state,state);assert.deepEqual(restored.notices,[]);
  }
});

test('unsupported annual selection and Earth/table preference are explained and stripped',()=>{
  const catalog=api.catalogForRegion(regions[0]);
  const restored=api.resolveAppExploration('?globeView=table&globeCell=Nepal%3A27.25%3A84.75',catalog);
  assert.equal(restored.state.globeView,'earth');assert.equal(restored.state.globeCell,null);
  assert.ok(restored.notices.some(n=>n.includes('Annual globe-cell selection')));
  assert.ok(restored.notices.some(n=>n.includes('Earth/table')));
  assert.equal(new URLSearchParams(restored.canonicalQuery).has('globeView'),false);
  assert.equal(new URLSearchParams(restored.canonicalQuery).has('globeCell'),false);
});

test('a partially visible linked week restores actual filtered daily rows',()=>{
  const region=regions[0],catalog=api.catalogForRegion(region);
  const restored=api.resolveAppExploration('?start=2020-03-05&end=2020-03-06&week=2020-03-04',catalog);
  const rows=region.daily.filter(r=>r.date>=restored.state.start&&r.date<=restored.state.end);
  const evidence=api.restoreEvidenceWeek(restored.state.evidenceWeek,utils.aggregateWeeks(rows));
  assert.equal(evidence.week.date,'2020-03-04');assert.equal(evidence.week.rows.length,2);
  assert.deepEqual(evidence.week.rows,rows);assert.equal(evidence.notice,null);
});

test('a valid week without loaded observations closes evidence without fabricating data',()=>{
  const result=api.restoreEvidenceWeek('2020-03-04',[]);
  assert.equal(result.week,null);assert.match(result.notice,/no observations/);
});

test('the year-end evidence bin restores even when only December 31 is visible',()=>{
  const rows=regions[0].daily.filter(r=>r.date==='2024-12-31');
  const evidence=api.restoreEvidenceWeek('2024-12-30',utils.aggregateWeeks(rows));
  assert.equal(evidence.week.week,53);assert.equal(evidence.week.rows.length,1);
});

test('in-progress or invalid edited date inputs cannot create a misleading share link',()=>{
  const catalog=api.catalogForRegion(regions[0]),state=parser.defaultExploration(catalog);
  assert.equal(api.canShareSelection(state,catalog),true);
  for(const patch of [{start:''},{end:'2024-02-30'},{start:'2025-01-01'},{start:'2023-01-01',end:'2020-01-01'},{end:'2099-12-31'},{cell:'unpublished'},{region:'unpublished'}])
    assert.equal(api.canShareSelection({...state,...patch},catalog),false,JSON.stringify(patch));
});

test('unknown country links reset dependent state before canonicalizing to the allow-listed fallback',()=>{
  const fallback=parser.linkedRegion('?region=Atlantis',index.regions.map(r=>r.id),'Nepal');
  const region=regions.find(r=>r.meta.region===fallback),catalog=api.catalogForRegion(region);
  const result=api.resolveAppExploration('?region=Atlantis&start=2020-01-01&cell=foreign&week=2020-01-01',catalog);
  assert.equal(result.state.region,fallback);assert.equal(result.state.start,region.meta.period_start);
  assert.equal(result.state.cell,'ALL');assert.equal(result.state.evidenceWeek,null);
  assert.ok(result.notices.length>0);
});
