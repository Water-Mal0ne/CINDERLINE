import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const require=createRequire(new URL('../package.json',import.meta.url));
const ts=require('typescript'),React=require('react');
const sourceRoot=fileURLToPath(new URL('../src/',import.meta.url));
const cellId='27.25:84.75',cellFile='Nepal-cell.json';
const daily=Array.from({length:14},(_,i)=>({date:`2024-01-${String(i+1).padStart(2,'0')}`,cell_id:cellId,
  raw_terra:3,raw_aqua:4,raw_viirs:8,raw:8,harmonized:4,lo:3,hi:5,coverage:'unknown',source:'converted VIIRS',model:'M1'}));
const region={meta:{region:'Nepal',name:'Nepal',label:'REAL FIRMS DATA',period_start:'2024-01-01',period_end:'2024-01-14',reference:'Aqua',model:'M1',coverage_note:'Unknown coverage',sources:[],centroid:[85,28]},
  daily,cells:[{id:cellId,file:cellFile,lat:27.25,lon:84.75}],anomalies:[],eval:[],weekly_climatology:[],critical_periods:[],rhythm:null};
const index={label:'REAL FIRMS DATA',generated_at:'2026-11-15T00:00:00Z',limitations:[],regions:[{id:'Nepal',name:'Nepal',file:'Nepal.json'}]};
const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};

function elements(node,predicate){
  if(!node||typeof node!=='object')return [];
  if(Array.isArray(node))return node.flatMap(item=>elements(item,predicate));
  return [...(predicate(node)?[node]:[]),...elements(node.props?.children,predicate)];
}
function text(node){
  if(node==null||typeof node==='boolean')return '';
  if(typeof node==='string'||typeof node==='number')return String(node);
  if(Array.isArray(node))return node.map(text).join('');
  return text(node.props?.children);
}
const namedChild=(tree,name)=>elements(tree,node=>node.type?.name===name)[0];
function button(tree,label){return elements(tree,node=>node.type==='button'&&text(node)===label)[0];}

// Run the actual App hooks, event handlers and promise continuations. Child views
// are inert elements: these tests cover App state transitions, not browser layout.
function appHarness(search,resource,indexResource=()=>Promise.resolve(index)){
  const slots=[],modules=new Map(),invalidated=[],requests=[],focus=[];
  let cursor=0,effects=[],dirty=true,tree,location=new URL(`https://firetrace.test/${search}`);
  const same=(a,b)=>a&&b&&a.length===b.length&&a.every((value,i)=>Object.is(value,b[i]));
  const memo=(factory,deps)=>{const slot=cursor++;if(!slots[slot]||!same(slots[slot].deps,deps))slots[slot]={deps,value:factory()};return slots[slot].value;};
  const hooks={...React,
    useState(initial){const slot=cursor++;if(!(slot in slots))slots[slot]={value:typeof initial==='function'?initial():initial};return [slots[slot].value,value=>{const next=typeof value==='function'?value(slots[slot].value):value;if(!Object.is(next,slots[slot].value)){slots[slot].value=next;dirty=true;}}];},
    useRef(initial){const slot=cursor++;if(!(slot in slots))slots[slot]={current:initial};return slots[slot];},
    useMemo:memo,useCallback:(fn,deps)=>memo(()=>fn,deps),
    useEffect(effect,deps){const slot=cursor++;if(!slots[slot]||!same(slots[slot].deps,deps)){const previous=slots[slot];slots[slot]={deps,cleanup:null};effects.push({slot,effect,cleanup:previous?.cleanup});}},
    lazy:()=>function LazyChild(){return null;},
  };
  const listeners=new Map();
  const window={get location(){return location;},history:{state:null,replaceState(_state,_title,url){location=new URL(url,location);}},
    addEventListener(name,fn){listeners.set(name,fn);},removeEventListener(name,fn){if(listeners.get(name)===fn)listeners.delete(name);},
    matchMedia:()=>({matches:true}),scrollTo(){}};
  const document={getElementById:id=>({focus(){focus.push(id);},scrollIntoView(){}})};
  const fetch=async url=>{assert.match(url,/data\/index\.json$/);return {ok:true,json:indexResource};};
  const realModules=new Set(['App','utils','explorationState','explorationIntegration','calendarView','loadData']);
  function load(file){
    if(modules.has(file))return modules.get(file);
    const source=readFileSync(file,'utf8').replaceAll('import.meta.env.BASE_URL',JSON.stringify('/'));
    const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
    const module={exports:{}};
    new Function('require','module','exports','window','document','fetch',compiled)(name=>{
      if(name==='react')return hooks;
      if(name.endsWith('.css'))return {};
      if(name.startsWith('.')){
        const basename=path.basename(name);
        if(!realModules.has(basename))return {default:function ChildView(){return null;}};
        return load(path.resolve(path.dirname(file),name+(basename==='App'?'.tsx':'.ts')));
      }
      return require(name);
    },module,module.exports,window,document,fetch);
    if(path.basename(file)==='loadData.ts')module.exports={...module.exports,
      loadData:(file,signal)=>{requests.push(file);return resource(file,signal);},invalidateData:file=>invalidated.push(file)};
    modules.set(file,module.exports);return module.exports;
  }
  const App=load(path.join(sourceRoot,'App.tsx')).default;
  function render(){cursor=0;effects=[];dirty=false;tree=App();const pending=effects;for(const item of pending)item.cleanup?.();for(const item of pending)slots[item.slot].cleanup=item.effect();}
  async function settle(){
    // Drain bounded microtask turns; unresolved deferred requests remain pending.
    for(let i=0;i<50;i++){if(dirty)render();await Promise.resolve();}
    assert.equal(dirty,false,'App effects must reach a stable render');return tree;
  }
  return {settle,click(label){const target=button(tree,label);assert.ok(target,`button '${label}' exists`);assert.ok(!target.props.disabled,`button '${label}' is enabled`);target.props.onClick();},
    pop(search){location=new URL(search,location);listeners.get('popstate')?.();},
    get tree(){return tree;},get url(){return location;},invalidated,requests,focus,
    dispose(){for(const slot of slots)slot?.cleanup?.();}};
}

