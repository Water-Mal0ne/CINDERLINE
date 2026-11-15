import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import ts from 'typescript';

const source = readFileSync(new URL('../src/workspaceNavigation.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions: {target: ts.ScriptTarget.ES2021, module: ts.ModuleKind.ES2022}}).outputText;
const {parseWorkspaceNavigation, withWorkspaceNavigation} = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));

test('workspace links restore each presentation choice without changing scientific filters', () => {
  const original = new URL('https://preview.example/?v=1&region=Egypt&start=2024-01-01&end=2024-12-31&scale=raw&week=2024-04-08#main');
  for (const section of ['calendar', 'patterns', 'earth']) {
    for (const calendar of ['weekly', 'monthly']) {
      for (const pattern of ['instruments', 'seasons', 'anomalies']) {
        const state = {section, calendar, pattern};
        const linked = new URL(withWorkspaceNavigation(original.href, state));
        assert.deepEqual(parseWorkspaceNavigation(linked.search), state);
        for (const [key, value] of original.searchParams) assert.equal(linked.searchParams.get(key), value);
        assert.equal(linked.hash, '#main');
      }
    }
  }
});

test('old and malformed workspace links use a safe calendar view', () => {
  assert.equal(parseWorkspaceNavigation('').calendar, 'monthly');
  const defaults = {section: 'calendar', calendar: 'weekly', pattern: 'instruments'};
  assert.deepEqual(parseWorkspaceNavigation('?view=rhythm&region=Nepal'), defaults);
  assert.deepEqual(parseWorkspaceNavigation('?workspace=unknown&calendar=hourly&pattern=forecast'), defaults);
  const cleaned = new URL(withWorkspaceNavigation('https://preview.example/?workspace=earth&calendar=monthly&pattern=seasons&view=rhythm', defaults));
  assert.equal(cleaned.search, '?view=rhythm');
});
