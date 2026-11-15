import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';

const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript');
function loader(fetch) {
  const source=readFileSync(new URL('../src/loadData.ts',import.meta.url),'utf8').replaceAll('import.meta.env.BASE_URL',JSON.stringify('/firetrace/'));
  const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.CommonJS}}).outputText;
  const module={exports:{}};
  new Function('module','exports','fetch',compiled)(module,module.exports,fetch);
  return module.exports;
}
const response=value=>({ok:true,json:async()=>value});
const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};

test('a repaired cell can be retried without evicting unrelated cached data',async()=>{
  const requests=[];
  let repaired=false;
  const api=loader(async(url,options)=>{requests.push({url,options});return response(url.endsWith('cell.json')?(repaired?{columns:['date','harmonized'],rows:[['2024-01-01',10]]}:{invalid:true}):{country:'Nepal'});});
  const region=await api.loadData('region.json');
  const awaitedCell=await api.loadData('cell.json');
  assert.throws(()=>api.decodeCell(awaitedCell),/Invalid cell data/);
  repaired=true;
  api.invalidateData('cell.json');
  assert.equal(await api.loadData('region.json'),region,'the successful region stays cached');
  const cell=await api.loadData('cell.json');
  assert.deepEqual(api.decodeCell(cell),[{date:'2024-01-01',harmonized:10}]);
  assert.equal(requests.length,3);
  assert.equal(requests[2].url,'/firetrace/data/cell.json');
  assert.equal(requests[2].options.cache,'reload');
  assert.equal(await api.loadData('cell.json'),cell);
  assert.equal(requests.length,3,'successful retry returns to ordinary memory caching');
});

test('failed and aborted refreshes remain eligible for a fresh network retry',async()=>{
  const requests=[];
  let failure='http';
  const controller=new AbortController();
  const api=loader(async(url,options)=>{
    requests.push(options);
    if(failure==='http')return {ok:false};
    if(failure==='abort')return {ok:true,json:async()=>{controller.abort();return {value:'aborted'};}};
    return response({value:'recovered'});
  });
  api.invalidateData('region.json');
  await assert.rejects(api.loadData('region.json'),/Processed data unavailable/);
  failure='abort';
  await assert.rejects(api.loadData('region.json',controller.signal),{name:'AbortError'});
  failure='none';
  assert.deepEqual(await api.loadData('region.json'),{value:'recovered'});
  assert.ok(requests.every(options=>options.cache==='reload'));
  await api.loadData('region.json');
  assert.equal(requests.length,3);
});

test('an older in-flight response cannot overwrite the refreshed resource',async()=>{
  const old=deferred(),requests=[];
  const api=loader(async(url,options)=>{requests.push(options);return requests.length===1?old.promise:response({version:'new'});});
  const first=api.loadData('region.json');
  api.invalidateData('region.json');
  assert.deepEqual(await api.loadData('region.json'),{version:'new'});
  old.resolve(response({version:'old'}));
  await first;
  assert.deepEqual(await api.loadData('region.json'),{version:'new'});
  assert.equal(requests.length,2);
  assert.equal(requests[0].cache,undefined);
  assert.equal(requests[1].cache,'reload');
});

test('an older refresh cannot clear a more recent invalidation',async()=>{
  const firstRefresh=deferred(),requests=[];
  const api=loader(async(url,options)=>{requests.push(options);return requests.length===1?firstRefresh.promise:response({version:'latest'});});
  api.invalidateData('region.json');
  const first=api.loadData('region.json');
  api.invalidateData('region.json');
  firstRefresh.resolve(response({version:'superseded'}));
  await first;
  assert.deepEqual(await api.loadData('region.json'),{version:'latest'});
  assert.equal(requests.length,2,'the superseded response must not repopulate the cache');
  assert.ok(requests.every(options=>options.cache==='reload'));
});
