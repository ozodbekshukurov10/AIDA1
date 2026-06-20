import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const isWindows = process.platform === 'win32';
const children = [];

mkdirSync(path.join(root, 'logs'), { recursive: true });

function startProcess(label, command, args, extraEnv = {}) {
  const child = spawn(command, args, {
    cwd: root,
    stdio: 'inherit',
    env: { ...process.env, ...extraEnv },
    shell: false,
  });
  child.on('error', (error) => {
    console.warn(`[${label}] ${error.message}`);
  });
  child.on('exit', (code, signal) => {
    if (code && code !== 0) console.warn(`[${label}] exited with code ${code}`);
    if (signal) console.warn(`[${label}] stopped by ${signal}`);
  });
  children.push(child);
  return child;
}

function runOnce(label, command, args, extraEnv = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd: root,
      stdio: 'inherit',
      env: { ...process.env, ...extraEnv },
      shell: false,
    });
    child.on('error', (error) => {
      console.warn(`[${label}] ${error.message}`);
      resolve(false);
    });
    child.on('exit', (code) => {
      if (code && code !== 0) console.warn(`[${label}] exited with code ${code}`);
      resolve(code === 0);
    });
  });
}

async function isOllamaReady() {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1200);
    const response = await fetch('http://127.0.0.1:11434/api/tags', { signal: controller.signal });
    clearTimeout(timer);
    return response.ok;
  } catch {
    return false;
  }
}

async function startOllamaIfNeeded() {
  if (String(process.env.AIDA_OLLAMA_AUTOSTART ?? 'true').toLowerCase() === 'false') return;
  if (await isOllamaReady()) return;
  startProcess('ollama', 'ollama', ['serve']);
}

function shutdown() {
  for (const child of children) {
    if (!child.killed) child.kill(isWindows ? undefined : 'SIGTERM');
  }
  process.exit(0);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

await startOllamaIfNeeded();

const python = process.env.PYTHON || (isWindows ? 'python' : 'python3');
const djangoEnv = {
  DJANGO_DEBUG: process.env.DJANGO_DEBUG || 'true',
  DJANGO_ALLOWED_HOSTS: process.env.DJANGO_ALLOWED_HOSTS || '127.0.0.1,localhost,.muleusercontent.com',
  AIDA_PROVIDER: process.env.AIDA_PROVIDER || 'local',
  AIDA_API_URL: process.env.AIDA_API_URL || 'http://localhost:11434',
};
await runOnce('migrate', python, ['manage.py', 'migrate', '--noinput'], djangoEnv);
startProcess('django', python, ['manage.py', 'runserver', '127.0.0.1:8001'], djangoEnv);

const viteBin = path.join(root, 'node_modules', '.bin', isWindows ? 'vite.cmd' : 'vite');
startProcess('vite', viteBin, ['--port=3000', '--host=0.0.0.0']);
