import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const require = createRequire(new URL('../package.json', import.meta.url));
const ts = require('typescript');
const React = require('react');
const sourceRoot = fileURLToPath(new URL('../src/', import.meta.url));

// Exercise component event handlers and effect dependencies without adding a DOM dependency.
function componentHarness(filename, commit = () => {}, namedFunction) {
  const slots = [];
  let cursor = 0, effects = [];
  const hooks = {...React,
    useState(initial) {
      const slot = cursor++;
      if (!(slot in slots)) slots[slot] = typeof initial === 'function' ? initial() : initial;
      return [slots[slot], value => { slots[slot] = typeof value === 'function' ? value(slots[slot]) : value; }];
    },
    useRef(initial) {
      const slot = cursor++;
      if (!(slot in slots)) slots[slot] = {current: initial};
      return slots[slot];
    },
    useEffect(effect, deps) {
      const slot = cursor++;
      if (!slots[slot] || deps.some((value, i) => !Object.is(value, slots[slot][i]))) effects.push(effect);
      slots[slot] = deps;
    },
    useMemo: factory => factory(),
    useId: () => 'explore-test',
  };
  const modules = new Map();
  function load(file) {
    if (modules.has(file)) return modules.get(file);
    let source = readFileSync(file, 'utf8');
    if (namedFunction && file === path.join(sourceRoot, filename)) {
      const tree = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
      const fn = tree.statements.find(node => ts.isFunctionDeclaration(node) && node.name?.text === namedFunction);
      const colors = tree.statements.find(node => ts.isVariableStatement(node) && node.declarationList.declarations.some(declaration => declaration.name.getText(tree) === 'COLORS'));
      assert.ok(fn, `${namedFunction} exists in the actual source`);
      source = `import {useState,useMemo} from 'react';import {numeric,fmt,prettyDate} from './utils';import {weekCoverage} from './calendarView';import {ScanLine,ArrowUpRight} from 'lucide-react';const Empty=()=>null,ChartLabel=()=>null;${colors.getText(tree)}\n${fn.getText(tree)}\nexport default ${namedFunction};`;
    }
    const compiled = ts.transpileModule(source, {compilerOptions: {
      target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
    }}).outputText;
    const module = {exports: {}};
    new Function('require', 'module', 'exports', compiled)(name => {
      if (name === 'react') return hooks;
      if (name.endsWith('.css')) return {};
      if (name.startsWith('.')) return load(path.resolve(path.dirname(file), name + '.ts'));
      return require(name);
    }, module, module.exports);
    modules.set(file, module.exports);
    return module.exports;
  }
  const Component = load(path.join(sourceRoot, filename)).default;
  return props => {
    cursor = 0; effects = [];
    let output = Component(props);
    commit(output);
    if (effects.length) {
      for (const effect of effects) effect();
      cursor = 0; effects = [];
      output = Component(props);
      commit(output);
    }
    return output;
  };
}

function elements(node, predicate) {
  if (!node || typeof node !== 'object') return [];
  if (Array.isArray(node)) return node.flatMap(item => elements(item, predicate));
  return [...(predicate(node) ? [node] : []), ...elements(node.props?.children, predicate)];
}
const withClass = (node, name) => elements(node, item => String(item.props?.className || '').split(' ').includes(name));
const input = node => elements(node, item => item.type === 'input' && item.props.type === 'range')[0];
const days = months => months.map(date => ({date: `${date}-01`, raw: 20, harmonized: 10, raw_aqua: 11, source: 'converted VIIRS', cell_id: 'ALL'}));

