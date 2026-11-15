import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import ts from 'typescript';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

// Render the actual component, preserving its JSX, hooks, formatting and icons.
// Ignore only styles; React comes from the same loader used by the renderer.
const require=createRequire(import.meta.url);
function compile(filename,dependencies={}){
  const source=readFileSync(new URL(`../src/${filename}`,import.meta.url),'utf8');
  const output=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  const compiled={exports:{}};
  const load=name=>name.endsWith('.css')?{}:Object.hasOwn(dependencies,name)?dependencies[name]:require(name);
  new Function('require','module','exports',output)(load,compiled,compiled.exports);
  return compiled.exports;
}
const SeasonalContext=compile('SeasonalContext.tsx',{'./utils':compile('utils.ts')}).default;
const index=JSON.parse(readFileSync(new URL('../public/data/index.json',import.meta.url),'utf8'));

test('all seven extended calendars retain the frozen baseline label while the date guide shows 2025',()=>{
  for(const item of index.regions){
    const region=JSON.parse(readFileSync(new URL(`../public/data/${item.file}`,import.meta.url),'utf8'));
    assert.equal(region.meta.period_end,'2025-12-31');
    assert.match(region.meta.extension_note,/remain based on 2003-2024/);
    const before=JSON.stringify([region.weekly_climatology,region.anomalies,region.critical_periods]);
    const html=renderToStaticMarkup(React.createElement(SeasonalContext,{region,label:region.meta.label,selectedYear:2025,cell:'ALL',onExport:()=>{}}));
    assert.match(html,/National baseline · 2003–2024/);
    assert.doesNotMatch(html,/National baseline · 2003–2025/);
    assert.match(html,/2025 DATE GUIDE/);
    assert.equal(JSON.stringify([region.weekly_climatology,region.anomalies,region.critical_periods]),before);
  }
});

test('changing date-guide year or selected cell does not relabel the climatology period',()=>{
  const region=JSON.parse(readFileSync(new URL('../public/data/Nepal.json',import.meta.url),'utf8'));
  const html=renderToStaticMarkup(React.createElement(SeasonalContext,{region,label:region.meta.label,selectedYear:2015,cell:'27.75:85.25',onExport:()=>{}}));
  assert.match(html,/National baseline · 2003–2024/);
  assert.match(html,/2015 DATE GUIDE/);
  assert.match(html,/national patterns/);
});
