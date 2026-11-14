import {spawnSync} from 'node:child_process';
import {cpSync, mkdirSync, rmSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
await import('./prepare-map.mjs');
// Invoke Node entrypoints directly so Windows does not need shell command quoting.
for (const [entry, args] of [
  ['typescript/bin/tsc', ['--noEmit']],
  ['vite/bin/vite.js', ['build']],
]) {
  const result = spawnSync(process.execPath, [path.join(root, 'web/node_modules', entry), ...args],
    {cwd: path.join(root, 'web'), stdio: 'inherit'});
  if (result.status !== 0) process.exit(result.status || 1);
}
const target = path.resolve(root, 'dist');
if (path.dirname(target) !== root || path.basename(target) !== 'dist') throw new Error('Invalid build output path');
rmSync(target, {recursive:true, force:true});
mkdirSync(target, {recursive: true});
cpSync(path.join(root, 'web/dist'), target, {recursive: true});
console.log('Static deployment assets prepared in dist/');
