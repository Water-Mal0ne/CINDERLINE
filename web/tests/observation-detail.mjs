import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createHash,webcrypto} from 'node:crypto';
import {createRequire} from 'node:module';
import ts from 'typescript';

if(!globalThis.crypto)globalThis.crypto=webcrypto;
const compiled=ts.transpileModule(readFileSync(new URL('../src/observationDetail.ts',import.meta.url),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const api=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const bytes=value=>Buffer.from(JSON.stringify(value));
const zeroHash='0'.repeat(64);
const ref={month:'2024-04',file:'observations/Nepal/2024-04.json',sha256:zeroHash,count:2};
const tile={id:'27_85',file:'observations/Nepal/2024-04/27_85.json',sha256:zeroHash,count:2,bounds:[85,27,86,28]};
const month={schema:'observations-v1',sensor:'VIIRS S-NPP',country:'Nepal',month:'2024-04',time_basis:'UTC',source_sha256:zeroHash,grid_size:.05,count:2,grid:[[550,1710,2]],tiles:[tile]};
const raw={schema:'observations-v1',sensor:'VIIRS S-NPP',country:'Nepal',month:'2024-04',time_basis:'UTC',id:tile.id,columns:[...api.OBSERVATION_COLUMNS],rows:[[27.5,85.5,'2024-04-01T06:30:00Z','n',.38,.4,0,'D'],[27.50001,85.50001,'2024-04-01T18:30:00Z','h',null,null,null,'N']]};
const index={schema:'observations-v1',sensor:'VIIRS S-NPP',year:2024,time_basis:'UTC',grid_size:.05,columns:[...api.OBSERVATION_COLUMNS],countries:[{id:'Nepal',name:'Nepal',source:{url:'https://firms.modaps.eosdis.nasa.gov/archive.csv',sha256:zeroHash,rows:2},months:[ref]}]};
const response=body=>({ok:true,arrayBuffer:async()=>body.buffer.slice(body.byteOffset,body.byteOffset+body.byteLength)});

test('observed records preserve timestamps, original coordinates, true zero FRP and unknown footprints',()=>{
  const before=JSON.stringify(raw),points=api.decodeObservationTile(raw,month,tile);
  assert.equal(points.length,2);
  assert.equal(points[0].frp,0);assert.equal(points[1].frp,null);
  assert.equal(points[1].scan,null);assert.equal(points[1].track,null);
  assert.equal(points[1].lat,27.50001);assert.equal(points[1].lon,85.50001);
  assert.equal(points[1].utc,'2024-04-01T18:30:00Z');
  assert.notEqual(points[0].id,points[1].id);
  assert.equal(JSON.stringify(raw),before);
});

test('mismatched country, month, malformed dates, invalid confidence and out-of-tile coordinates fail closed',()=>{
  const altered=(i,value)=>({...raw,rows:[raw.rows[0].map((old,j)=>j===i?value:old),raw.rows[1]]});
  for(const value of [{...raw,country:'India'},{...raw,month:'2024-05'},{...raw,id:'other'},{...raw,time_basis:'local'},{...raw,count:1},{...raw,bounds:[84,27,86,28]},
    altered(0,91),altered(1,84.99),altered(2,'2024-04-31T06:30:00Z'),altered(2,'2024-04-01T06:30:00+05:45'),
    altered(2,'2024-04-01T06:30:59Z'),altered(3,'l'),altered(4,0),altered(5,-1),altered(6,-.1),altered(6,Infinity),altered(7,'day')]){
    assert.throws(()=>api.decodeObservationTile(value,month,tile),/validation/);
  }
});

test('month grids and tile inventories conserve country-month counts without duplicate identities',()=>{
  assert.deepEqual(api.decodeObservationMonth(month,'Nepal',ref),month);
  for(const value of [{...month,grid:[[550,1710,1]]},{...month,tiles:[]},{...month,time_basis:'local'},{...month,grid:[[550,1710,1],[550,1710,1]]},
    {...month,tiles:[tile,tile]},{...month,grid:[[1800,1710,2]]},{...month,tiles:[{...tile,bounds:[85,27,85,28]}]},{...month,tiles:[{...tile,file:'observations/../secret.json'}]}]){
    assert.throws(()=>api.decodeObservationMonth(value,'Nepal',ref),/validation/);
  }
  const empty={...month,count:0,grid:[],tiles:[]};
  assert.deepEqual(api.decodeObservationMonth(empty,'Nepal',{...ref,count:0}),empty);
});

test('manifest rejects an unsupported sensor, year, duplicate country or duplicate month',()=>{
  assert.deepEqual(api.decodeObservationIndex(index),index);
  for(const value of [{...index,sensor:'MODIS Aqua'},{...index,year:2025},{...index,time_basis:'local'},
    {...index,countries:[index.countries[0],index.countries[0]]},
    {...index,countries:[{...index.countries[0],months:[ref,ref]}]}])assert.throws(()=>api.decodeObservationIndex(value),/validation/);
});

test('downloaded bytes must match the manifest hash before decoding',async()=>{
  const body=bytes(raw),correctTile={...tile,sha256:hash(body)},context={...month,tiles:[correctTile]};
  const options={fetcher:async()=>response(body)};
  assert.equal((await api.loadObservationTiles(context,[correctTile],undefined,options)).length,2);
  await assert.rejects(api.loadObservationTiles(context,[correctTile],undefined,{fetcher:async()=>response(bytes({...raw,rows:[raw.rows[0]]}))}),/manifest/);
  await assert.rejects(api.loadObservationTiles(context,[{...correctTile,file:'observations/Nepal/other.json'}],undefined,options),/validation/);
});

test('cancelled fetches cannot publish stale points even when a fetch implementation ignores cancellation',async()=>{
  const body=bytes(raw),correctTile={...tile,sha256:hash(body)},context={...month,tiles:[correctTile]};
  const controller=new AbortController();let release;
  const pending=api.loadObservationTiles(context,[correctTile],controller.signal,{fetcher:async()=>{await new Promise(resolve=>{release=resolve;});return response(body);}});
  controller.abort();release();
  await assert.rejects(pending,error=>error.name==='AbortError');
});

test('tile requests have bounded concurrency and preserve separate identities for repeated detections',async()=>{
  let active=0,peak=0;const payloads=new Map();
  const tiles=Array.from({length:7},(_,i)=>{
    const id=`chunk${i}`,body=bytes({...raw,id}),entry={...tile,id,file:`observations/Nepal/2024-04/${id}.json`,sha256:hash(body)};
    payloads.set('/data/'+entry.file,body);return entry;
  });
  const points=await api.loadObservationTiles({...month,count:14,tiles},tiles,undefined,{fetcher:async url=>{
    active++;peak=Math.max(peak,active);await new Promise(resolve=>setTimeout(resolve,2));active--;return response(payloads.get(url));
  }});
  assert.equal(peak,2);assert.equal(points.length,14);assert.equal(new Set(points.map(p=>p.id)).size,14);
});

test('month downloads enforce selected context and retry requests reload cached resources',async()=>{
  const body=bytes(month),goodRef={...ref,sha256:hash(body)},goodIndex={...index,countries:[{...index.countries[0],months:[goodRef]}]};
  let received;
  assert.equal((await api.loadObservationMonth(goodIndex,'Nepal','2024-04',undefined,{reload:true,fetcher:async(url,options)=>{received={url,options};return response(body);}})).count,2);
  assert.equal(received.options.cache,'reload');
  await assert.rejects(api.loadObservationMonth(goodIndex,'Nepal','2025-04'),/not published/);
  assert.equal(api.observationMonthLabel('2024-04'),'April 2024');
});

const require=createRequire(import.meta.url),React=require('react');
const controlSource=ts.transpileModule(readFileSync(new URL('../src/ObservationControls.tsx',import.meta.url),'utf8').replaceAll('import.meta.env.BASE_URL',JSON.stringify('/')),{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
function controlsModule(react=React,data=api){
  const module={exports:{}};
  new Function('require','module','exports',controlSource)(name=>name==='react'?react:name==='./observationDetail'?data:name.endsWith('.css')?{}:require(name),module,module.exports);
  return module.exports;
}
test('observation controls distinguish unharmonized UTC data, limited coverage and unknown values',()=>{
  const {renderToStaticMarkup}=require('react-dom/server'),Controls=controlsModule().default;
  const html=renderToStaticMarkup(React.createElement(Controls,{mode:'observations',onMode(){},month:'2024-04',regionName:'Nepal',status:'ready',pointCount:2,display:'points',loadedPointCount:2,selectedPoint:api.decodeObservationTile(raw,month,tile)[0]}));
  assert.match(html,/Observed VIIRS detections · not harmonized · UTC dates/);
  assert.match(html,/2024 detail only/);assert.match(html,/local-date, outage-masked calendar/);
  assert.match(html,/<p class="observation-scope">[^<]*UTC records include detections on calendar-excluded dates, so totals differ\./);
  assert.match(html,/schematic pixel centres, not fire boundaries/);
  assert.match(html,/0 MW/);assert.match(html,/0.38 km/);
  assert.match(html,/aria-pressed="true"[^>]*>Satellite observations/);
  const empty=renderToStaticMarkup(React.createElement(Controls,{mode:'observations',onMode(){},status:'ready',pointCount:0}));
  assert.match(empty,/does not establish that no fires occurred/);
  const overview=renderToStaticMarkup(React.createElement(Controls,{mode:'harmonized',onMode(){}}));
  assert.match(overview,/Harmonized overview/);assert.doesNotMatch(overview,/Observation month|0 qualifying/);
});

test('selecting a new observation focuses its evidence once; clearing returns focus to the month control',()=>{
  const refs=[],effectSlots=[],focusEvents=[];let refCursor=0,effectCursor=0,effects=[],tree,cleared=0;
  const same=(a,b)=>a&&b&&a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));
  const hooks={...React,useId:()=>':observation-test:',useRef(initial){const at=refCursor++;return refs[at]??(refs[at]={current:initial});},useEffect(effect,deps){const at=effectCursor++;if(!same(effectSlots[at],deps)){effectSlots[at]=deps;effects.push(effect);}}};
  const Controls=controlsModule(hooks).default;
  const nodes=value=>Array.isArray(value)?value.flatMap(nodes):value&&typeof value==='object'?[value,...nodes(value.props?.children)]:[];
  const render=selectedPoint=>{
    refCursor=0;effectCursor=0;effects=[];
    tree=Controls({mode:'observations',onMode(){},status:'ready',selectedPoint,onClearSelection(){cleared++;}});
    for(const node of nodes(tree))if(node.ref&&typeof node.ref==='object')node.ref.current=node.type==='section'?{focus(options){focusEvents.push(['evidence',options]);},scrollIntoView(options){focusEvents.push(['scroll',options]);}}:{focus(options){focusEvents.push(['month',options]);}};
    for(const effect of effects)effect();
  };
  const points=api.decodeObservationTile(raw,month,tile);
  render(null);assert.deepEqual(focusEvents,[]);
  render(points[0]);assert.deepEqual(focusEvents,[['evidence',{preventScroll:true}],['scroll',{block:'nearest'}]]);
  const evidence=nodes(tree).find(node=>node.type==='section');assert.equal(evidence.props.tabIndex,-1);
  render({...points[0]});assert.equal(focusEvents.length,2);
  render(points[1]);assert.equal(focusEvents.length,4);
  nodes(tree).find(node=>node.type==='button'&&node.props.children==='Clear observation').props.onClick();
  assert.equal(cleared,1);assert.deepEqual(focusEvents.at(-1),['month',{preventScroll:true}]);
  render(null);assert.equal(focusEvents.length,5);
});

test('country changes suppress earlier hook results before and after pending downloads finish',async()=>{
  const slots=[],pending=[];let cursor=0,effects=[],dirty=true,params={enabled:true,country:'Nepal',month:'2024-04'},view;
  const same=(a,b)=>a&&b&&a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));
  const hooks={...React,
    useState(initial){const n=cursor++;if(!(n in slots))slots[n]={value:initial};return [slots[n].value,value=>{slots[n].value=typeof value==='function'?value(slots[n].value):value;dirty=true;}];},
    useEffect(effect,deps){const n=cursor++;if(!same(slots[n]?.deps,deps)){const cleanup=slots[n]?.cleanup;slots[n]={deps};effects.push(()=>{cleanup?.();slots[n].cleanup=effect();});}},
  };
  const mock={...api,loadObservationIndex:async()=>index,loadObservationMonth:async(_index,country,selectedMonth)=>new Promise(resolve=>pending.push({country,month:selectedMonth,resolve}))};
  const {useObservationDetail}=controlsModule(hooks,mock);
  const render=()=>{cursor=0;effects=[];dirty=false;view=useObservationDetail(params);for(const effect of effects)effect();};
  const settle=async()=>{for(let i=0;i<5;i++){if(dirty)render();await Promise.resolve();}};
  await settle();assert.equal(pending[0].country,'Nepal');
  params={...params,country:'India'};dirty=true;await settle();
  assert.equal(view.status,'loading');assert.equal(view.monthData,null);
  pending[1].resolve({...month,country:'India'});await settle();
  assert.equal(view.monthData.country,'India');
  pending[0].resolve(month);await settle();
  assert.equal(view.monthData.country,'India');
  params={...params,enabled:false};dirty=true;await settle();
  assert.equal(view.status,'idle');assert.equal(view.monthData,null);
  for(const slot of slots)slot.cleanup?.();
});

test('all seven published countries and 84 month inventories pass the browser contract and byte hashes',async()=>{
  const options={fetcher:async url=>response(readFileSync(new URL('../public'+url,import.meta.url)))};
  const published=await api.loadObservationIndex(undefined,options);
  assert.equal(published.countries.length,7);
  assert.deepEqual(published.countries.map(c=>c.id).sort(),['Australia','Bangladesh','Brazil','Egypt','India','Nepal','United_States']);
  let inspected=0;
  for(const country of published.countries){
    assert.equal(country.months.length,12);let total=0,busiest;
    for(const ref of country.months){
      const data=await api.loadObservationMonth(published,country.id,ref.month,undefined,options);
      total+=data.count;inspected++;
      if(!busiest||data.count>busiest.count)busiest=data;
    }
    assert.equal(total,country.count);
    const tile=[...busiest.tiles].sort((a,b)=>b.count-a.count)[0];
    if(tile){const points=await api.loadObservationTiles(busiest,[tile],undefined,options);assert.equal(points.length,tile.count);}
  }
  assert.equal(inspected,84);
});
