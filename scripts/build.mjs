import {spawnSync} from 'node:child_process';
import {cpSync, mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
// Invoke Node entrypoints directly so Windows does not need shell command quoting.
for (const [entry, args] of [
  ['typescript/bin/tsc', ['--noEmit']],
  ['vite/bin/vite.js', ['build']],
]) {
  const result = spawnSync(process.execPath, [path.join(root, 'web/node_modules', entry), ...args],
    {cwd: path.join(root, 'web'), stdio: 'inherit'});
  if (result.status !== 0) process.exit(result.status || 1);
}
mkdirSync(path.join(root, 'dist'), {recursive: true});
cpSync(path.join(root, 'web/dist'), path.join(root, 'dist'), {recursive: true});
console.log('Static deployment assets prepared in dist/');
