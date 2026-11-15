import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';

const require = createRequire(new URL('../package.json', import.meta.url));
const ts = require('typescript');
const fixture = name => JSON.parse(readFileSync(new URL(`../public/data/${name}`, import.meta.url), 'utf8'));
const compile = name => ts.transpileModule(readFileSync(new URL(`../src/${name}`, import.meta.url), 'utf8'), {
  compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX},
}).outputText;
function moduleFrom(name, dependencies = {}) {
  const module = {exports: {}};
  vm.runInNewContext(compile(name), {
    module, exports: module.exports, AbortController,
    require: id => id.endsWith('.css') ? {} : (dependencies[id] ?? require(id)),
  }, {filename: name});
  return module.exports;
}
const navigation = moduleFrom('rhythmMapNavigation.ts');
const validation = moduleFrom('rhythmData.ts');

// Run the actual component and event handlers with controlled effects/promises.
// DOM focus/layout is checked separately in the browser; no extra test package is needed.
function mount(name, loadData, props = {}) {
  const slots = [], cleanups = new Map();
  const invalidations = [];
  let cursor = 0, dirty = false, queued = [], tree;
  const hooks = {
    useState(initial) {
      const at = cursor++;
      if (!(at in slots)) slots[at] = typeof initial === 'function' ? initial() : initial;
      return [slots[at], value => {
        const next = typeof value === 'function' ? value(slots[at]) : value;
        if (!Object.is(next, slots[at])) { slots[at] = next; dirty = true; }
      }];
    },
    useMemo: fn => fn(),
    useRef(initial) {
      const at = cursor++;
      if (!(at in slots)) slots[at] = {current: initial};
      return slots[at];
    },
    useEffect(effect, dependencies) {
      const at = cursor++, old = slots[at];
      if (!old || dependencies.some((value, i) => !Object.is(value, old[i]))) {
        slots[at] = dependencies;
        queued.push(() => { cleanups.get(at)?.(); cleanups.set(at, effect()); });
      }
    },
  };
  const Component = moduleFrom(name, {react: hooks,
    './loadData': {loadData, invalidateData: file => invalidations.push(file)},
    './rhythmMapNavigation': navigation, './rhythmData': validation,
    // The FRP panel has its own suite (frp-comparison.mjs); here it is an inert child element.
    './FrpComparison': {default: function FrpComparison() { return null; }},
  }).default;
  function render() {
    let passes = 0;
    do {
      assert.ok(passes++ < 10, 'component effects settle');
      cursor = 0; dirty = false;
      tree = Component(props);
      const effects = queued; queued = [];
      effects.forEach(effect => effect());
    } while (dirty);
    return tree;
  }
  render();
  return {
    render, invalidations, get tree() { return tree; },
    async settle() { await new Promise(resolve => setImmediate(resolve)); return render(); },
    unmount() { for (const cleanup of cleanups.values()) cleanup?.(); },
  };
}
function nodes(value, match) {
  if (Array.isArray(value)) return value.flatMap(child => nodes(child, match));
  if (!value || typeof value !== 'object') return [];
  return [...(match(value) ? [value] : []), ...nodes(value.props?.children, match)];
}
const text = value => Array.isArray(value) ? value.map(text).join('') : (value && typeof value === 'object' ? text(value.props?.children) : String(value ?? ''));
const button = (tree, label) => nodes(tree, n => n.type === 'button' && text(n) === label)[0];
const select = (tree, id) => nodes(tree, n => n.type === 'select' && n.props.id === id)[0];
const mapCells = tree => nodes(tree, n => n.type === 'rect' && n.props.role === 'button');
const realMap = {'rhythm_cells.json': fixture('rhythm_cells.json'), 'rhythm_cells_summary.json': fixture('rhythm_cells_summary.json'), 'world-land.json': {features: []}};

test('weekday data failure exposes a retry that recovers the actual seven-country results', async () => {
  let calls = 0;
  const payload = fixture('rhythm.json');
  const app = mount('RhythmView.tsx', async () => {
    if (++calls === 1) throw new Error('temporary network failure');
    return payload;
  });
  await app.settle();
  assert.equal(app.tree.props.role, 'alert');
  const retry = button(app.tree, 'Retry weekday analysis');
  assert.ok(retry);
  retry.props.onClick(); app.render();
  assert.equal(app.tree.props.role, 'status');
  await app.settle();
  assert.equal(calls, 2);
  assert.deepEqual(app.invalidations, ['rhythm.json']);
  const picker = select(app.tree, 'rh-country-select');
  assert.equal(nodes(picker, n => n.type === 'option').length, 7);
  assert.deepEqual(nodes(picker, n => n.type === 'option').map(n => n.props.value), payload.countries.map(c => c.country));
  assert.equal(nodes(app.tree, n => n.props?.role === 'alert').length, 0);
  app.unmount();
});

