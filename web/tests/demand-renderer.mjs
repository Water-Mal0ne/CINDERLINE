import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';

const source=fs.readFileSync(new URL('../src/demandRenderer.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const {createDemandRenderer}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));

function harness(draw=()=>false){
  let id=0,draws=0;
  const frames=new Map();
  const loop=createDemandRenderer(()=>{draws++;return draw();},callback=>{frames.set(++id,callback);return id;},key=>frames.delete(key));
  const next=()=>{assert.equal(frames.size,1,'Only one frame may be queued');const [key,callback]=frames.entries().next().value;frames.delete(key);callback();};
  return {loop,frames,next,get draws(){return draws;}};
}

// Invisible work remains dormant, and repeated changes coalesce into one visible draw.
const idle=harness();
idle.loop.invalidate();idle.loop.invalidate();assert.equal(idle.frames.size,0);
idle.loop.setActive(true);idle.loop.invalidate();idle.loop.invalidate();idle.next();
assert.equal(idle.draws,1);assert.equal(idle.frames.size,0,'An idle globe must stop scheduling frames');
idle.loop.invalidate();idle.next();assert.equal(idle.draws,2);

// Simulate damping: render each changed camera frame, then stop after settling.
let remaining=3;
const damping=harness(()=>remaining-->0);
damping.loop.setActive(true);
for(let i=0;i<4;i++)damping.next();
assert.equal(damping.draws,4);assert.equal(damping.frames.size,0);

// Leaving the viewport or hiding the page cancels pending work; returning draws fresh data.
const hidden=harness();hidden.loop.setActive(true);hidden.loop.setActive(false);
assert.equal(hidden.frames.size,0);hidden.loop.invalidate();assert.equal(hidden.frames.size,0);
hidden.loop.setActive(true);hidden.next();assert.equal(hidden.draws,1);

// OrbitControls may invalidate synchronously inside draw(); the request must not be lost.
let first=true,reentrant;
reentrant=harness(()=>{if(first){first=false;reentrant.loop.invalidate();}return false;});
reentrant.loop.setActive(true);reentrant.next();reentrant.next();
assert.equal(reentrant.draws,2);assert.equal(reentrant.frames.size,0);

// Unmount and graphics-loss cleanup prevent queued or late callbacks from drawing.
const disposed=harness();disposed.loop.setActive(true);
const late=disposed.frames.values().next().value;
disposed.loop.dispose();assert.equal(disposed.frames.size,0);late();
disposed.loop.invalidate();disposed.loop.setActive(true);
assert.equal(disposed.draws,0);assert.equal(disposed.frames.size,0);
console.log('PASS: demand rendering sleeps idle/offscreen, coalesces changes, preserves damping, resumes and disposes safely.');
