import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require = createRequire(new URL('../package.json', import.meta.url)), ts = require('typescript');
const compile = name => ts.transpileModule(readFileSync(new URL('../src/' + name, import.meta.url), 'utf8'), {
  compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.ES2022},
}).outputText;
const dataUrl = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const stateUrl = dataUrl(compile('explorationState.ts'));
const integration = await import(dataUrl(compile('explorationIntegration.ts').replace("'./explorationState'", JSON.stringify(stateUrl))));
const state = await import(stateUrl);
const area = await import(dataUrl(compile('areaSelection.ts')));
const {normalizePublishedData} = await import(dataUrl(compile('loadData.ts')));
const read = name => JSON.parse(readFileSync(new URL('../public/data/' + name, import.meta.url), 'utf8'));

test('GLOBE_LAST_YEAR matches the published annual Earth view', () => {
  const globe = read('globe.json');
  assert.equal(integration.GLOBE_LAST_YEAR, globe.years.at(-1));
});

test('a calendar running past the Earth data shares the latest globe year', () => {
  const region = normalizePublishedData(read('Nepal.json'));
  assert.ok(region.meta.period_end > `${integration.GLOBE_LAST_YEAR}-12-31`, 'calendar extends beyond the globe');
  const catalog = integration.catalogForRegion(region);
  assert.equal(Math.max(...catalog.regions[0].globeYears), integration.GLOBE_LAST_YEAR);
  const resolved = integration.resolveAppExploration('?region=Nepal', catalog);
  assert.equal(resolved.state.end, region.meta.period_end);
  assert.equal(resolved.state.globeYear, integration.GLOBE_LAST_YEAR);
  const link = state.createShareLink('https://example.org/firetrace/', resolved.state, catalog);
  assert.equal(new URL(link.url).searchParams.get('globeYear'), String(integration.GLOBE_LAST_YEAR));
  // even a state that asks for the calendar year is canonicalised to the latest globe year
  const asked = state.createShareLink('https://example.org/firetrace/', {...resolved.state, globeYear: 2025}, catalog);
  assert.equal(new URL(asked.url).searchParams.get('globeYear'), String(integration.GLOBE_LAST_YEAR));
  assert.equal(integration.canShareSelection(resolved.state, catalog), true);
});

test('area period note matches the area files', () => {
  const nepal = read('area/Nepal.json');
  const lastYear = Number(nepal.first_month.slice(0, 4)) + nepal.months / 12 - 1;
  assert.equal(area.AREA_PERIOD_NOTE, `Area series run ${nepal.first_month.slice(0, 4)}-${lastYear}; 2025 is national only.`);
});