test('map failure can retry without reloading the national analysis', async () => {
  let cellCalls = 0;
  const app = mount('RhythmCellMap.tsx', async file => {
    if (file === 'rhythm_cells.json' && ++cellCalls === 1) throw new Error('temporary failure');
    return realMap[file];
  });
  await app.settle();
  assert.equal(app.tree.props.role, 'alert');
  button(app.tree, 'Retry per-cell map').props.onClick(); app.render();
  await app.settle();
  assert.equal(cellCalls, 2);
  assert.deepEqual(app.invalidations, ['rhythm_cells.json', 'rhythm_cells_summary.json']);
  assert.ok(mapCells(app.tree).length > 1);
  app.unmount();
});

test('loaded empty map data exits loading, and a missing default country selects available data', async () => {
  const empty = {...realMap['rhythm_cells.json'], rows: []};
  const app = mount('RhythmCellMap.tsx', async file => file === 'rhythm_cells.json' ? empty : realMap[file]);
  await app.settle();
  assert.match(text(app.tree), /No per-cell results are available/);
  assert.doesNotMatch(text(app.tree), /Loading/);
  app.unmount();
  const table = realMap['rhythm_cells.json'], countryColumn = table.columns.indexOf('country');
  const usa = {...table, rows: table.rows.filter(row => row[countryColumn] === 'United_States')};
  const fallback = mount('RhythmCellMap.tsx', async file => file === 'rhythm_cells.json' ? usa : realMap[file]);
  await fallback.settle();
  assert.ok(mapCells(fallback.tree).length > 1);
  assert.equal(select(fallback.tree, 'rh-map-country-select').props.value, 'United_States');
  fallback.unmount();
});

test('each map has one tab stop; arrow keys, End, Space and country changes keep selection consistent', async () => {
  const app = mount('RhythmCellMap.tsx', async file => realMap[file]);
  await app.settle();
  let cells = mapCells(app.tree);
  assert.ok(cells.length > 100);
  assert.equal(cells.filter(cell => cell.props.tabIndex === 0).length, 1);
  cells.forEach(cell => cell.ref({focus: () => cell.props.onFocus()}));
  let prevented = 0;
  cells[0].props.onKeyDown({key: 'ArrowRight', preventDefault() { prevented++; }});
  app.render(); cells = mapCells(app.tree);
  assert.equal(cells[1].props.tabIndex, 0);
  assert.equal(cells[1].props['aria-pressed'], true);
  cells.forEach(cell => cell.ref({focus: () => cell.props.onFocus()}));
  cells[1].props.onKeyDown({key: 'End', preventDefault() { prevented++; }});
  app.render(); cells = mapCells(app.tree);
  assert.equal(cells.at(-1).props.tabIndex, 0);
  cells.at(-1).props.onKeyDown({key: ' ', preventDefault() { prevented++; }});
  app.render();
  assert.equal(prevented, 3);
  assert.equal(mapCells(app.tree).at(-1).props['aria-pressed'], true);
  select(app.tree, 'rh-map-country-select').props.onChange({target: {value: 'Brazil'}}); app.render();
  cells = mapCells(app.tree);
  assert.equal(cells[0].props.tabIndex, 0);
  assert.equal(cells.filter(cell => cell.props['aria-pressed']).length, 0);
  assert.match(text(app.tree), /Select a cell to see its values/);
  app.unmount();
});

test('missing map outline is recoverable while cell values remain available', async () => {
  let landCalls = 0, cellCalls = 0, summaryCalls = 0;
  const app = mount('RhythmCellMap.tsx', async file => {
    if (file === 'world-land.json' && ++landCalls === 1) throw new Error('outline unavailable');
    if (file === 'rhythm_cells.json' && ++cellCalls > 1) throw new Error('science must not refetch');
    if (file === 'rhythm_cells_summary.json' && ++summaryCalls > 1) throw new Error('science must not refetch');
    return realMap[file];
  });
  await app.settle();
  assert.ok(mapCells(app.tree).length);
  mapCells(app.tree)[0].props.onClick(); app.render();
  const selectedLabel = mapCells(app.tree)[0].props['aria-label'];
  button(app.tree, 'Retry map outline').props.onClick(); app.render();
  await app.settle();
  assert.equal(landCalls, 2);
  assert.equal(cellCalls, 1);
  assert.equal(summaryCalls, 1);
  assert.deepEqual(app.invalidations, ['world-land.json']);
  assert.equal(button(app.tree, 'Retry map outline'), undefined);
  assert.ok(mapCells(app.tree).length);
  assert.equal(mapCells(app.tree).find(cell => cell.props['aria-pressed']).props['aria-label'], selectedLabel);
  app.unmount();
});