test('monthly inspection retains its date when the observation range changes', () => {
  const render = componentHarness('ComparisonChart.tsx');
  const props = {rows: days(['2023-01', '2023-02', '2023-03']), mode: 'harmonized', label: 'REAL FIRMS DATA', regionId: 'Nepal', regionName: 'Nepal', cellId: 'ALL'};
  let tree = render(props);
  input(tree).props.onChange({target: {value: '1'}});
  tree = render(props);
  assert.match(input(tree).props['aria-valuetext'], /^2023-02,/);
  tree = render({...props, rows: days(['2022-12', '2023-01', '2023-02', '2023-03'])});
  assert.match(input(tree).props['aria-valuetext'], /^2023-02,/, 'adding an earlier month must not silently select January');
  tree = render({...props, rows: days(['2023-03', '2023-04'])});
  assert.match(input(tree).props['aria-valuetext'], /^2023-03,/, 'an excluded selection moves to the nearest available boundary');
});

test('monthly inspection starts within the new country or cell scope', () => {
  const render = componentHarness('ComparisonChart.tsx');
  const props = {rows: days(['2023-01', '2023-02']), mode: 'harmonized', label: 'REAL FIRMS DATA', regionId: 'Nepal', regionName: 'Nepal', cellId: 'ALL'};
  let tree = render(props);
  input(tree).props.onChange({target: {value: '1'}});
  tree = render({...props, cellId: '27.5_85.25'});
  assert.match(input(tree).props['aria-valuetext'], /^2023-01,/);
  tree = render({...props, rows: []});
  assert.equal(input(tree), undefined, 'empty selections keep their explicit empty state');
});

test('anomaly expansion survives an evidence-panel parent rerender but resets for a changed selection', () => {
  const render = componentHarness('AnomalyPanel.tsx');
  const anomalies = Array.from({length: 12}, (_, i) => ({date: `2023-${String(i + 1).padStart(2, '0')}-01`, week: i + 1, status: i % 2 ? 'high' : 'low', value: i * 10, z_score: i / 2}));
  const props = {anomalies, cell: 'ALL', label: 'REAL FIRMS DATA', onSelect() {}};
  let tree = render(props);
  assert.equal(withClass(tree, 'ft-anomaly-result').length, 8);
  withClass(tree, 'ft-anomaly-more')[0].props.onClick();
  tree = render(props);
  assert.equal(withClass(tree, 'ft-anomaly-result').length, 12);
  tree = render({...props, anomalies: anomalies.map(row => ({...row}))});
  assert.equal(withClass(tree, 'ft-anomaly-result').length, 12, 'equivalent parent data must preserve expanded results');
  tree = render({...props, anomalies: anomalies.slice(1)});
  assert.equal(withClass(tree, 'ft-anomaly-result').length, 8, 'a genuinely different selection resets pagination');
});

test('monthly table control names and exposes its keyboard-scrollable target', () => {
  const render = componentHarness('ComparisonChart.tsx');
  const props = {rows: days(['2023-01']), mode: 'harmonized', label: 'REAL FIRMS DATA', regionId: 'Nepal', regionName: 'Nepal', cellId: 'ALL'};
  let tree = render(props);
  const toggle = elements(tree, item => item.type === 'button' && 'aria-expanded' in item.props)[0];
  toggle.props.onClick();
  tree = render(props);
  const table = withClass(tree, 'comparison-table')[0];
  const openToggle = elements(tree, item => item.type === 'button' && 'aria-expanded' in item.props)[0];
  assert.equal(openToggle.props['aria-expanded'], true);
  assert.equal(openToggle.props['aria-controls'], table.props.id);
  assert.ok(table.props.id);
  assert.equal(table.props.role, 'region');
  assert.equal(table.props.tabIndex, 0);
  assert.equal(table.props['aria-label'], 'Monthly comparison values');
});

