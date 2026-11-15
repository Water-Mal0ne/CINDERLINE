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
const coverageUrl = dataUrl(compile('calendarView.ts').replace("'./explorationState'", JSON.stringify(dataUrl(compile('explorationState.ts')))));
const source = compile('evidenceBrief.ts').replace("'./utils'", JSON.stringify(utilsUrl)).replace("'./calendarView'", JSON.stringify(coverageUrl));
const {buildEvidenceBrief} = await import(dataUrl(source));
const {aggregateWeeks} = await import(utilsUrl);
const {normalizePublishedData, decodeCell} = await import(dataUrl(compile('loadData.ts')));
const readData = name => JSON.parse(readFileSync(new URL('../public/data/' + name, import.meta.url), 'utf8'));
const nepal = normalizePublishedData(readData('Nepal.json'));
const weeks = aggregateWeeks(nepal.daily);
const publishedWeek = (year, week) => weeks.find(item => item.year === year && item.week === week);
const caveats = [
  'Detections are sensor observations, not a count of distinct fires.',
  'Conversion intervals are reported below, not summed into a weekly confidence interval. Direct Aqua values have no calibration step; this does not mean observation uncertainty is zero.',
  nepal.meta.coverage_note,
];
const input = week => ({week, region: nepal, label: nepal.meta.label, cellId: 'ALL', shareUrl: null, caveats});
const summary = (content, label) => content.split('\n').find(line => line.startsWith(`| ${label} |`));
const daily = content => content.split('\n').filter(line => /^\| \d{4}-\d{2}-\d{2} \|/.test(line));

test('published week exports current values, reference, sources, exact daily precision and the supplied view URL', () => {
  const week = publishedWeek(2016, 15);
  const before = JSON.stringify(week);
  const shareUrl = 'https://cinderline-spaceapps.pages.dev/?region=Nepal&week=2016-04-08&scale=raw';
  const result = buildEvidenceBrief({...input(week), shareUrl});
  assert.equal(result.filename, 'CINDERLINE_Nepal_whole-region_2016-04-08_week-15_evidence.md');
  assert.match(result.content, /Reference scale: MODIS Aqua/);
  assert.match(result.content, /Calendar period: 2016-04-08 to 2016-04-14/);
  assert.equal(summary(result.content, 'Raw baseline'), '| Raw baseline | 17,034 |');
  assert.equal(summary(result.content, 'Aqua-reference-equivalent activity'), '| Aqua-reference-equivalent activity | 979.2 |');
  assert.equal(summary(result.content, 'Terra observations'), '| Terra observations | 1,014 |');
  assert.equal(summary(result.content, 'Aqua observations'), '| Aqua observations | 1,079 |');
  assert.equal(summary(result.content, 'VIIRS observations'), '| VIIRS observations | 17,034 |');
  assert.equal(daily(result.content).length, 7);
  assert.ok(daily(result.content)[0].includes('| 129.40887 | 122.99922–143.36231 | M1 | converted VIIRS |'));
  for (const caveat of caveats) assert.ok(result.content.includes(caveat));
  assert.ok(result.content.indexOf(caveats[1]) < result.content.indexOf('## Daily records in this view'), 'the unchanged interval caveat refers to the records below it');
  assert.ok(result.content.includes('[NASA FIRMS archive](<https://firms.modaps.eosdis.nasa.gov/country/>)'));
  assert.ok(result.content.includes(`[Open this view](<${shareUrl}>)`));
  assert.equal(JSON.stringify(week), before, 'the builder does not mutate evidence rows');
  assert.equal(buildEvidenceBrief({...input(week), shareUrl}).content, result.content, 'no generated timestamp changes the export');
});

test('partial published selection retains calendar period but exports only selected daily records and totals', () => {
  const week = aggregateWeeks(publishedWeek(2016, 15).rows.slice(1, 3))[0];
  const {content} = buildEvidenceBrief(input(week));
  assert.match(content, /Calendar period: 2016-04-08 to 2016-04-14/);
  assert.match(content, /Records in this view: 2016-04-09 to 2016-04-10/);
  assert.match(content, /Calendar records: 2 of 7 calendar days/);
  assert.match(content, /Available Aqua-reference-equivalent days: 2 of 7 calendar days/);
  assert.match(content, /Partial week in this view\. Totals include only these records\./);
  assert.equal(summary(content, 'Raw baseline'), '| Raw baseline | 7,209 |');
  assert.equal(daily(content).length, 2);
  assert.ok(!content.includes('| 2016-04-08 |'));
});

