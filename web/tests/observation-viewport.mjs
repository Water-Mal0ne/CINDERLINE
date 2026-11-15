import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';

const require=createRequire(new URL('../package.json',import.meta.url));
const ts=require('typescript'),module={exports:{}};
const source=readFileSync(new URL('../src/observationViewport.ts',import.meta.url),'utf8');
vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.CommonJS}}).outputText,{module,exports:module.exports});
const {surfaceView,angularSeparation,tileIntersectsView,pointInView,boundedObservationZoom,OBSERVATION_MIN_DISTANCE}=module.exports;
const rad=Math.PI/180;
const point=(lat,lon)=>[Math.cos(lat*rad)*Math.sin(lon*rad),Math.sin(lat*rad),Math.cos(lat*rad)*Math.cos(lon*rad)];
const dot=(a,b)=>a.reduce((n,v,i)=>n+v*b[i],0);

// Independently project surface samples through a camera basis. This does not
// reproduce the helper's diagonal-ray/spherical-cap calculation.
function projectsInside(lat,lon,cameraLat,cameraLon,distance,fov,aspect){
  const p=point(lat,lon),normal=point(cameraLat,cameraLon),camera=normal.map(v=>v*distance);
  if(dot(p,camera)<1-1e-12)return false; // occluded by the sphere
  const right=[Math.cos(cameraLon*rad),0,-Math.sin(cameraLon*rad)];
  const up=[-Math.sin(cameraLat*rad)*Math.sin(cameraLon*rad),Math.cos(cameraLat*rad),-Math.sin(cameraLat*rad)*Math.cos(cameraLon*rad)];
  const relative=p.map((v,i)=>v-camera[i]),depth=-dot(relative,normal);
  if(depth<=0)return false;
  const halfHeight=depth*Math.tan(fov*rad/2);
  return Math.abs(dot(relative,up))<=halfHeight+1e-12&&Math.abs(dot(relative,right))<=halfHeight*aspect+1e-12;
}

test('observation cap includes independently projected surface points at close, regional and global zoom',()=>{
  for(const [cameraLat,cameraLon] of [[0,0],[28,84],[-33,151],[65,179.8],[89.5,-35]]){
    for(const distance of [OBSERVATION_MIN_DISTANCE,1.012,1.055,1.2,3.4]){
      for(const aspect of [.35,.75,1,2.8]){
        const [x,y,z]=point(cameraLat,cameraLon).map(v=>v*distance);
        const view=surfaceView(x,y,z,39,aspect);
        let visible=0;
        // Dense local samples exercise the very small near-surface viewport;
        // broader samples check limb/horizon cases without assuming its radius.
        for(const span of [.08,.8,8,80]){
          for(let a=-8;a<=8;a++)for(let b=-8;b<=8;b++){
            const lat=Math.max(-90,Math.min(90,cameraLat+a*span/8));
            const lon=((cameraLon+b*span/8+540)%360)-180;
            if(!projectsInside(lat,lon,cameraLat,cameraLon,distance,39,aspect))continue;
            visible++;
            assert.ok(pointInView(lat,lon,view),`viewport omitted ${lat},${lon} from camera ${cameraLat},${cameraLon}, distance${distance}, aspect${aspect}`);
          }
        }
        assert.ok(visible>0,'camera centre is represented');
        assert.ok(Number.isFinite(view.radiusDegrees)&&view.radiusDegrees>0&&view.radiusDegrees<90);
      }
    }
  }
});

test('view cap retrieves adjacent storage tiles across the antimeridian without selecting the far side',()=>{
  const [x,y,z]=point(0,179.99).map(v=>v*1.012),view=surfaceView(x,y,z,39,1);
  assert.ok(tileIntersectsView([178,-2,180,0],view));
  assert.ok(tileIntersectsView([-180,0,-178,2],view));
  assert.equal(tileIntersectsView([-2,-2,0,0],view),false);
  assert.ok(pointInView(0,-179.99,view));
  assert.equal(pointInView(0,0,view),false);
  assert.ok(Math.abs(angularSeparation(0,179.9,0,-179.9)-.2)<1e-9);
});

test('polar tiles and edge-containing tiles are conservatively included',()=>{
  const polar=surfaceView(0,1.012,0,39,.4);
  for(const west of [-180,-90,0,90,178])assert.ok(tileIntersectsView([west,88,west+2,90],polar));
  const [x,y,z]=point(28,84).map(v=>v*1.055),view=surfaceView(x,y,z,39,1.8);
  for(let south=22;south<=34;south+=2)for(let west=78;west<=90;west+=2){
    const bounds=[west,south,west+2,south+2];
    const samples=[[south,west],[south+2,west],[south,west+2],[south+2,west+2],[south+1,west+1]];
    if(samples.some(([lat,lon])=>pointInView(lat,lon,view)))assert.ok(tileIntersectsView(bounds,view),`edge tile omitted ${bounds}`);
  }
});

test('zoom uses altitude and remains outside Earth after repeated phone-sized steps',()=>{
  let distance=3.4;
  for(let i=0;i<200;i++){
    const next=boundedObservationZoom(distance,.85,6);
    assert.ok(Number.isFinite(next)&&next>=OBSERVATION_MIN_DISTANCE&&next<=distance);
    distance=next;
  }
  assert.equal(distance,OBSERVATION_MIN_DISTANCE);
  for(let i=0;i<200;i++)distance=boundedObservationZoom(distance,1.2,6);
  assert.equal(distance,6);
  assert.ok(Math.abs(boundedObservationZoom(1.1,.5,6)-1.05)<1e-12);
});

test('malformed camera or zoom inputs fail rather than create NaN or inside-Earth positions',()=>{
  for(const args of [[0,0,1,39,1],[0,0,0,39,1],[NaN,0,3,39,1],[0,0,3,0,1],[0,0,3,180,1],[0,0,3,39,0],[0,0,3,39,Infinity]])
    assert.throws(()=>surfaceView(...args),/Invalid observation camera/);
  for(const args of [[NaN,.85,6],[1.1,0,6],[1.1,-1,6],[1.1,.85,NaN],[1.1,.85,Infinity],[1.1,.85,1]])
    assert.throws(()=>boundedObservationZoom(...args),/Invalid zoom/);
});
