import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';

const require = createRequire(new URL('../package.json', import.meta.url));
const React = require('react'), ts = require('typescript');
const compiled = ts.transpileModule(readFileSync(new URL('../src/ShareView.tsx', import.meta.url), 'utf8'), {
  compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX},
}).outputText;

function nodes(tree, predicate) {
  if (!tree || typeof tree !== 'object') return [];
  if (Array.isArray(tree)) return tree.flatMap(node => nodes(node, predicate));
  return [...(predicate(tree) ? [tree] : []), ...nodes(tree.props?.children, predicate)];
}

// Run the real component's event/effect lifecycle with a small DOM boundary stub.
function harness(writeText) {
  const slots = [], listeners = new Map();
  let cursor = 0, effects = [], changed = false, tree, props = {url: 'https://firetrace.test/?view=evidence'};
  const input = {inside: true, focusCount: 0, selections: 0, focus() { this.focusCount++; }, select() { this.selections++; }};
  const trigger = {inside: true, focusCount: 0, focus() { this.focusCount++; }};
  const root = {contains: target => target?.inside === true};
  const document = {
    addEventListener(name, callback) { if (!listeners.has(name)) listeners.set(name, new Set()); listeners.get(name).add(callback); },
    removeEventListener(name, callback) { listeners.get(name)?.delete(callback); },
  };
  const hooks = {...React,
    useState(initial) {
      const i = cursor++;
      if (!(i in slots)) slots[i] = typeof initial === 'function' ? initial() : initial;
      return [slots[i], next => { const value = typeof next === 'function' ? next(slots[i]) : next; changed ||= !Object.is(value, slots[i]); slots[i] = value; }];
    },
    useRef(initial) { const i = cursor++; return slots[i] ||= {current: initial}; },
    useEffect(effect, deps) {
      const i = cursor++, previous = slots[i];
      if (!previous || deps.some((value, index) => !Object.is(value, previous.deps[index]))) {
        effects.push(() => { previous?.cleanup?.(); slots[i] = {deps, cleanup: effect()}; });
      }
    },
    useId: () => 'share-test',
  };
  const module = {exports: {}};
  new Function('require', 'module', 'exports', 'document', 'navigator', compiled)(name => {
    if (name === 'react') return hooks;
    if (name.endsWith('.css')) return {};
    return require(name);
  }, module, module.exports, document, {clipboard: writeText ? {writeText} : undefined});
  const Component = module.exports.default;
  function render(next = props) {
    props = next;
    for (let pass = 0; pass < 8; pass++) {
      cursor = 0; effects = []; changed = false; tree = Component(props);
      for (const node of nodes(tree, node => node.ref)) node.ref.current = node.type === 'input' ? input : node.type === 'button' ? trigger : root;
      for (const effect of effects) effect();
      if (!changed) return tree;
    }
    throw new Error('ShareView render did not settle');
  }
  return {
    render, input, trigger,
    get tree() { return tree; },
    get open() { return nodes(tree, node => node.props?.className === 'share-panel').length > 0; },
    copy() { return nodes(tree, node => node.type === 'button' && 'aria-expanded' in node.props)[0].props.onClick(); },
    dispatch(name, target) { for (const listener of listeners.get(name) || []) listener({target}); },
    listenerCount(name) { return listeners.get(name)?.size || 0; },
    unmount() { for (const slot of slots) slot?.cleanup?.(); },
  };
}

test('share details dismiss outside without stealing focus or accepting a late clipboard result', async () => {
  let finish;
  const view = harness(() => new Promise(resolve => { finish = resolve; }));
  view.render();
  const pending = view.copy(); view.render();
  assert.equal(view.open, true);
  view.dispatch('pointerdown', {inside: true}); view.render();
  assert.equal(view.open, true, 'interacting with the link keeps the panel open');
  view.dispatch('pointerdown', {inside: false}); view.render();
  assert.equal(view.open, false, 'moving on to another control dismisses the popover');
  assert.equal(view.trigger.focusCount, 0, 'outside dismissal preserves the new focus destination');
  finish(); await pending; view.render();
  assert.equal(view.open, false);
  assert.equal(nodes(view.tree, node => node.type === require('lucide-react').Check).length, 0, 'an obsolete clipboard result must not report success');
  assert.equal(view.listenerCount('pointerdown'), 0);
  assert.equal(view.listenerCount('focusin'), 0);
  view.unmount();
});

test('clipboard fallback selects the link and outside keyboard focus dismisses it', async () => {
  const view = harness();
  view.render(); await view.copy(); view.render();
  assert.equal(view.open, true);
  assert.ok(view.input.focusCount > 0);
  assert.ok(view.input.selections > 0);
  view.dispatch('focusin', {inside: true}); view.render();
  assert.equal(view.open, true);
  view.dispatch('focusin', {inside: false}); view.render();
  assert.equal(view.open, false);
  assert.equal(view.trigger.focusCount, 0);
  view.unmount();
});

test('Escape closes only the share panel, restores its trigger, and URL changes cancel old copies', async () => {
  let finish;
  const view = harness(() => new Promise(resolve => { finish = resolve; }));
  view.render(); const pending = view.copy(); view.render();
  let prevented = false, stopped = false;
  view.tree.props.onKeyDown({key: 'Escape', preventDefault() { prevented = true; }, stopPropagation() { stopped = true; }});
  view.render();
  assert.equal(view.open, false);
  assert.equal(view.trigger.focusCount, 1);
  assert.equal(prevented && stopped, true, 'Escape must not also dismiss the parent evidence drawer');
  finish(); await pending;
  const nextPending = view.copy(); view.render();
  view.render({url: 'https://firetrace.test/?view=methods'});
  assert.equal(view.open, false);
  finish(); await nextPending; view.render();
  assert.equal(view.open, false);
  view.unmount();
  assert.equal(view.listenerCount('pointerdown'), 0);
  assert.equal(view.listenerCount('focusin'), 0);
});
