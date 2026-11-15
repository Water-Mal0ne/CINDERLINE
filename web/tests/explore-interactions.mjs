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
function componentHarness(filename) {
  const slots = [];
  let cursor = 0, effects = [];
  const hooks = {...React,
    useState(initial) {
      const slot = cursor++;
      if (!(slot in slots)) slots[slot] = typeof initial === 'function' ? initial() : initial;
      return [slots[slot], value => { slots[slot] = typeof value === 'function' ? value(slots[slot]) : value; }];
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
    const source = readFileSync(file, 'utf8');
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
    if (effects.length) {
      for (const effect of effects) effect();
      cursor = 0; effects = [];
      output = Component(props);
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