test('published outage preserves unavailable week estimates alongside recorded sensor zeros and daily coverage', () => {
  const {content} = buildEvidenceBrief(input(publishedWeek(2024, 28)));
  assert.equal(summary(content, 'Raw baseline'), '| Raw baseline | Unavailable |');
  assert.equal(summary(content, 'Aqua-reference-equivalent activity'), '| Aqua-reference-equivalent activity | Unavailable |');
  assert.equal(summary(content, 'VIIRS observations'), '| VIIRS observations | 0 |');
  assert.match(content, /Calendar records: 7 of 7 calendar days/);
  assert.match(content, /Available Aqua-reference-equivalent days: 1 of 7 calendar days/);
  assert.ok(daily(content)[0].startsWith('| 2024-07-08 | 0 | 0 | 0 | 0 | 0 | 0–0 |'));
  assert.ok(daily(content)[1].includes('| 0 | 0 | 0 | Unavailable | Unavailable | Not available | M1 | no observation |'));
  assert.ok(content.includes('no observation: Suomi-NPP GPS/geolocation anomaly'));
  assert.ok(!content.includes('Partial week in this view.'));
});

test('year-end week is complete at two days and never extends into next year', () => {
  const {content} = buildEvidenceBrief(input(publishedWeek(2024, 53)));
  assert.match(content, /Calendar period: 2024-12-30 to 2024-12-31/);
  assert.match(content, /Calendar records: 2 of 2 calendar days/);
  assert.ok(!content.includes('Partial week in this view.'));
});

test('published cell identity and supplied spatial caveat survive a renamed portable brief', () => {
  const cell = nepal.cells[0];
  const week = aggregateWeeks(decodeCell(readData(cell.file))).find(item => item.year === 2016 && item.week === 15);
  const spatial = 'This cell uses a nationally selected calibration. Its bands omit spatial model error, and cell agreement can be much poorer than national agreement.';
  const {content, filename} = buildEvidenceBrief({...input(week), cellId: cell.id, caveats: [...caveats, spatial]});
  assert.equal(filename, 'CINDERLINE_Nepal_cell_27.25_84.75_2016-04-08_week-15_evidence.md');
  assert.match(content, /Country \/ region: Nepal/);
  assert.match(content, /Spatial scope: Cell 27.25:84.75 · 27.4° N, 84.9° E/);
  assert.ok(content.includes(spatial));
  assert.equal(daily(content).length, week.rows.length);
  assert.ok(!content.includes(cell.file), 'local data paths are not exported');
});

test('unavailable sensors remain unavailable; direct Aqua intervals stay not applicable', () => {
  const week = aggregateWeeks([{...publishedWeek(2016, 15).rows[0], source: 'observed Aqua', raw_terra: null, raw_viirs: null, raw_aqua: 0, raw: 0, harmonized: 0, lo: 0, hi: 0}])[0];
  const {content} = buildEvidenceBrief(input(week));
  assert.equal(summary(content, 'Terra observations'), '| Terra observations | Unavailable |');
  assert.equal(summary(content, 'VIIRS observations'), '| VIIRS observations | Unavailable |');
  assert.equal(summary(content, 'Aqua observations'), '| Aqua observations | 0 |');
  assert.ok(daily(content)[0].includes('| Unavailable | 0 | Unavailable | 0 | 0 | Not applicable |'));
});

test('Markdown syntax is escaped and unsafe/private-file URL schemes are not exported', () => {
  const region = {...nepal, meta: {...nepal.meta, region: '../Bad/Region', name: '[country](javascript:bad)', sources: [
    {name: 'Unsafe', url: 'javascript:alert(1)'}, {name: 'Local', url: 'file:///C:/private/data.csv'},
    {name: 'Credentials', url: 'https://secret:token@example.com/'},
    {name: '[source]', url: 'https://example.org/source_(v1)'},
  ]}};
  const week = aggregateWeeks([{...publishedWeek(2016, 15).rows[0], model: 'M1 | added\n# heading <script>'}])[0];
  const {content, filename} = buildEvidenceBrief({...input(week), region, cellId: '../bad:cell', shareUrl: 'file:///C:/private/share.html', caveats: ['# Heading\n[new](javascript:bad)']});
  assert.ok(!/[\\/]/.test(filename));
  assert.ok(content.includes('M1 \\| added \\# heading &lt;script&gt;'));
  assert.ok(content.includes('\\[country\\]\\(javascript:bad\\)'));
  assert.ok(content.includes('[\\[source\\]](<https://example.org/source_(v1)>)'));
  assert.ok(!content.includes('C:/private') && !content.includes('secret:token'));
  assert.ok(!content.includes('[Unsafe]') && !content.includes('[Local]'));
  assert.match(content, /Share URL unavailable\./);
});

test('an empty selection or nonfinite values never become a zero or an invented date', () => {
  const empty = {...publishedWeek(2016, 15), rows: [], raw: null, harmonized: null};
  const {content} = buildEvidenceBrief(input(empty));
  assert.match(content, /Records in this view: Unavailable/);
  assert.match(content, /Calendar records: 0 of 7 calendar days/);
  assert.match(content, /No daily records in this view\./);
  assert.ok(!content.includes('undefined') && !content.includes('Invalid Date'));
  const invalid = aggregateWeeks([{...publishedWeek(2016, 15).rows[0], harmonized: NaN, raw: Infinity, lo: NaN, hi: Infinity}])[0];
  assert.ok(daily(buildEvidenceBrief(input(invalid)).content)[0].includes('| Unavailable | Unavailable | Not available |'));
});