test('expanding anomaly results focuses the first new row even when Show more disappears', () => {
  const focused = [];
  const render = componentHarness('AnomalyPanel.tsx', tree => {
    const list = withClass(tree, 'ft-anomaly-results')[0];
    if (list?.ref) list.ref.current = {querySelectorAll: () => withClass(tree, 'ft-anomaly-result').map((row, index) => ({focus() { focused.push(index); }}))};
  });
  const anomalies = Array.from({length: 20}, (_, i) => ({date: `2023-01-${String(i + 1).padStart(2, '0')}`, week: i + 1, status: 'high', value: i * 10, z_score: i / 2}));
  const props = {anomalies, cell: 'ALL', label: 'REAL FIRMS DATA', onSelect() {}};
  let tree = render(props);
  withClass(tree, 'ft-anomaly-more')[0].props.onClick();
  tree = render(props);
  assert.equal(withClass(tree, 'ft-anomaly-result').length, 16);
  assert.deepEqual(focused, [8], 'focus moves into the new batch instead of staying below it');
  withClass(tree, 'ft-anomaly-more')[0].props.onClick();
  tree = render(props);
  assert.equal(withClass(tree, 'ft-anomaly-more').length, 0);
  assert.deepEqual(focused, [8, 16], 'the last expansion keeps focus on an existing observation');
  render({...props, anomalies: anomalies.map(row => ({...row}))});
  assert.deepEqual(focused, [8, 16], 'ordinary rerenders do not steal focus');
});

test('isolated monthly values remain visible without connecting across missing observations', () => {
  const render = componentHarness('ComparisonChart.tsx');
  const rows = days(['2023-01', '2023-02', '2023-03', '2023-04', '2023-05']).map((row, i) => ({...row, raw: null, raw_aqua: null, harmonized: i === 1 ? 0 : i === 3 ? 10 : null}));
  const tree = render({rows, mode: 'harmonized', label: 'REAL FIRMS DATA', regionId: 'Nepal', regionName: 'Nepal', cellId: 'ALL'});
  const chart = elements(tree, item => item.type === 'svg')[0];
  const marks = elements(chart, item => item.type === 'circle');
  assert.equal(marks.length, 2, 'both isolated values need visible marks when neither is selected');
  const zeroLine = elements(chart, item => item.type === 'line')[0];
  assert.ok(marks.some(mark => mark.props.cy === zeroLine.props.y1), 'the observed zero is plotted at the baseline');
  const converted = elements(chart, item => item.type === 'path' && item.props.stroke === '#f79963')[0];
  assert.doesNotMatch(converted.props.d, /L/, 'missing months must not be bridged');
});

test('an absent calendar month breaks the monthly line and preserves its isolated values', () => {
  const render = componentHarness('ComparisonChart.tsx');
  const props = {rows: days(['2023-01', '2023-03']).map((row, i) => ({...row, raw: null, raw_aqua: null, harmonized: i ? 0 : 10})), mode: 'harmonized', label: 'REAL FIRMS DATA', regionId: 'Nepal', regionName: 'Nepal', cellId: 'ALL'};
  const tree = render(props), chart = elements(tree, item => item.type === 'svg')[0];
  const converted = elements(chart, item => item.type === 'path' && item.props.stroke === '#f79963')[0];
  assert.doesNotMatch(converted.props.d, /L/, 'January and March must not be connected when February has no rows');
  const marks = elements(chart, item => item.type === 'circle');
  assert.equal(marks.length, 2, 'both sides of the absent month remain visible');
  assert.ok(marks.some(mark => mark.props.cy === elements(chart, item => item.type === 'line')[0].props.y1), 'the unselected zero remains visible');
});

test('consecutive December and January remain connected across the year boundary', () => {
  const render = componentHarness('ComparisonChart.tsx');
  const tree = render({rows: days(['2023-12', '2024-01']), mode: 'harmonized', label: 'REAL FIRMS DATA', regionId: 'Nepal', regionName: 'Nepal', cellId: 'ALL'});
  const chart = elements(tree, item => item.type === 'svg')[0];
  const converted = elements(chart, item => item.type === 'path' && item.props.stroke === '#f79963')[0];
  assert.equal((converted.props.d.match(/L/g) || []).length, 1);
  assert.equal(withClass(chart, 'comparison-isolated-point').length, 0);
});

