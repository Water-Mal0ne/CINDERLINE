import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const source=readFileSync(new URL('../src/globeCells.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const {createGlobeCellSelection}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const pointer=(patch={})=>({pointerId:1,clientX:100,clientY:100,button:0,isPrimary:true,...patch});

test('a primary click or tap tolerates small hand movement and selects only once',()=>{
  const gesture=createGlobeCellSelection();
  gesture.down(pointer());
  gesture.move(pointer({clientX:102,clientY:101}));
  assert.equal(gesture.up(pointer({clientX:103,clientY:102})),true);
  assert.equal(gesture.up(pointer()),false,'a duplicate release cannot select again');
});

test('secondary and middle mouse buttons never select annual cells',()=>{
  for(const button of [1,2]){
    const gesture=createGlobeCellSelection();
    gesture.down(pointer({button}));
    assert.equal(gesture.up(pointer({button})),false);
  }
});

test('orbiting away and back to the original pixel does not become a cell click',()=>{
  const gesture=createGlobeCellSelection();
  gesture.down(pointer());
  gesture.move(pointer({clientX:180}));
  gesture.move(pointer());
  assert.equal(gesture.up(pointer()),false);
  gesture.down(pointer());
  assert.equal(gesture.up(pointer()),true,'the next intentional tap still works');
});

test('a two-finger gesture cannot select on either release, in either release order',()=>{
  for(const primaryFirst of [true,false]){
    const gesture=createGlobeCellSelection();
    const first=pointer(),second=pointer({pointerId:2,clientX:140,isPrimary:false});
    gesture.down(first);gesture.down(second);
    for(const released of primaryFirst?[first,second]:[second,first])assert.equal(gesture.up(released),false);
    gesture.down(first);
    assert.equal(gesture.up(first),true,'a completed pinch must not block later taps');
  }
});

test('cancelled pointers and window-focus loss cannot leave a pending selection',()=>{
  const gesture=createGlobeCellSelection();
  gesture.down(pointer());gesture.cancel(pointer());
  assert.equal(gesture.up(pointer()),false);
  gesture.down(pointer());gesture.reset();
  assert.equal(gesture.up(pointer()),false);
  gesture.down(pointer({pointerId:3}));
  assert.equal(gesture.up(pointer({pointerId:3})),true);
});

test('unmatched document releases do not select or interrupt a valid canvas tap',()=>{
  const gesture=createGlobeCellSelection();
  assert.equal(gesture.up(pointer()),false);
  gesture.down(pointer());
  assert.equal(gesture.up(pointer({pointerId:9})),false);
  assert.equal(gesture.up(pointer()),true);
  gesture.down(pointer({isPrimary:false}));
  assert.equal(gesture.up(pointer({isPrimary:false})),false);
});
