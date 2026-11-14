import {spawnSync} from 'node:child_process';
import {readdirSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const directory = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(directory, '..');
const prechecks = ['data-contract.mjs', 'anomalies.mjs', 'demand-renderer.mjs'];

function run(args) {
  const result = spawnSync(process.execPath, args, {cwd: webRoot, stdio: 'inherit'});
  if (result.error) console.error(result.error.message);
  if (result.status !== 0) process.exit(result.status || 1);
}

for (const file of prechecks) run([path.join(directory, file)]);
const suites = readdirSync(directory, {withFileTypes: true})
  .filter(entry => entry.isFile() && entry.name.endsWith('.mjs') && entry.name !== 'run.mjs' && !prechecks.includes(entry.name))
  .map(entry => entry.name).sort().map(file => path.join(directory, file));
if (!suites.length) throw new Error('No web test suites were found.');
run(['--test', ...suites]);
