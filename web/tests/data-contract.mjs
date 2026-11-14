import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';

// Exercise the actual exported client data helpers, including calendar-year edges.
const source = fs.readFileSync(new URL('../src/utils.ts', import.meta.url), 'utf8');
const output = ts.transpileModule(source, {compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const utils = await import('data:text/javascript;base64,' + Buffer.from(output).toString('base64'));
assert.deepEqual(utils.isoWeek('2020-12-31'), {year:2020,week:53});
assert.deepEqual(utils.isoWeek('2021-01-01'), {year:2021,week:1});
assert.deepEqual(utils.isoWeek('2024-01-08'), {year:2024,week:2});
assert.equal(utils.weekStart(2024,53),'2024-12-30');
assert.equal(utils.weekStart(2024,54),'2025-01-01');
assert.equal(utils.sum([null,undefined,NaN]),null);
assert.equal(utils.sum([0,null,2]),2);

const rows = [{date:'2020-12-31',harmonized:null,raw:null},{date:'2021-01-01',harmonized:4,raw:9}];
const weeks = utils.aggregateWeeks(rows);
assert.equal(weeks.length,2);
assert.equal(weeks[0].harmonized,null);
assert.equal(weeks[1].year,2021);
assert.equal(weeks[1].harmonized,4);

const historical={date:'2009-01-01',raw:8,raw_aqua:8,raw_viirs:500,harmonized:8,source:'observed Aqua'};
const paired={date:'2019-01-01',raw:100,raw_aqua:9,raw_viirs:100,harmonized:11,source:'converted VIIRS'};
const missingReference={...paired,date:'2019-01-02',raw_aqua:null,harmonized:900};
const example=utils.comparisonWeek(utils.aggregateWeeks([historical,paired,missingReference]));
assert.equal(example.week.year,2019);
assert.equal(example.paired.length,1);
assert.equal(example.converted,11);
assert.equal(example.aqua,9);
assert.equal(utils.comparisonWeek(utils.aggregateWeeks([historical])),null);
const month=utils.monthly([paired,missingReference])[0];
assert.equal(month.aqua,9);
assert.equal(month.aquaDays,1);
assert.equal(month.harmonizedDays,2);
assert.deepEqual(utils.sourcePeriods([paired,historical]),{observed:{start:'2009-01-01',end:'2009-01-01'},converted:{start:'2019-01-01',end:'2019-01-01'}});
assert.equal(utils.geoCoordinate(-99,'lon'),'99.0° W');
const loaderSource=fs.readFileSync(new URL('../src/loadData.ts',import.meta.url),'utf8');
const loaderOutput=ts.transpileModule(loaderSource,{compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const loader=await import('data:text/javascript;base64,'+Buffer.from(loaderOutput).toString('base64'));
assert.deepEqual(loader.decodeCell({columns:['date','harmonized','source'],rows:[['2009-01-01',null,'observed Aqua']]}),[{date:'2009-01-01',harmonized:null,source:'observed Aqua'}]);
assert.deepEqual(loader.decodeCell({daily:[paired]}),[paired]);
assert.throws(()=>loader.decodeCell({}),/Invalid cell/);
const encoded={encoding:'column-dictionary-v1',columns:['date','harmonized','source'],
  rows:[['2020-01-01',0,0],['2020-01-02',1,1],['2020-01-03',2,0]],
  dictionaries:{harmonized:[null,0,1.23456789012345],source:['observed Aqua','converted VIIRS']}};
const decoded=[{date:'2020-01-01',harmonized:null,source:'observed Aqua'},
  {date:'2020-01-02',harmonized:0,source:'converted VIIRS'},
  {date:'2020-01-03',harmonized:1.23456789012345,source:'observed Aqua'}];
assert.deepEqual(loader.decodeCell(encoded),decoded);
assert.deepEqual(loader.normalizePublishedData({meta:{region:'Nepal'},daily_compact:encoded}),{meta:{region:'Nepal'},daily:decoded});
assert.throws(()=>loader.normalizePublishedData({daily:[],daily_compact:encoded}),/Ambiguous/);
assert.throws(()=>loader.decodeCell({...encoded,encoding:'future'}),/encoding/);
assert.throws(()=>loader.decodeCell({...encoded,encoding:undefined}),/encoding/);
for(const bad of [-1,3,.5,null,'0'])assert.throws(()=>loader.decodeCell({...encoded,rows:[['2020-01-01',bad,0]]}),/dictionary index/);
assert.throws(()=>loader.decodeCell({...encoded,rows:[['2020-01-01']]}),/row/);
assert.throws(()=>loader.decodeCell({...encoded,columns:['date','date','source']}),/columns/);

let captured;
const originalURL = URL.createObjectURL;
URL.createObjectURL = (blob) => {captured=blob;return 'blob:test';};
URL.revokeObjectURL = () => {};
global.document = {createElement:()=>({click(){},remove(){}}),body:{appendChild(){}}};
utils.exportICS([{start_week:53,end_week:53,label:'Historical high activity'}],2024,'Nepal','SYNTHETIC DATA');
const ics = await captured.text();
assert.ok(ics.includes('DTSTART;VALUE=DATE:20241230'));
assert.ok(ics.includes('DTEND;VALUE=DATE:20250101'));
assert.ok(ics.includes('SYNTHETIC DATA'));
assert.ok(ics.includes('not a forecast'));
utils.exportCSV([{date:'2021-01-01',harmonized:null,source:'Source "A"'}],'Nepal','SYNTHETIC DATA');
const csv = await captured.text();
assert.ok(csv.includes('"Source ""A"""'));
assert.ok(csv.includes('"SYNTHETIC DATA"'));
URL.createObjectURL = originalURL;
console.log('PASS: calendar boundaries, paired comparisons, source provenance, lazy cell formats, missing values, CSV and ICS exports.');
