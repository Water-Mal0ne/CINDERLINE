import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import ts from 'typescript';

const compiled=ts.transpileModule(readFileSync(new URL('../src/globeData.ts',import.meta.url),'utf8'),{
  compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022},
}).outputText;
const {validGlobeData}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const globe=JSON.parse(readFileSync(new URL('../public/data/globe.json',import.meta.url),'utf8'));
const hash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

test('all published globe values, sources, years and country identities pass unchanged',()=>{
  const before=hash(globe);
  assert.equal(validGlobeData(globe),true);
  assert.equal(hash(globe),before);
  assert.equal(globe.coverage_regions.length,7);
  assert.equal(globe.cells.length,41986);
});

test('invalid render metadata, annual rows and ambiguous cell identities are rejected',()=>{
  const row=globe.cells[0],small={...globe,cells:[row]};
  const invalid=[{},null,{...small,years:[]},{...small,years:[2024,2023]},
    {...small,coverage_regions:[null]},{...small,cell_size:0},{...small,cells:[null]},
    {...small,cells:[{...row,values:{}}]},
    {...small,cells:[{...row,values:row.values.slice(1)}]},
    {...small,cells:[{...row,lat:NaN}]},
    {...small,cells:[{...row,region:'Unpublished'}]},
    {...small,cells:[row,{...row,lat:row.lat+1}]}];
  for(const payload of invalid)assert.equal(validGlobeData(payload),false);
});

test('zero observations, unknown annual values and an empty annual layer remain distinct valid inputs',()=>{
  const row={...globe.cells[0],values:[0,null]};
  const sparse={...globe,years:[2023,2024],cells:[row]};
  assert.equal(validGlobeData(sparse),true);
  assert.deepEqual(row.values,[0,null]);
  assert.equal(validGlobeData({...sparse,cells:[]}),true);
});