test('malformed HTTP-200 analysis and map summary data reach recoverable errors', async () => {
  let calls = 0;
  const analysis = mount('RhythmView.tsx', async () => ++calls === 1 ? {countries: []} : fixture('rhythm.json'));
  await analysis.settle();
  assert.equal(analysis.tree.props.role, 'alert');
  button(analysis.tree, 'Retry weekday analysis').props.onClick(); analysis.render();
  await analysis.settle();
  assert.ok(analysis.tree.props.className.split(' ').includes('rhythm-page'));
  assert.deepEqual(analysis.invalidations, ['rhythm.json']);
  analysis.unmount();
  let summaries = 0, outlines = 0;
  const app = mount('RhythmCellMap.tsx', async file => {
    if (file === 'rhythm_cells_summary.json' && ++summaries === 1) return {aqua_check: {India: null}};
    if (file === 'world-land.json') outlines++;
    return realMap[file];
  });
  await app.settle();
  assert.equal(app.tree.props.role, 'alert');
  button(app.tree, 'Retry per-cell map').props.onClick(); app.render();
  await app.settle();
  assert.ok(mapCells(app.tree).length);
  assert.equal(outlines, 1, 'science retry does not refetch the outline');
  assert.deepEqual(app.invalidations, ['rhythm_cells.json', 'rhythm_cells_summary.json']);
  assert.equal(app.tree.props.role, undefined);
  app.unmount();
});

test('render contracts accept published values unchanged and reject malformed geometry or numbers', () => {
  const data = fixture('rhythm.json'), cells = realMap['rhythm_cells.json'], summary = realMap['rhythm_cells_summary.json'];
  const before = JSON.stringify([data, cells, summary]);
  assert.equal(validation.validRhythmPayload(data), true);
  assert.equal(validation.validRhythmCellTable(cells), true);
  assert.equal(validation.validRhythmCellSummary(summary), true);
  assert.equal(validation.validRhythmLand(fixture('world-land.json')), true);
  assert.equal(JSON.stringify([data, cells, summary]), before, 'validation never mutates scientific payloads');
  const broken = structuredClone(data);
  broken.countries[0].streams[0].weekdays[0].index = NaN;
  assert.equal(validation.validRhythmPayload(broken), false);
  assert.equal(validation.validRhythmCellTable({...cells, rows: [[null]]}), false);
  assert.equal(validation.validRhythmLand({features: [{geometry: {type: 'Polygon', coordinates: [[null]]}}]}), false);
});

test('cell keyboard navigation respects boundaries and leaves Tab to the browser', () => {
  const {nextRhythmCell: next} = navigation;
  assert.equal(next('ArrowLeft', 0, 3), 0);
  assert.equal(next('ArrowRight', 2, 3), 2);
  assert.equal(next('Home', 2, 3), 0);
  assert.equal(next('End', 0, 3), 2);
  assert.equal(next('Tab', 0, 3), null);
  assert.equal(next('End', 0, 0), null);
});

test('verdict country links focus the updated detail heading, including repeated selection, without hijacking in-panel controls', async () => {
  const app = mount('RhythmView.tsx', async () => fixture('rhythm.json'));
  await app.settle();
  const heading = () => nodes(app.tree, n => n.props?.id === 'rh-country-title')[0];
  const link = name => nodes(app.tree, n => n.type === 'button' && n.props.className === 'rh-link' && text(n) === name)[0];
  assert.equal(link('United States').props['aria-pressed'], true);
  assert.equal(link('Brazil').props['aria-controls'], 'rh-country-panel');
  const focused = [], scrolled = [];
  heading().ref.current = {
    focus(options) { assert.equal(options.preventScroll, true); focused.push(text(heading())); },
    scrollIntoView(options) { assert.equal(options.block, 'start'); scrolled.push(text(heading())); },
  };
  link('Brazil').props.onClick(); app.render();
  assert.deepEqual(focused, ['Brazil']);
  assert.deepEqual(scrolled, ['Brazil']);
  assert.equal(link('Brazil').props['aria-pressed'], true);
  link('Brazil').props.onClick(); app.render();
  assert.deepEqual(focused, ['Brazil', 'Brazil']);
  select(app.tree, 'rh-country-select').props.onChange({target: {value: 'India'}}); app.render();
  assert.equal(text(heading()), 'India');
  button(app.tree, 'Daytime only').props.onClick(); app.render();
  assert.deepEqual(focused, ['Brazil', 'Brazil'], 'in-panel controls keep their own focus and scroll position');
  app.unmount();
});

