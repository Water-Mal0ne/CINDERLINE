import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require = createRequire(new URL('../package.json', import.meta.url)), ts = require('typescript');
const compile = name => ts.transpileModule(readFileSync(new URL('../src/' + name, import.meta.url), 'utf8'), {
  compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.ES2022},
}).outputText;
const dataUrl = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const utilsUrl = dataUrl(compile('utils.ts'));
const stats = await import(dataUrl(compile('monthStats.ts').replace("'./utils'", JSON.stringify(utilsUrl))));
const coverageUrl = dataUrl(compile('calendarView.ts').replace("'./explorationState'", JSON.stringify(dataUrl(compile('explorationState.ts')))));
const {buildEvidenceBrief} = await import(dataUrl(compile('evidenceBrief.ts').replace("'./utils'", JSON.stringify(utilsUrl)).replace("'./calendarView'", JSON.stringify(coverageUrl))));
const {aggregateWeeks} = await import(utilsUrl);
const {normalizePublishedData} = await import(dataUrl(compile('loadData.ts')));
const nepal = normalizePublishedData(JSON.parse(readFileSync(new URL('../public/data/Nepal.json', import.meta.url), 'utf8')));

function days(year, month, value, extra = {}) {
  const n = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return Array.from({length: n}, (_, i) => ({date: `${year}-${String(month).padStart(2, '0')}-${String(i + 1).padStart(2, '0')}`,
    raw: value * 2, harmonized: value, source: 'converted VIIRS', ...extra}));
}

test('months sum published daily values; an outage day marks the whole month as no observation, not zero', () => {
  const rows = [...days(2020, 1, 1), ...days(2020, 2, 2)];
  rows.find(r => r.date === '2020-02-10').source = 'no observation';
  rows.find(r => r.date === '2020-02-10').harmonized = null;
  const m = stats.monthMatrix(rows, 'harmonized');
  assert.equal(m.cells.get('2020-01').value, 31);
  assert.equal(m.cells.get('2020-01').status, 'ok');
  assert.equal(m.cells.get('2020-02').value, null);
  assert.equal(m.cells.get('2020-02').status, 'no-observation');
  assert.equal(stats.monthMatrix(rows, 'raw').cells.get('2020-01').value, 62);
});

test('partial and empty months are flagged and never highlighted or used as history', () => {
  const rows = [...days(2019, 3, 5).slice(0, 10), ...days(2019, 4, 1), ...days(2019, 5, 0).map(r => ({...r, harmonized: null}))];
  const m = stats.monthMatrix(rows, 'harmonized');
  assert.equal(m.cells.get('2019-03').status, 'partial');
  assert.equal(m.cells.get('2019-05').status, 'missing');
  assert.equal(m.busiestMonth.key, '2019-04');
  assert.equal(m.busiestYear, null, 'a year without 12 observed months is not ranked');
});

test('busiest month and busiest fully observed year; history uses other years only', () => {
  const rows = [];
  for (const [year, scale] of [[2015, 1], [2016, 2], [2017, 3], [2018, 4], [2019, 10]]) for (let month = 1; month <= 12; month++) rows.push(...days(year, month, scale * (month === 3 ? 5 : 1)));
  rows.find(r => r.date === '2019-07-04').source = 'no observation';
  const m = stats.monthMatrix(rows, 'harmonized');
  assert.equal(m.busiestMonth.key, '2019-03');
  assert.equal(m.busiestYear.year, 2018, '2019 has an outage month, so it is not ranked as a full year');
  const h = stats.monthHistory(m, 2016, 3);
  assert.equal(h.years, 4);
  assert.equal(h.median, stats.percentile([31 * 5, 31 * 15, 31 * 20, 31 * 50], .5));
  assert.equal(h.p10, stats.percentile([155, 465, 620, 1550], .1));
  assert.match(h.relation, /Within|Below|Above/);
  assert.match(stats.monthHistory(m, 2019, 7).relation, /No observation/);
  assert.equal(stats.percentile([1, 2, 3, 4], .5), 2.5);
  assert.equal(stats.percentile([10, 20], .1), 11);
});

test('colour bins cover the ramp and the legend edges start at zero', () => {
  assert.equal(stats.RAMP.length, 7);
  assert.equal(stats.colorBin(0, 100), 0);
  assert.equal(stats.colorBin(100, 100), 6);
  assert.deepEqual(stats.binEdges(36).slice(0, 2), [0, 1]);
});

test('real Nepal data: 2022 S-NPP outage months are marked, history and CSV are complete', () => {
  const m = stats.monthMatrix(nepal.daily, 'harmonized');
  assert.equal(m.years[0], 2003);
  assert.equal(m.years.at(-1), Number(nepal.meta.period_end.slice(0, 4)));
  for (const key of ['2022-07', '2022-08', '2024-07']) assert.equal(m.cells.get(key).status, 'no-observation', key);
  assert.ok(m.busiestMonth && m.busiestYear);
  assert.ok(m.busiestYear.year !== 2022 && m.busiestYear.year !== 2024);
  const h = stats.monthHistory(m, 2016, 4);
  assert.ok(h.years >= 15 && h.median > 0 && h.p10 <= h.median && h.median <= h.p90);
  const csv = stats.monthCalendarCSV(m, 'Nepal', 'Region total', nepal.meta.label).replace('﻿', '').split('\r\n');
  assert.match(csv[0], /same_month_other_years_median/);
  assert.equal(csv.length, 1 + m.years.length * 12);
  assert.ok(csv.some(line => line.includes('"2022","7",""') && line.includes('no-observation')));
  assert.ok(csv.every((line, i) => i === 0 || line.includes('not a forecast')));
});

test('evidence brief carries the month-vs-history comparison when supplied', () => {
  const weeks = aggregateWeeks(nepal.daily);
  const week = weeks.find(w => w.year === 2016 && w.week === 15);
  const history = stats.monthHistory(stats.monthMatrix(nepal.daily, 'harmonized'), 2016, Number(week.date.slice(5, 7)));
  const input = {week, region: nepal, label: nepal.meta.label, cellId: 'ALL', shareUrl: null, caveats: ['c']};
  const withMonth = buildEvidenceBrief({...input, monthHistory: history}).content;
  assert.match(withMonth, /## Month vs history/);
  assert.match(withMonth, /Historical comparison, not a forecast/);
  assert.match(withMonth, /\| Other years compared \| \d+ \|/);
  assert.doesNotMatch(buildEvidenceBrief(input).content, /Month vs history/);
});
