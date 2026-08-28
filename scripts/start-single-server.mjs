import { spawn, spawnSync } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import fs from 'node:fs';

const root = process.cwd();
const isWindows = process.platform === 'win32';

// 1. Python executableni aniqlash (Virtual environment ustunligi bilan)
let pythonBin = isWindows ? 'python' : 'python3';
const venvPythonWin = path.join(root, '.venv', 'Scripts', 'python.exe');
const venvPythonUnix = path.join(root, '.venv', 'bin', 'python');

if (fs.existsSync(venvPythonWin)) {
  pythonBin = venvPythonWin;
} else if (fs.existsSync(venvPythonUnix)) {
  pythonBin = venvPythonUnix;
}

console.log(`[AIDA Launcher] Python ishlatilmoqda: ${pythonBin}`);

// 2. Frontendni build qilish
console.log('\n[AIDA Launcher] React frontend yig\'ilmoqda (vite build)...');
const buildRes = spawnSync('npm', ['run', 'build', '--prefix', 'frontend'], {
  cwd: root,
  stdio: 'inherit',
  shell: true,
});

if (buildRes.status !== 0) {
  console.error('[AIDA Launcher] Frontendni yig\'ishda xatolik yuz berdi!');
  process.exit(buildRes.status || 1);
}

console.log('[AIDA Launcher] Frontend muvaffaqiyatli yig\'ildi!');

// 3. Django serverni ishga tushirish (port 8001)
console.log('\n[AIDA Launcher] Django backend server ishga tushirilmoqda...');
console.log('ðŸ”— Browser orqali kirish manzili: http://127.0.0.1:8001');

const django = spawn(pythonBin, ['manage.py', 'runserver', '127.0.0.1:8001'], {
  cwd: root,
  stdio: 'inherit',
  env: {
    ...process.env,
    DJANGO_DEBUG: 'true',
  },
  shell: true,
});

django.on('error', (err) => {
  console.error(`[AIDA Backend Error]: ${err.message}`);
});

process.on('SIGINT', () => {
  django.kill('SIGINT');
  process.exit(0);
});
process.on('SIGTERM', () => {
  django.kill('SIGTERM');
  process.exit(0);
});