test('rhythm tables expose country row headers and named detection controls', async () => {
  const app = mount('RhythmView.tsx', async () => fixture('rhythm.json'));
  await app.settle();
  const tables = nodes(app.tree, n => n.type === 'table');
  assert.equal(tables.length, 2);
  for (const table of tables) {
    const head = nodes(table, n => n.type === 'thead')[0], body = nodes(table, n => n.type === 'tbody')[0];
    assert.ok(nodes(head, n => n.type === 'th').every(header => header.props.scope === 'col'));
    for (const row of nodes(body, n => n.type === 'tr')) {
      const headers = nodes(row, n => n.type === 'th' && n.props.scope === 'row');
      assert.equal(headers.length, 1);
      assert.ok(text(headers[0]).trim());
    }
  }
  assert.equal(nodes(app.tree, n => n.props?.['aria-label'] === 'Detections included')[0].props.role, 'group');
  app.unmount();
});

test('focused rhythm views preserve country and defer the map until requested', async () => {
  const child = {type: 'div', props: {id: 'map-sentinel', children: 'Map content'}};
  const app = mount('RhythmView.tsx', async () => fixture('rhythm.json'), {children: child});
  await app.settle();
  const panel = id => nodes(app.tree, n => n.props?.id === `rh-analysis-${id}`)[0];
  const map = () => nodes(app.tree, n => n.props?.id === 'map-sentinel');
  assert.equal(panel('charts').props.hidden, false);
  assert.equal(panel('results').props.hidden, true);
  assert.equal(panel('map').props.hidden, true);
  assert.equal(map().length, 0, 'the spatial data component is not mounted on entry');
  select(app.tree, 'rh-country-select').props.onChange({target: {value: 'Brazil'}}); app.render();
  button(app.tree, 'Country results').props.onClick(); app.render();
  assert.equal(panel('results').props.hidden, false);
  assert.equal(panel('charts').props.hidden, true);
  button(app.tree, 'Spatial patterns').props.onClick(); app.render();
  assert.equal(panel('map').props.hidden, false);
  assert.equal(map().length, 1);
  button(app.tree, 'Weekday charts').props.onClick(); app.render();
  assert.equal(select(app.tree, 'rh-country-select').props.value, 'Brazil');
  assert.equal(map().length, 1, 'the previously opened map remains mounted to preserve its selection');
  assert.equal(panel('map').props.hidden, true);
  const link = nodes(app.tree, n => n.type === 'button' && n.props.className === 'rh-link' && text(n) === 'India')[0];
  button(app.tree, 'Country results').props.onClick(); app.render();
  link.props.onClick(); app.render();
  assert.equal(panel('charts').props.hidden, false);
  assert.equal(select(app.tree, 'rh-country-select').props.value, 'India');
  app.unmount();
});

test('FRP is an explicit disclosure and all seven weekday selectors retain the published profiles', async () => {
  const payload = fixture('rhythm.json');
  const app = mount('RhythmView.tsx', async () => payload);
  await app.settle();
  const frp = () => nodes(app.tree, n => typeof n.type === 'function' && n.type.name === 'FrpComparison');
  const disclosure = () => nodes(app.tree, n => n.type === 'details' && n.props.className.includes('rh-frp-disclosure'))[0];
  assert.equal(frp().length, 0, 'separate FRP data is not fetched until opened');
  disclosure().props.onToggle({currentTarget: {open: true}}); app.render();
  assert.equal(frp().length, 1);
  disclosure().props.onToggle({currentTarget: {open: false}}); app.render();
  assert.equal(frp().length, 0);
  for (const country of payload.countries) {
    select(app.tree, 'rh-country-select').props.onChange({target: {value: country.country}}); app.render();
    const streams = nodes(app.tree, n => typeof n.type === 'function' && n.type.name === 'StreamCard');
    assert.deepEqual(streams.map(n => n.props.row), country.streams);
    assert.ok(streams.every(n => n.props.rest === country.rest_day));
  }
  app.unmount();
});

test('map boundary keys restore the focused cell after pointer hover without relying on a new focus event', async () => {
  const app = mount('RhythmCellMap.tsx', async file => realMap[file]);
  await app.settle();
  let focused = 0, cells = mapCells(app.tree);
  const attachRefs = () => cells.forEach((cell, i) => cell.ref({focus() {
    if (i !== focused) { focused = i; cell.props.onFocus(); }
  }}));
  cells[0].props.onFocus(); app.render();
  for (const key of ['Home', 'ArrowLeft']) {
    cells = mapCells(app.tree); cells[1].props.onMouseEnter(); app.render();
    cells = mapCells(app.tree); attachRefs();
    assert.equal(cells[1].props['aria-pressed'], true);
    cells[0].props.onKeyDown({key, preventDefault() {}}); app.render();
    assert.equal(mapCells(app.tree)[0].props['aria-pressed'], true, key);
    assert.equal(mapCells(app.tree)[1].props['aria-pressed'], false, key);
  }
  app.unmount();
});
