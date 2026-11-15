import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';

const require=createRequire(new URL('../package.json',import.meta.url));
const ts=require('typescript'),module={exports:{}};
const source=readFileSync(new URL('../src/globeViewport.ts',import.meta.url),'utf8');
vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.CommonJS}}).outputText,{module,exports:module.exports});
const {globeOverviewDistance}=module.exports;

test('global framing contains the Earth and annual layer in portrait and landscape viewports',()=>{
  const radius=1.007,fov=39,vertical=fov*Math.PI/360;
  for(const [width,height] of [[300,320],[300,880],[768,440],[1180,440],[440,440]]){
    const aspect=width/height,distance=globeOverviewDistance(fov,aspect);
    // A sphere subtends asin(radius/distance), not atan(radius/distance).
    const angularRadius=Math.asin(radius/distance);
    assert.ok(angularRadius<vertical,`${width}×${height}: vertical field contains sphere`);
    assert.ok(angularRadius<Math.atan(Math.tan(vertical)*aspect),`${width}×${height}: horizontal field contains sphere`);
  }
});

test('portrait framing retreats as the viewport narrows; landscape height limits the fit',()=>{
  assert.ok(globeOverviewDistance(39,.4)>globeOverviewDistance(39,.8));
  assert.ok(globeOverviewDistance(39,.8)>globeOverviewDistance(39,1));
  assert.equal(globeOverviewDistance(39,1),globeOverviewDistance(39,2));
});