test('isolated seasonal zeros remain visible while missing weeks stay gaps', () => {
  const render = componentHarness('SeasonalContext.tsx');
  const region = {meta: {region: 'Nepal', name: 'Nepal', period_start: '2003-01-01', period_end: '2024-12-31'},
    weekly_climatology: [{week: 4, median: 10, p10: 5, p90: 15, critical: false}, {week: 20, median: 0, p10: 0, p90: 1, critical: false}], critical_periods: []};
  const props = {region, label: 'REAL FIRMS DATA', selectedYear: 2024, onExport() {}, cell: 'ALL'};
  let tree = render(props);
  const chart = withClass(tree, 'seasonal-chart')[0];
  const marks = elements(chart, item => item.type === 'circle');
  assert.equal(marks.length, 2, 'the selected peak and the isolated zero both remain visible');
  const zeroLine = withClass(chart, 'seasonal-gridline')[0];
  assert.ok(marks.some(mark => mark.props.cy === zeroLine.props.y1));
  for (const line of withClass(chart, 'seasonal-median')) assert.doesNotMatch(line.props.d, /L/);
  assert.equal(withClass(chart, 'seasonal-band').length, 2, 'absent weeks separate percentile-band segments too');
  for (const band of withClass(chart, 'seasonal-band')) {
    const xs = [...band.props.d.matchAll(/[ML]([^, ]+),/g)].map(match => Number(match[1]));
    assert.equal(new Set(xs).size, 1, 'an isolated band must not extend across the missing weeks');
  }
  input(tree).props.onChange({target: {value: '2'}});
  tree = render(props);
  assert.equal(elements(withClass(tree, 'seasonal-chart')[0], item => item.type === 'circle').length, 2, 'selecting an unknown week must not add a fabricated marker');
  assert.match(input(tree).props['aria-valuetext'], /historical median —/);
});

test('calendar boundary arrows restore the focused week after a different hover preview', () => {
  const render = componentHarness('App.tsx', () => {}, 'Heatmap');
  const weeks = [1, 2].map(week => ({key: `2024-${week}`, year: 2024, week, date: week === 1 ? '2024-01-01' : '2024-01-08', raw: week * 10, harmonized: week * 5,
    rows: [{date: week === 1 ? '2024-01-01' : '2024-01-08', raw: week * 10, harmonized: week * 5}]}));
  const props = {weeks, mode: 'harmonized', label: 'REAL FIRMS DATA', onSelect() {}};
  const copy = node => typeof node === 'string' || typeof node === 'number' ? String(node) : Array.isArray(node) ? node.map(copy).join('') : node && typeof node === 'object' ? copy(node.props?.children) : '';
  let tree = render(props);
  withClass(tree, 'week-cell')[0].props.onFocus();
  for (const key of ['ArrowLeft', 'ArrowUp']) {
    withClass(tree, 'week-cell')[1].props.onMouseEnter();
    tree = render(props);
    assert.match(copy(withClass(tree, 'calendar-inspector')[0]), /WEEK 2/);
    const buttons = withClass(tree, 'week-cell');
    let focusMoves = 0, prevented = false;
    const nodes = buttons.map(button => ({disabled: button.props.disabled, focus() { focusMoves++; button.props.onFocus(); }, closest() { return {querySelectorAll: () => nodes}; }}));
    buttons[0].props.onKeyDown({key, currentTarget: nodes[0], preventDefault() { prevented = true; }});
    tree = render(props);
    assert.equal(prevented, true);
    assert.equal(focusMoves, 0, 'a boundary arrow does not move outside the calendar');
    assert.match(copy(withClass(tree, 'calendar-inspector')[0]), /WEEK 1/, 'the preview follows keyboard focus even without a focus event');
  }
  withClass(tree, 'week-cell')[1].props.onMouseEnter();
  tree = render(props);
  withClass(tree, 'week-cell')[0].props.onKeyDown({key: 'Tab'});
  tree = render(props);
  assert.match(copy(withClass(tree, 'calendar-inspector')[0]), /WEEK 2/, 'ordinary tab navigation does not erase the pointer preview');
});
