import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(import.meta.dirname, '..');
const isWindows = process.platform === 'win32';
const children = [];

function startProcess(label, command, args, extraEnv = {}) {
  const child = spawn(command, args, {
    cwd: root,
    stdio: 'inherit',
    env: { ...process.env, ...extraEnv },
  });
  child.on('error', (error) => console.warn(`[${label}] ${error.message}`));
  child.on('exit', (code, signal) => {
    if (code && code !== 0) console.warn(`[${label}] exited with code ${code}`);
    if (signal) console.warn(`[${label}] stopped by ${signal}`);
  });
  children.push(child);
  return child;
}

function shutdown() {
  for (const child of children) {
    if (!child.killed) child.kill(isWindows ? undefined : 'SIGTERM');
  }
  process.exit(0);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

const viteBin = path.join(root, 'node_modules', '.bin', isWindows ? 'vite.cmd' : 'vite');
startProcess('vite', viteBin, ['--port=3000', '--host=0.0.0.0']);

console.log('\n  AIDA Frontend started on http://localhost:3000');
console.log('  Backend API expected at http://127.0.0.1:8001\n');
