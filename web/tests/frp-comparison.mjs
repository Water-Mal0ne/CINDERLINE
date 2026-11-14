import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';

const require = createRequire(new URL('../package.json', import.meta.url));
const ts = require('typescript');
const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
const source = readFileSync(new URL('../src/FrpComparison.tsx', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source.replaceAll('import.meta.env.BASE_URL', JSON.stringify('/firetrace/')), {
  compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX},
}).outputText;
const componentModule = {exports: {}};
new Function('require', 'module', 'exports', compiled)(name => name.endsWith('.css') ? {} : require(name), componentModule, componentModule.exports);
const {parseFrpPayload, FrpEvidence} = componentModule.exports;
const published = JSON.parse(readFileSync(new URL('../public/data/frp.json', import.meta.url), 'utf8'));
const copy = () => structuredClone(published);

test('published FRP evidence renders all stream estimates without promoting Terra', () => {
  const data = parseFrpPayload(copy());
  const markup = renderToStaticMarkup(React.createElement(FrpEvidence, {data}));
  for (const row of data.streams) {
    const article = markup.match(new RegExp(`<article[^>]+data-frp-stream="${row.stream}"[^>]*>([\\s\\S]*?)</article>`))?.[1];
    assert.ok(article, `${row.stream} has an evidence card`);
    assert.ok(article.includes(row.count_sunday.toFixed(3)), `${row.stream} count from payload`);
    assert.ok(article.includes(row.frp_sunday.toFixed(3)), `${row.stream} FRP from payload`);
    assert.match(article, row.passed ? /Criteria met/ : /Criteria not met/);
  }
  const terra = markup.match(/data-frp-stream="Terra"[^>]*>([\s\S]*?)<\/article>/)[1];
  assert.match(terra, /interval includes zero/);
  assert.doesNotMatch(terra, /Criteria met/);
  assert.match(markup, /REAL FIRMS DATA, US daytime 2013-2024/);
});

test('every weekday profile and table value uses the published paired observations', () => {
  const data = parseFrpPayload(copy());
  const markup = renderToStaticMarkup(React.createElement(FrpEvidence, {data}));
  assert.equal((markup.match(/class="frp-profile"/g) || []).length, data.streams.length);
  for (const row of data.streams) {
    for (const values of [row.count_weekdays, row.frp_weekdays]) {
      for (const value of values) assert.ok(markup.includes(value.toFixed(3)));
    }
  }
  assert.match(markup, /same detections/);
  assert.match(markup, /not harmonized FRP/);
});

test('evidence links work below a subpath and Git chronology remains visible', () => {
  const data = parseFrpPayload(copy());
  const markup = renderToStaticMarkup(React.createElement(FrpEvidence, {data}));
  for (const path of Object.values(data.evidence)) assert.ok(markup.includes(`/firetrace/${path.replace(/^\/+/, '')}`));
  assert.match(markup, /was added after the results/);
  assert.ok(markup.includes(`${data.protocol.git_receipt_commit}/DECISIONS.md`));
  assert.match(markup, /not energy, emissions, burned area or fire counts/);
});

test('nonfinite, truncated and internally contradictory numerical evidence is rejected', () => {
  const invalid = [
    data => { data.streams[0].count_weekdays[0] = NaN; },
    data => { data.streams[0].frp_weekdays.pop(); },
    data => { data.streams[0].count_sunday += .1; },
    data => { data.streams[0].ci_low = data.streams[0].ci_high + 1; },
    data => { data.streams.find(row => row.stream === 'Terra').passed = true; },
    data => { data.masks.find(mask => mask.name === 'padded').streams.find(row => row.stream === 'Aqua').passed = false; },
  ];
  for (const mutate of invalid) { const data = copy(); mutate(data); assert.throws(() => parseFrpPayload(data)); }
});

test('unverified gates, different country scopes and unsafe evidence links are rejected', () => {
  const invalid = [
    data => { data.data_gate.passed = false; },
    data => { data.verdict = 'fail'; },
    data => { data.scope.country = 'Nepal'; },
    data => { data.protocol.git_receipt_after_original_results = false; },
    data => { data.evidence.summary = 'https://example.com/unverified.csv'; },
    data => { data.evidence.report = '/evidence/frp/../../other.md'; },
  ];
  for (const mutate of invalid) { const data = copy(); mutate(data); assert.throws(() => parseFrpPayload(data)); }
});
