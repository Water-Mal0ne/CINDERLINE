import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../package.json',import.meta.url)),ts=require('typescript');
const source=ts.transpileModule(readFileSync(new URL('../src/comparisonExport.ts',import.meta.url),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const {buildMonthlyExport}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const points=[{date:'2020-09',raw:134,harmonized:19.43175,aqua:13,days:1,rawDays:1,harmonizedDays:1,aquaDays:1}];
const scope={regionId:'United_States',regionName:'United States',cellId:'40.75:-123.50',label:'REAL FIRMS DATA'};

test('monthly exports retain country, cell, precision and available-day counts after renaming',()=>{
  const result=buildMonthlyExport(points,scope);
  assert.equal(result.filename,'CINDERLINE_United_States_cell_40.75_-123.50_2020-09_2020-09_monthly.csv');
  assert.equal(result.content,'\uFEFFregion,region_name,cell_id,month,raw_sensor_switch_detections,aqua_equivalent_detections,observed_aqua_detections,raw_days,harmonized_days,aqua_days,data_label\r\n"United_States","United States","40.75:-123.50","2020-09","134","19.43175","13","1","1","1","REAL FIRMS DATA"');
});

test('whole-region exports are distinct from cells and preserve null versus recorded zero',()=>{
  const result=buildMonthlyExport([{...points[0],raw:null,harmonized:0,aqua:null,rawDays:0,aquaDays:0}],{...scope,cellId:'ALL'});
  assert.match(result.filename,/_whole-region_/);
  assert.ok(result.content.includes('"ALL","2020-09","","0","","0","1","0"'));
});

test('CSV quotes embedded commas and quotation marks without altering identity',()=>{
  const result=buildMonthlyExport(points,{...scope,regionName:'Country, "example"'});
  assert.ok(result.content.includes('"Country, ""example"""'));
  assert.equal(buildMonthlyExport([],{...scope,cellId:'ALL'}).content.split('\r\n').length,1);
});