test('a delayed region response cannot override explicit Methods navigation or reopen the original week',async()=>{
  const pending=deferred();
  const app=appHarness('?region=Nepal&view=evidence&week=2024-01-01&scale=raw',file=>file==='Nepal.json'?pending.promise:Promise.resolve({daily}));
  try{
    await app.settle();assert.deepEqual(app.requests,['Nepal.json']);
    app.click('Methods');await app.settle();assert.ok(namedChild(app.tree,'Methods'));
    pending.resolve(region);await app.settle();
    assert.ok(namedChild(app.tree,'Methods'),'the explicit view must survive delayed URL hydration');
    assert.equal(namedChild(app.tree,'EvidenceDrawer'),undefined);
    assert.equal(app.url.searchParams.get('view'),'methods');
    assert.equal(app.url.searchParams.get('scale'),'raw','data scale still restores');
    assert.equal(app.url.searchParams.get('region'),'Nepal');
    assert.equal(app.url.searchParams.has('week'),false);
    assert.ok(app.focus.includes('main'));
  }finally{app.dispose();}
});

function failingCellApp(){
  let cellCalls=0;
  return appHarness(`?region=Nepal&cell=${encodeURIComponent(cellId)}&week=2024-01-01`,file=>{
    if(file==='Nepal.json')return Promise.resolve(region);
    assert.equal(file,cellFile);
    return ++cellCalls===1?Promise.reject(new Error('503 temporary outage')):Promise.resolve({daily});
  });
}

test('a shared evidence week survives cell failure and opens after a successful scoped retry',async()=>{
  const app=failingCellApp();
  try{
    await app.settle();assert.equal(namedChild(app.tree,'EvidenceDrawer'),undefined);
    assert.match(text(app.tree),/grid data was unavailable/);
    app.click('Retry loading');await app.settle();
    assert.deepEqual(app.invalidated,[cellFile]);
    const drawer=namedChild(app.tree,'EvidenceDrawer');
    assert.ok(drawer,'the original week must be restored after recovery');
    assert.equal(drawer.props.week.date,'2024-01-01');
    assert.equal(drawer.props.cellId,cellId);
    assert.equal(app.url.searchParams.get('week'),'2024-01-01');
    assert.equal(app.url.searchParams.get('cell'),cellId);
    assert.doesNotMatch(text(app.tree),/grid data was unavailable/);
  }finally{app.dispose();}
});

test('deliberate navigation cancels a retained evidence week before a later retry succeeds',async()=>{
  const app=failingCellApp();
  try{
    await app.settle();app.click('Methods');await app.settle();
    app.click('Retry loading');await app.settle();
    assert.ok(namedChild(app.tree,'Methods'));
    assert.equal(namedChild(app.tree,'EvidenceDrawer'),undefined,'recovery must not reopen a deliberately dismissed view');
    assert.equal(app.url.searchParams.get('view'),'methods');
    assert.equal(app.url.searchParams.has('week'),false);
    assert.deepEqual(app.invalidated,[cellFile]);
  }finally{app.dispose();}
});

test('independent shared pages open even when the calendar country fails',async()=>{
  for(const [view,label] of [['rhythm','Weekly Rhythm Index'],['methods','Methods']]){
    const app=appHarness(`?view=${view}`,()=>Promise.reject(new Error('country unavailable')));
    try{
      await app.settle();
      assert.equal(button(app.tree,label).props['aria-current'],'page');
      assert.match(text(app.tree),/This region has no readable processed data/);
    }finally{app.dispose();}
  }
});

test('independent shared pages open without waiting for the calendar index',async()=>{
  for(const [view,label] of [['rhythm','Weekly Rhythm Index'],['methods','Methods']]){
    const pending=deferred(),app=appHarness(`?view=${view}`,()=>Promise.resolve(region),()=>pending.promise);
    try{
      await app.settle();
      assert.equal(button(app.tree,label).props['aria-current'],'page');
      assert.deepEqual(app.requests,[]);
      pending.resolve(null);await app.settle();
      assert.equal(button(app.tree,label).props['aria-current'],'page','index failure cannot hide the independent page');
    }finally{app.dispose();}
  }
});

test('history and Methods anchors preserve index retry when the catalog is unavailable',async()=>{
  let calls=0;
  const app=appHarness('?view=methods',()=>Promise.resolve(region),()=>Promise.resolve(++calls===1?null:index));
  try{
    await app.settle();
    app.pop('?view=methods#method-limitations');await app.settle();
    assert.equal(button(app.tree,'Methods').props['aria-current'],'page');
    app.click('Retry loading');await app.settle();
    assert.equal(button(app.tree,'Methods').props['aria-current'],'page');
    assert.equal(button(app.tree,'Retry loading'),undefined,'catalog retry must recover after a hash/history transition');
    assert.deepEqual(app.requests,['Nepal.json']);
  }finally{app.dispose();}
});
