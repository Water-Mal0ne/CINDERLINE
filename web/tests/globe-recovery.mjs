import assert from 'node:assert/strict';
import {test} from 'node:test';
import {existsSync,readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const require=createRequire(new URL('../package.json',import.meta.url));
const ts=require('typescript'),React=require('react');
const sourceRoot=fileURLToPath(new URL('../src/',import.meta.url));
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const alignmentSource=ts.transpileModule(readFileSync(path.join(sourceRoot,'calendarAlignment.ts'),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const {globeAlignmentIdentity,applyCalendarAlignment}=await import('data:text/javascript;base64,'+Buffer.from(alignmentSource).toString('base64'));
const shipped=JSON.parse(readFileSync(new URL('../public/data/globe.json',import.meta.url),'utf8'));
const shippedAlignment=JSON.parse(readFileSync(new URL('../public/data/calendar-alignment.json',import.meta.url),'utf8'));
// Preserve the real correction semantics when slicing a fast, small UI fixture.
async function alignmentFor(globe){
  const localIndex=new Map(globe.cells.map((cell,index)=>[cell.id,index]));
  const corrections=Object.fromEntries(Object.entries(shippedAlignment.corrections).map(([year,rows])=>[year,
    rows.filter(([ci])=>localIndex.has(shipped.cells[ci].id)).map(([ci,di])=>[localIndex.get(shipped.cells[ci].id),di])
  ]));
  return {...shippedAlignment,cell_count:globe.cells.length,corrections,
    source:{...shippedAlignment.source,globe_view_sha256:await globeAlignmentIdentity(globe)}};
}
const data={...shipped,cells:shipped.cells.filter(cell=>cell.region==='Nepal').slice(0,3)};
const alignment=await alignmentFor(data);
const props={regionId:'Nepal',year:2024,onYear(){},onRegion(){},onCell(){},availableCells:[]};
const nodes=(value,predicate)=>Array.isArray(value)?value.flatMap(v=>nodes(v,predicate)):
  !value||typeof value!=='object'?[]:[...(predicate(value)?[value]:[]),...nodes(value.props?.children,predicate)];
const text=value=>Array.isArray(value)?value.map(text).join(''):
  value&&typeof value==='object'?text(value.props?.children):String(value??'');
const button=(tree,label)=>nodes(tree,node=>node.type==='button'&&text(node)===label)[0];
const selection=tree=>nodes(tree,node=>node.props?.role==='region'&&String(node.props?.['aria-label']).startsWith('Selected grid cell'))[0];

// Exercise the actual Globe hooks and shared loader. Canvas refs intentionally
// stay unmounted; WebGL appearance and focus layout are checked in the browser.
function mount(responses){
  const slots=[],modules=new Map(),requests=[],attempts=new Map();
  let cursor=0,effects=[],dirty=true,tree,currentProps=props;
  const same=(a,b)=>a&&b&&a.length===b.length&&a.every((value,i)=>Object.is(value,b[i]));
  const hooks={...React,
    useState(initial){const at=cursor++;if(!(at in slots))slots[at]={value:typeof initial==='function'?initial():initial};return [slots[at].value,value=>{const next=typeof value==='function'?value(slots[at].value):value;if(!Object.is(next,slots[at].value)){slots[at].value=next;dirty=true;}}];},
    useRef(initial){const at=cursor++;if(!(at in slots))slots[at]={current:initial};return slots[at];},
    useMemo(factory,deps){const at=cursor++;if(!slots[at]||!same(slots[at].deps,deps))slots[at]={deps,value:factory()};return slots[at].value;},
    useEffect(effect,deps){const at=cursor++;if(!slots[at]||!same(slots[at].deps,deps)){const previous=slots[at];slots[at]={deps,cleanup:null};effects.push({at,effect,cleanup:previous?.cleanup});}},
  };
  const fetch=async(url,options)=>{
    requests.push({url,options});
    const attempt=attempts.get(url)??0;attempts.set(url,attempt+1);
    const response=responses[Math.min(attempt,responses.length-1)];
    assert.ok(url==='/data/globe.json'||url==='/data/calendar-alignment.json',`unexpected resource ${url}`);
    const value=url.endsWith('/globe.json')?response.globe:response.alignment;
    return {ok:true,json:async()=>value};
  };
  function load(file){
    if(modules.has(file))return modules.get(file);
    const source=readFileSync(file,'utf8').replaceAll('import.meta.env.BASE_URL',JSON.stringify('/'));
    const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
    const module={exports:{}};
    new Function('require','module','exports','fetch','requestAnimationFrame',compiled)(name=>{
      if(name==='react')return hooks;
      if(name==='three'||name.includes('OrbitControls')||name.endsWith('.css'))return {};
      if(name.startsWith('.')){
        const base=path.resolve(path.dirname(file),name);
        return load(existsSync(base+'.tsx')?base+'.tsx':base+'.ts');
      }
      return require(name);
    },module,module.exports,fetch,callback=>{callback();return 1;});
    modules.set(file,module.exports);return module.exports;
  }
  const Globe=load(path.join(sourceRoot,'Globe.tsx')).default;
  function render(){cursor=0;effects=[];dirty=false;tree=Globe(currentProps);for(const item of effects)item.cleanup?.();for(const item of effects)slots[item.at].cleanup=item.effect();}
  return {
    async settle(){
      // WebCrypto settles on an event-loop turn, not only a promise microtask.
      for(let i=0;i<1000;i++){
        if(dirty)render();
        await new Promise(resolve=>setTimeout(resolve,1));
        const loading=nodes(tree,node=>node.props?.role==='status'&&text(node).includes('Loading annual grid observations')).length;
        if(!dirty&&!loading)return tree;
      }
      assert.fail('Globe did not settle after loading and source verification');
    },
    click(label){const target=button(tree,label);assert.ok(target,`button ${label} exists`);target.props.onClick();},
    changeProps(patch){currentProps={...currentProps,...patch};dirty=true;},
    get tree(){return tree;},requests,
    dispose(){for(const slot of slots)slot?.cleanup?.();},
  };
}

test('malformed successful globe data reaches a scoped retry and never poisons the next render',async()=>{
  const app=mount([{globe:{},alignment},{globe:data,alignment}]);
  try{
    await app.settle();
    assert.ok(nodes(app.tree,node=>node.props?.role==='alert').length);
    app.click('Retry annual globe layer');await app.settle();
    assert.equal(nodes(app.tree,node=>node.props?.role==='alert').length,0);
    assert.ok(button(app.tree,'Grid table'));
    assert.equal(app.requests.length,4);
    for(const url of ['/data/globe.json','/data/calendar-alignment.json']){
      const calls=app.requests.filter(request=>request.url===url);
      assert.equal(calls.length,2,`${url} must be fetched again on retry`);
      assert.equal(calls[1].options.cache,'reload');
    }
  }finally{app.dispose();}
});

test('the inspected annual cell survives Earth/table round trips and resets on country change',async()=>{
  const app=mount([{globe:data,alignment}]);
  try{
    await app.settle();app.click('Grid table');await app.settle();
    const inspect=nodes(app.tree,node=>node.type==='button'&&String(node.props?.['aria-label']).startsWith('Inspect grid cell'))[0];
    assert.ok(inspect);inspect.props.onClick();await app.settle();
    const original=selection(app.tree)?.props['aria-label'];assert.ok(original);
    app.click('Show 3D Earth');await app.settle();
    assert.equal(selection(app.tree)?.props['aria-label'],original);
    app.click('Grid table');await app.settle();
    assert.equal(selection(app.tree)?.props['aria-label'],original);
    assert.equal(nodes(app.tree,node=>node.type==='button'&&node.props['aria-pressed']===true&&text(node)==='Selected').length,1);
    app.changeProps({regionId:'India'});await app.settle();
    assert.equal(selection(app.tree),undefined);
  }finally{app.dispose();}
});

test('annual regional drill-down forwards its displayed year even when the country is already selected',async()=>{
  const requests=[],app=mount([{globe:data,alignment}]);
  try{
    app.changeProps({year:2020,onRegion:(...args)=>requests.push(args)});
    await app.settle();app.click('Grid table');await app.settle();
    nodes(app.tree,node=>node.type==='button'&&String(node.props?.['aria-label']).startsWith('Inspect grid cell'))[0].props.onClick();
    await app.settle();
    const action=nodes(selection(app.tree),node=>node.type==='button')[0];
    action.props.onClick();
    assert.deepEqual(requests,[['Nepal',2020]],'regional navigation must carry the inspected annual context');
    assert.equal(text(action).trim(),'Open 2020 region calendar');
    app.changeProps({year:2019});await app.settle();
    const changedYearAction=nodes(selection(app.tree),node=>node.type==='button')[0];
    changedYearAction.props.onClick();
    assert.deepEqual(requests,[['Nepal',2020],['Nepal',2019]],'a retained cell must use the newly displayed year');
    assert.equal(text(changedYearAction).trim(),'Open 2019 region calendar');
  }finally{app.dispose();}
});

test('annual daily drill-down forwards the local published cell ID and the selected year',async()=>{
  const country=JSON.parse(readFileSync(new URL('../public/data/Nepal.json',import.meta.url),'utf8'));
  const id=country.cells[0].id;
  const annual=shipped.cells.find(cell=>cell.id===`Nepal:${id}`);
  assert.ok(annual);
  const dailyData={...shipped,cells:[annual]};
  const requests=[],app=mount([{globe:dailyData,alignment:await alignmentFor(dailyData)}]);
  try{
    app.changeProps({year:2020,availableCells:[id],onCell:(...args)=>requests.push(args)});
    await app.settle();app.click('Grid table');await app.settle();
    nodes(app.tree,node=>node.type==='button'&&String(node.props?.['aria-label']).startsWith('Inspect grid cell'))[0].props.onClick();
    await app.settle();
    const action=nodes(selection(app.tree),node=>node.type==='button')[0];
    action.props.onClick();
    assert.deepEqual(requests,[[id,2020]],'country-qualified annual IDs must become the existing local daily ID');
    assert.equal(text(action).trim(),'Open 2020 daily record');
  }finally{app.dispose();}
});

test('the Earth selection shortcut targets the selected evidence without moving focus until requested',async()=>{
  const app=mount([{globe:data,alignment}]);
  try{
    await app.settle();
    assert.equal(button(app.tree,'Inspect selected cell'),undefined);
    app.click('Grid table');await app.settle();
    nodes(app.tree,node=>node.type==='button'&&String(node.props?.['aria-label']).startsWith('Inspect grid cell'))[0].props.onClick();
    await app.settle();
    assert.equal(button(app.tree,'Inspect selected cell'),undefined,'table inspection already focuses the evidence directly');
    let focused=0;
    selection(app.tree).ref.current={focus(){focused++;}};
    app.click('Show 3D Earth');await app.settle();
    const shortcut=button(app.tree,'Inspect selected cell'),panel=selection(app.tree);
    assert.ok(shortcut);
    assert.equal(shortcut.props['aria-controls'],panel.props.id);
    assert.equal(shortcut.props['aria-label'].replace('Inspect selected cell ','Selected grid cell '),panel.props['aria-label']);
    assert.equal(focused,0,'opening the globe does not jump away from it');
    app.click('Inspect selected cell');
    assert.equal(focused,1,'explicit inspection focuses the matching below-globe panel');
    app.changeProps({regionId:'India'});await app.settle();
    assert.equal(button(app.tree,'Inspect selected cell'),undefined,'clearing selection removes the shortcut');
  }finally{app.dispose();}
});

test('a wrong-source annual alignment fails closed, then retry reloads both resources',async()=>{
  const stale=structuredClone(alignment);stale.source.globe_view_sha256='0'.repeat(64);
  const app=mount([{globe:data,alignment:stale},{globe:data,alignment}]);
  try{
    await app.settle();
    assert.ok(nodes(app.tree,node=>node.props?.role==='alert').length);
    assert.equal(button(app.tree,'Grid table'),undefined,'unverified annual values must never render');
    app.click('Retry annual globe layer');await app.settle();
    assert.ok(button(app.tree,'Grid table'));
    assert.equal(nodes(app.tree,node=>node.props?.role==='alert').length,0);
    for(const url of ['/data/globe.json','/data/calendar-alignment.json']){
      const calls=app.requests.filter(request=>request.url===url);
      assert.equal(calls.length,2);assert.equal(calls[1].options.cache,'reload');
    }
  }finally{app.dispose();}
});

test('the grid table and selected evidence use the derived annual value',async()=>{
  const [ci]=shippedAlignment.corrections['2024'][0];
  const globe={...shipped,cells:[shipped.cells[ci]]};
  const correction=await alignmentFor(globe),aligned=await applyCalendarAlignment(globe,correction);
  const yi=globe.years.indexOf(2024),expected=aligned.cells[0].values[yi];
  assert.ok(expected<globe.cells[0].values[yi],'fixture must exercise a nonzero exclusion');
  const app=mount([{globe,alignment:correction}]);
  try{
    app.changeProps({regionId:globe.cells[0].region});
    await app.settle();app.click('Grid table');await app.settle();
    const row=nodes(app.tree,node=>node.type==='tr'&&nodes(node,child=>child.type==='button'&&String(child.props?.['aria-label']).startsWith('Inspect grid cell')).length)[0];
    const format=value=>Number(value).toLocaleString('en-US',{maximumFractionDigits:1});
    assert.equal(text(nodes(row,node=>node.type==='td')[1]),format(expected));
    nodes(row,node=>node.type==='button')[0].props.onClick();await app.settle();
    assert.ok(text(selection(app.tree)).includes(`${format(expected)} Aqua-reference-equivalent detections in 2024`));
  }finally{app.dispose();}
});
