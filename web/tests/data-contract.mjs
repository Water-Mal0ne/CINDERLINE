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
console.log('PASS: calendar boundaries, missing values, grouped totals, CSV provenance, ICS year-end boundaries.');
