import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const source=readFileSync(new URL('../src/globeCells.ts',import.meta.url),'utf8');
const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const {filterGlobeTableCells,globeTablePage,localGlobeCellId,visibleGlobeCells}=await import('data:text/javascript;base64,'+Buffer.from(output).toString('base64'));
const globe=JSON.parse(readFileSync(new URL('../public/data/globe.json',import.meta.url),'utf8'));
const yearIndex=globe.years.indexOf(2024);
assert.ok(yearIndex>=0);
const pair=globe.cells.filter(c=>c.lat===23.125&&c.lon===92.375);

test('actual Bangladesh/India border square follows selected country without summation',()=>{
  assert.deepEqual(pair.map(c=>c.region).sort(),['Bangladesh','India']);
  for(const region of ['Bangladesh','India']){
    const expected=pair.find(c=>c.region===region);
    for(const input of [pair,[...pair].reverse()]){
      const visible=visibleGlobeCells(input,yearIndex,region);
      assert.equal(visible.length,1);
      assert.equal(visible[0],expected);
      assert.equal(visible[0].values[yearIndex],expected.values[yearIndex]);
    }
  }
});

test('foreign border fallback uses stable country ordering regardless of input order',()=>{
  assert.equal(visibleGlobeCells(pair,yearIndex,'Australia')[0].region,'Bangladesh');
  assert.equal(visibleGlobeCells([...pair].reverse(),yearIndex,'Australia')[0].region,'Bangladesh');
});

test('all published annual geometry has unique centers and retains original records',()=>{
  const original=new Set(globe.cells);
  const duplicateCount=globe.cells.length-new Set(globe.cells.map(c=>`${c.lat}:${c.lon}`)).size;
  assert.equal(duplicateCount,130,'current seven-country overlap inventory');
  for(const region of globe.coverage_regions.map(r=>r.id)){
    const visible=visibleGlobeCells(globe.cells,yearIndex,region);
    assert.equal(new Set(visible.map(c=>`${c.lat}:${c.lon}`)).size,visible.length);
    assert.ok(visible.every(c=>original.has(c)),'no new combined or fabricated records');
  }
});

test('selected-country unknown stays unknown and recorded zero stays visible',()=>{
  const foreign={id:'A:0:0',region:'A',lat:0.125,lon:0.125,values:[9,9,9]};
  const selected={id:'B:0:0',region:'B',lat:0.125,lon:0.125,values:[null,0,NaN]};
  const cells=Object.freeze([Object.freeze(foreign),Object.freeze(selected)]);
  assert.deepEqual(visibleGlobeCells(cells,0,'B'),[]);
  assert.deepEqual(visibleGlobeCells(cells,1,'B'),[selected]);
  assert.deepEqual(visibleGlobeCells(cells,2,'B'),[]);
  assert.deepEqual(visibleGlobeCells(cells,3,'B'),[]);
  assert.deepEqual(visibleGlobeCells(cells,0,'A'),[foreign]);
});

test('annual table pagination reaches every country record without hiding cells after the top 20',()=>{
  for(const region of globe.coverage_regions.map(r=>r.id)){
    const rows=filterGlobeTableCells(globe.cells,yearIndex,region,[]);
    const expected=globe.cells.filter(c=>c.region===region&&Number.isFinite(c.values[yearIndex]));
    assert.equal(rows.length,expected.length);
    assert.ok(rows.length>20);
    assert.ok(rows.every((c,index)=>index===0||rows[index-1].values[yearIndex]>=c.values[yearIndex]));
    const collected=[];
    for(let page=0;page<globeTablePage(rows,0).pages;page++)collected.push(...globeTablePage(rows,page).rows);
    assert.deepEqual(collected,rows);
    assert.equal(new Set(collected.map(c=>c.id)).size,expected.length);
    assert.equal(globeTablePage(rows,99999).last,rows.length,'stale page clamps to final page');
  }
});

test('daily-record filter uses the actual available cell IDs in all seven countries',()=>{
  for(const region of globe.coverage_regions.map(r=>r.id)){
    const country=JSON.parse(readFileSync(new URL(`../public/data/${region}.json`,import.meta.url),'utf8'));
    const ids=country.cells.map(cell=>cell.id);
    const rows=filterGlobeTableCells(globe.cells,yearIndex,region,ids,true);
    assert.equal(ids.length,12);
    assert.deepEqual(rows.map(localGlobeCellId).sort(),[...ids].sort());
    assert.ok(rows.every(c=>c.region===region),'no foreign country reuses a local ID');
  }
});

test('grid search accepts exact signed centers and compass coordinates without losing zero',()=>{
  const south={id:'A:-23.25:-50.25',region:'A',lat:-23.125,lon:-50.125,values:[0,null]};
  const north={id:'A:23:50',region:'A',lat:23.125,lon:50.125,values:[10,5]};
  const missing={id:'A:0:0',region:'A',lat:0.125,lon:0.125,values:[null,0]};
  const cells=Object.freeze([Object.freeze(south),Object.freeze(north),Object.freeze(missing)]);
  assert.deepEqual(filterGlobeTableCells(cells,0,'A',[],false,' -23.125, -50.125 '),[south]);
  assert.deepEqual(filterGlobeTableCells(cells,0,'A',[],false,'23.125° S / 50.125° W'),[south]);
  assert.deepEqual(filterGlobeTableCells(cells,0,'A',[],false,'23.125 N, 50.125 E'),[north]);
  assert.deepEqual(filterGlobeTableCells(cells,0,'A',[],false,'23.125'),[north,south]);
  assert.deepEqual(filterGlobeTableCells(cells,0,'A',[],false,'0.125 N'),[],'missing is not a zero');
  assert.deepEqual(filterGlobeTableCells(cells,1,'A',[],false,'0.125 N'),[missing]);
  assert.deepEqual(filterGlobeTableCells(cells,0,'A',[],true),[]);
  assert.deepEqual(globeTablePage([],100),{page:0,pages:1,rows:[],first:0,last:0});
  assert.equal(globeTablePage([north],-1).page,0);
  assert.equal(globeTablePage([north],NaN).page,0);
});
