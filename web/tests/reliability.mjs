import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const source = readFileSync(new URL('../src/reliability.ts', import.meta.url), 'utf8');
const output = ts.transpileModule(source, {compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.ES2022}}).outputText;
const {selectedConversion, nationalEvaluation, recordAvailability, includesUnevaluatedYears} = await import('data:text/javascript;base64,' + Buffer.from(output).toString('base64'));
const daily = (date, value, extra = {}) => ({date, harmonized: value, raw: value, raw_aqua: value, raw_terra: value, raw_viirs: value, lo: value, hi: value, model: 'Aqua', source: 'Observed Aqua', coverage: 'Observation exposure unknown', ...extra});
const evaluation = (extra = {}) => ({region: 'Nepal', model: 'M1', split: 'test', aggregation: 'weekly', bias_pct: -8, mae: 11, correlation: 0.97, peak_week_error: 1, ...extra});

test('national evaluation binds country, selected conversion, split and weekly scale', () => {
  const wanted = evaluation();
  const rows = [evaluation({region: 'India'}), evaluation({split: 'validation'}), evaluation({aggregation: 'monthly'}), evaluation({model: 'B1'}), wanted];
  assert.equal(nationalEvaluation(rows, 'Aqua reference / M1', 'Nepal'), wanted);
  assert.equal(nationalEvaluation(rows, 'Aqua reference / M1', 'Egypt'), null);
  assert.equal(nationalEvaluation(rows, 'Aqua reference / B1', undefined), null);
  assert.equal(nationalEvaluation([...rows, wanted], 'M1', 'Nepal'), null);
});

test('ambiguous or unknown calibration labels do not invent a selected model', () => {
  assert.equal(selectedConversion('Aqua reference / B1'), 'B1');
  assert.equal(selectedConversion('M1 / M1'), 'M1');
  for (const value of [undefined, '', 'B0', 'B10', 'M10', 'B1 versus M1', 'Aqua observations']) {
    assert.equal(selectedConversion(value), null, String(value));
  }
});

test('all actual national notices resolve exactly the existing frozen weekly test row', () => {
  const index = JSON.parse(readFileSync(new URL('../public/data/index.json', import.meta.url), 'utf8'));
  for (const item of index.regions) {
    const region = JSON.parse(readFileSync(new URL(`../public/data/${item.file}`, import.meta.url), 'utf8'));
    const result = nationalEvaluation(region.eval, region.meta.model, region.meta.region);
    assert.ok(result, region.meta.name);
    assert.equal(result.region, item.id);
    assert.equal(result.split, 'test');
    assert.equal(result.aggregation, 'weekly');
    assert.equal(result.model, selectedConversion(region.meta.model));
  }
});

test('availability distinguishes leap-day missing values, absent dates and recorded zero', () => {
  const result = recordAvailability([daily('2024-02-28', 0), daily('2024-02-29', null), daily('2024-03-01', 5)], '2024-02-27', '2024-03-01');
  assert.equal(result.expectedDays, 4);
  assert.equal(result.recordDays, 3);
  assert.equal(result.availableDays, 2);
  assert.equal(result.unavailableDays, 1);
  assert.equal(result.zeroDays, 1);
  assert.equal(result.missingDays, 1);
});

test('range filters are inclusive and do not borrow observations from adjacent years', () => {
  const rows = [daily('2023-12-31', 1), daily('2024-01-01', 2), daily('2024-12-31', 3), daily('2025-01-01', 4)];
  const result = recordAvailability(rows, '2024-01-01', '2024-12-31');
  assert.equal(result.expectedDays, 366);
  assert.equal(result.availableDays, 2);
  assert.equal(result.missingDays, 364);
});

test('unknown daily support is not converted into zero coverage or a full year', () => {
  const absent = recordAvailability(undefined, '2025-01-01', '2025-12-31');
  assert.equal(absent.status, 'not-supplied');
  assert.equal(absent.expectedDays, null);
  const empty = recordAvailability([], '2025-01-01', '2025-12-31');
  assert.equal(empty.status, 'known');
  assert.equal(empty.availableDays, 0);
  assert.equal(empty.missingDays, 365);
  assert.equal(recordAvailability([]).expectedDays, null);
});

test('invalid civil dates and reversed bounds do not produce misleading availability', () => {
  for (const bounds of [['2023-02-29', '2023-03-01'], ['2024-03-01', '2024-02-29'], ['', '2024-12-31']]) {
    assert.equal(recordAvailability([], ...bounds).status, 'invalid-range');
  }
  const result = recordAvailability([daily('2023-02-29', 7), daily('2023-03-01', 3)], '2023-03-01', '2023-03-01');
  assert.equal(result.invalidDateRows, 1);
  assert.equal(result.availableDays, 1);
});

test('duplicates cannot inflate daily coverage and conflicting values are unavailable', () => {
  const rows = Object.freeze([Object.freeze(daily('2024-01-01', 0)), Object.freeze(daily('2024-01-01', 0)), Object.freeze(daily('2024-01-02', 5)), Object.freeze(daily('2024-01-02', null))]);
  const result = recordAvailability(rows, '2024-01-01', '2024-01-02');
  assert.equal(result.recordDays, 2);
  assert.equal(result.availableDays, 1);
  assert.equal(result.zeroDays, 1);
  assert.equal(result.duplicateDays, 2);
  assert.equal(result.conflictingDays, 1);
  assert.equal(result.unavailableDays, 1);
});

test('calibration interval availability applies to converted dates only', () => {
  const rows = [daily('2024-01-01', 2, {lo: null, hi: null}), daily('2024-01-02', 3, {source: 'Converted VIIRS S-NPP', lo: null, hi: null}), daily('2024-01-03', 0, {source: 'Converted VIIRS S-NPP', lo: 0, hi: 0}), daily('2024-01-04', 1, {source: 'Converted VIIRS S-NPP', lo: 2, hi: 1})];
  const result = recordAvailability(rows);
  assert.equal(result.convertedDays, 3);
  assert.equal(result.missingIntervalDays, 2);
  assert.equal(result.zeroDays, 1);
  assert.equal(recordAvailability(rows, undefined, undefined, 'raw').convertedDays, 0);
});

test('only finite nonnegative values count as available in the displayed scale', () => {
  const rows = [daily('2024-01-01', NaN), daily('2024-01-02', Infinity), daily('2024-01-03', -1), daily('2024-01-04', 0, {raw: null})];
  assert.equal(recordAvailability(rows).availableDays, 1);
  assert.equal(recordAvailability(rows, undefined, undefined, 'raw').availableDays, 0);
});

test('the later-data disclosure starts after the frozen test end, not at training years', () => {
  assert.equal(includesUnevaluatedYears('2003-01-01', '2024-12-31'), false);
  assert.equal(includesUnevaluatedYears('2024-12-31', '2025-01-01'), true);
  assert.equal(includesUnevaluatedYears('2025-01-01', '2025-12-31'), true);
  assert.equal(includesUnevaluatedYears(undefined, '2025-01-01'), true);
  assert.equal(includesUnevaluatedYears('2025-12-31', '2025-01-01'), false);
  assert.equal(includesUnevaluatedYears('2025-02-29', '2025-03-01'), false);
  assert.equal(includesUnevaluatedYears(), false);
});
