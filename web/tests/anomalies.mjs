import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';

// Compile the actual pure selectors exported by the component, without a browser.
const source = fs.readFileSync(new URL('../src/AnomalyPanel.tsx', import.meta.url), 'utf8');
const ast = ts.createSourceFile('AnomalyPanel.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const selectors = ast.statements.filter(node => ts.isFunctionDeclaration(node) && ['anomalyDirection','selectAnomalies'].includes(node.name?.text)).map(node => node.getText(ast)).join('\n');
const compiled = ts.transpileModule(selectors, {compilerOptions:{target:ts.ScriptTarget.ES2021,module:ts.ModuleKind.ES2022}}).outputText;
const {anomalyDirection, selectAnomalies} = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));
const rows = [
  {date:'2020-01-01',week:1,value:500,z_score:null,status:'high'},
  {date:'2021-01-01',week:1,value:30,z_score:-4,status:'low'},
  {date:'2022-01-01',week:1,value:400,z_score:2,status:'high'},
  {date:'2023-01-01',week:1,value:0,z_score:0,status:'low'},
  {date:'2024-01-01',week:1,value:600,z_score:NaN,status:'high'},
];
const originalOrder = rows.map(row => row.date);
assert.equal(anomalyDirection({...rows[0],status:'HIGH'}),'high');
assert.equal(anomalyDirection({...rows[0],status:'unknown'}),'other');
assert.deepEqual(selectAnomalies(rows,'all','strongest').map(row => row.date), ['2021-01-01','2022-01-01','2023-01-01','2024-01-01','2020-01-01']);
assert.deepEqual(selectAnomalies(rows,'high','latest').map(row => row.date), ['2024-01-01','2022-01-01','2020-01-01']);
assert.deepEqual(selectAnomalies(rows,'low','oldest').map(row => row.date), ['2021-01-01','2023-01-01']);
assert.deepEqual(selectAnomalies([], 'all', 'strongest'), []);
assert.deepEqual(rows.map(row => row.date), originalOrder, 'Sorting must not mutate parent data');
console.log('PASS: anomaly severity filters, chronological order, absolute-z ranking, missing-z placement and immutable input.');
