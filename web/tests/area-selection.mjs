import assert from 'node:assert/strict';
import {test} from 'node:test';
import {existsSync, readFileSync, readdirSync, statSync} from 'node:fs';
import {createRequire} from 'node:module';
const require = createRequire(new URL('../package.json', import.meta.url)), ts = require('typescript');
const compile = name => ts.transpileModule(readFileSync(new URL('../src/' + name, import.meta.url), 'utf8'), {
  compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.ES2022},
}).outputText;
const dataUrl = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const area = await import(dataUrl(compile('areaSelection.ts')));
const utilsUrl = dataUrl(compile('utils.ts'));
const stats = await import(dataUrl(compile('monthStats.ts').replace("'./utils'", JSON.stringify(utilsUrl))));

const payload = {label: 'TEST', country: 'X', model: 'B1', reference: 'MODIS Aqua', first_month: '2003-01', months: 24, grid: .25,
  unit: 'tenths', switch: '2013-01', outage_months: ['2004-07'], note: area.AREA_NOTE,
  lat: [10.125, 10.375, 20.125], lon: [80.125, 80.125, 85.125],
  series: [[0, 10, 2, 25], [2, 5], [23, 1000]]};

test('payload validation rejects malformed area files', () => {
  assert.ok(area.validPayload(payload));
  assert.equal(area.validPayload({...payload, lat: [1]}), false);
  assert.equal(area.validPayload({...payload, first_month: '2003'}), false);
  assert.equal(area.validPayload(null), false);
});

test('rectangle and radius select cells by centre; sums decode sparse tenths', () => {
  assert.deepEqual(area.selectCells(payload, {kind: 'rect', rect: {south: 10, north: 10.5, west: 80, east: 80.5}}), [0, 1]);
  assert.deepEqual(area.selectCells(payload, {kind: 'circle', circle: {lat: 10.125, lon: 80.125, km: 20}}), [0]);
  assert.deepEqual(area.selectCells(payload, {kind: 'circle', circle: {lat: 10.125, lon: 80.125, km: 40}}), [0, 1]);
  const total = area.sumSeries(payload, [0, 1]);
  assert.equal(total.length, 24);
  assert.equal(total[0], 1);
  assert.equal(total[2], 3);
  assert.equal(total[1], 0);
  assert.equal(area.sumSeries(payload, [2])[23], 100);
});

test('haversine distance and typed-input validation', () => {
  assert.ok(Math.abs(area.haversineKm(0, 0, 0, 1) - 111.195) < .01);
  assert.equal(area.circleError('27.7', '85.3', '25'), null);
  assert.match(area.circleError('', '85.3', '25'), /numbers/);
  assert.match(area.circleError('95', '85.3', '25'), /Latitude/);
  assert.match(area.circleError('27', '190', '25'), /Longitude/);
  assert.match(area.circleError('27', '85', '0'), /Radius/);
  assert.match(area.describeSelection({kind: 'circle', circle: {lat: 27.7, lon: 85.3, km: 25}}), /25 km around 27\.700, 85\.300/);
});

test('area months feed the month calendar; outage months stay no observation, not zero', () => {
  const m = stats.monthMatrixFromMonthly(area.sumSeries(payload, [0, 1, 2]), 2003, payload.outage_months, 'harmonized');
  assert.equal(m.cells.get('2003-01').value, 1);
  assert.equal(m.cells.get('2004-07').status, 'no-observation');
  assert.equal(m.cells.get('2004-07').value, null);
  assert.equal(m.cells.get('2004-12').value, 100);
  assert.equal(m.busiestMonth.key, '2004-12');
  assert.equal(m.busiestYear.year, 2003, '2004 contains an outage month and is not ranked');
});

const dir = new URL('../public/data/area/', import.meta.url);
test('published area files: valid, under 25 MiB each, and carry the calibration note', {skip: !existsSync(dir)}, () => {
  const files = readdirSync(dir).filter(f => f.endsWith('.json'));
  assert.equal(files.length, 7);
  for (const f of files) {
    const size = statSync(new URL(f, dir)).size;
    assert.ok(size < 25 * 2 ** 20, `${f} is ${size} bytes`);
    const p = JSON.parse(readFileSync(new URL(f, dir), 'utf8'));
    assert.ok(area.validPayload(p), f);
    assert.equal(p.note, area.AREA_NOTE);
    assert.equal(p.months, 264);
    assert.ok(p.series.every(s => s.length % 2 === 0 && s.every(Number.isInteger)), f);
  }
});
