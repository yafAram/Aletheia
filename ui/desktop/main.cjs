const { app, BrowserWindow, Tray, Menu, ipcMain, globalShortcut, nativeImage } = require('electron');
const { spawn } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const settingsPath = () => path.join(app.getPath('userData'), 'settings.json');
function readSettings() {
  try { return JSON.parse(fs.readFileSync(settingsPath(), 'utf8')); } catch { return {}; }
}
function writeSettings(settings) {
  fs.mkdirSync(path.dirname(settingsPath()), { recursive: true });
  fs.writeFileSync(settingsPath(), JSON.stringify(settings, null, 2), { mode: 0o600 });
  try { fs.chmodSync(settingsPath(), 0o600); } catch {}
}
function agentTokenFile() {
  return process.env.ALETHEIA_DESKTOP_TOKEN_FILE || path.join(os.homedir(), '.config', 'aletheia', 'desktop-agent-token');
}
function getAgentToken() {
  try {
    const token = fs.readFileSync(agentTokenFile(), 'utf8').trim();
    if (token.length >= 20) return token;
  } catch {}
  // Compatibility fallback for installations that have not launched the new agent yet.
  return String(process.env.ALETHEIA_DESKTOP_TOKEN || readSettings().agentToken || '');
}
async function agentRequest(pathname, method = 'GET', body) {
  if (!['/v1/apps', '/v1/apps/open'].includes(pathname)) throw new Error('Ruta del agente no permitida.');
  const token = getAgentToken();
  if (!token) throw new Error('Configura el token del agente en Lumina.');
  const response = await fetch(`${AGENT_ORIGIN}${pathname}`, {
    method, headers: { Authorization: `Bearer ${token}`, ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
    body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(8000),
  });
  const text = await response.text();
  let payload; try { payload = text ? JSON.parse(text) : null; } catch { payload = text; }
  if (!response.ok) throw new Error(typeof payload === 'string' ? payload : JSON.stringify(payload));
  return payload;
}

const DEV_URL = 'http://127.0.0.1:5173/?desktop=1';
const API_ORIGIN = process.env.ALETHEIA_API_ORIGIN || 'http://127.0.0.1:8000';
const AGENT_ORIGIN = process.env.ALETHEIA_DESKTOP_AGENT_ORIGIN || 'http://127.0.0.1:8765';
let desktopAgentProcess = null;
let mainWindow = null;
let tray = null;
let viteProcess = null;
let quitting = false;

function appRoot() {
  return app.isPackaged ? app.getAppPath() : path.resolve(__dirname, '..');
}

function autostartFile() {
  return path.join(os.homedir(), '.config', 'autostart', 'lumina-companion.desktop');
}

function isAutostartEnabled() {
  if (process.platform === 'linux') return fs.existsSync(autostartFile());
  try { return Boolean(app.getLoginItemSettings().openAtLogin); } catch { return false; }
}

function setAutostartEnabled(enabled) {
  if (process.platform === 'linux') {
    const file = autostartFile();
    if (!enabled) {
      try { fs.rmSync(file, { force: true }); } catch {}
      return;
    }
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const execPath = process.execPath.replaceAll('"', '\\"');
    const entryPath = path.join(__dirname, 'main.cjs').replaceAll('"', '\\"');
    const command = app.isPackaged ? `"${execPath}"` : `"${execPath}" "${entryPath}"`;
    fs.writeFileSync(file, `[Desktop Entry]\nType=Application\nName=Lumina\nComment=Compañera de escritorio Lumina\nExec=${command}\nTerminal=false\nX-GNOME-Autostart-enabled=true\n`, { mode: 0o600 });
    return;
  }
  app.setLoginItemSettings({ openAtLogin: enabled, path: process.execPath, args: app.isPackaged ? [] : [path.join(__dirname, 'main.cjs')] });
}

async function waitForVite(url, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return true;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  return false;
}

async function agentIsHealthy() {
  try {
    const response = await fetch(`${AGENT_ORIGIN}/health`, { signal: AbortSignal.timeout(1200) });
    return response.ok;
  } catch { return false; }
}

async function startDesktopAgentIfNeeded() {
  if (await agentIsHealthy()) return;
  const projectRoot = path.resolve(__dirname, '..', '..');
  const candidates = process.platform === 'win32'
    ? [path.join(projectRoot, '.venv-desktop', 'Scripts', 'python.exe'), 'python']
    : [path.join(projectRoot, '.venv-desktop', 'bin', 'python'), 'python3'];
  let python = candidates.find((candidate) => candidate !== 'python3' && candidate !== 'python' && fs.existsSync(candidate));
  if (!python) python = process.platform === 'win32' ? 'python' : 'python3';
  const tokenFile = agentTokenFile();
  fs.mkdirSync(path.dirname(tokenFile), { recursive: true, mode: 0o700 });
  try { fs.chmodSync(path.dirname(tokenFile), 0o700); } catch {}
  desktopAgentProcess = spawn(python, ['-m', 'desktop_agent'], {
    cwd: projectRoot,
    stdio: 'ignore',
    windowsHide: true,
    env: { ...process.env, ALETHEIA_DESKTOP_TOKEN_FILE: tokenFile },
  });
  desktopAgentProcess.on('error', (error) => console.error('No se pudo iniciar el agente local:', error));
  const started = Date.now();
  while (Date.now() - started < 10000) {
    if (await agentIsHealthy()) return;
    if (desktopAgentProcess.exitCode !== null) break;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error('No pude iniciar el agente local. Comprueba .venv-desktop y desktop_agent/requirements.txt. Si hay una instancia antigua, ciérrala una vez y vuelve a abrir Lumina.');
}

async function startDevServer() {
  if (app.isPackaged) return;
  const root = appRoot();
  viteProcess = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'dev', '--', '--host', '127.0.0.1'], {
    cwd: root,
    stdio: 'ignore',
    windowsHide: true,
    shell: process.platform === 'win32',
    env: { ...process.env, BROWSER: 'none' },
  });
  const ready = await waitForVite('http://127.0.0.1:5173');
  if (!ready) throw new Error('Vite no inició en http://127.0.0.1:5173. Ejecuta npm install dentro de ui y vuelve a intentarlo.');
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 390,
    height: 620,
    minWidth: 320,
    minHeight: 390,
    show: false,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    resizable: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    title: 'Lumina',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  mainWindow.setAlwaysOnTop(true, 'floating');
  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: false });
  mainWindow.on('close', (event) => {
    if (!quitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
  mainWindow.on('closed', () => { mainWindow = null; });

  if (app.isPackaged) {
    void mainWindow.loadFile(path.join(appRoot(), 'dist', 'index.html'), { query: { desktop: '1' } });
  } else {
    void mainWindow.loadURL(DEV_URL);
  }
  mainWindow.once('ready-to-show', () => mainWindow && mainWindow.show());
}

function showWindow() {
  if (!mainWindow) createWindow();
  else { mainWindow.show(); mainWindow.focus(); }
}

function toggleWindow() {
  if (mainWindow && mainWindow.isVisible()) mainWindow.hide();
  else showWindow();
}

function createTray() {
  // Small generated monochrome icon, so the patch does not depend on external artwork.
  const iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14" fill="#08232b" stroke="#62f6e7" stroke-width="2"/><path d="M8 10 4 4l9 4M24 10l4-6-9 4" fill="#62f6e7"/><ellipse cx="16" cy="17" rx="9" ry="10" fill="#e7ffff"/><ellipse cx="12.5" cy="16" rx="2" ry="3" fill="#008f9c"/><ellipse cx="19.5" cy="16" rx="2" ry="3" fill="#008f9c"/><path d="M13 21q3 3 6 0" fill="none" stroke="#008f9c" stroke-width="1.5" stroke-linecap="round"/></svg>`;
  const dataUrl = `data:image/svg+xml;base64,${Buffer.from(iconSvg).toString('base64')}`;
  tray = new Tray(nativeImage.createFromDataURL(dataUrl));
  tray.setToolTip('Lumina');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Mostrar / ocultar Lumina', click: toggleWindow },
    { label: 'Abrir chat', click: () => { showWindow(); mainWindow.webContents.send('lumina:open-chat'); } },
    { type: 'separator' },
    { label: 'Iniciar con el sistema', type: 'checkbox', checked: isAutostartEnabled(), click: (item) => {
      try { setAutostartEnabled(item.checked); } catch (error) {
        item.checked = !item.checked;
        console.error('No se pudo cambiar el inicio automático:', error);
      }
    } },
    { type: 'separator' },
    { label: 'Salir de Lumina', click: () => { quitting = true; app.quit(); } },
  ]));
  tray.on('click', toggleWindow);
}

function safeApiPath(pathname) {
  return typeof pathname === 'string' && pathname.startsWith('/api/') && !pathname.includes('..');
}

ipcMain.handle('lumina:api-request', async (_event, request) => {
  const { pathname, method = 'GET', body } = request || {};
  if (!safeApiPath(pathname)) throw new Error('Ruta API no permitida.');
  if (!['GET', 'POST'].includes(method)) throw new Error('Método no permitido.');
  const response = await fetch(`${API_ORIGIN}${pathname}`, {
    method,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    // CPU inference on this machine has taken 100-115 seconds for a long prompt.
    signal: AbortSignal.timeout(300000),
  });
  const text = await response.text();
  let payload;
  try { payload = text ? JSON.parse(text) : null; } catch { payload = text; }
  if (!response.ok) {
    const detail = typeof payload === 'string' ? payload : JSON.stringify(payload);
    throw new Error(detail || `La API respondió HTTP ${response.status}.`);
  }
  return payload;
});

ipcMain.handle('lumina:agent-configured', () => Boolean(getAgentToken()));
ipcMain.handle('lumina:agent-save-token', (_event, token) => {
  if (typeof token !== 'string' || token.trim().length < 20 || token.length > 512) throw new Error('El token parece incompleto. Pega el token completo del agente.');
  const settings = readSettings(); settings.agentToken = token.trim(); writeSettings(settings);
  return { saved: true };
});
ipcMain.handle('lumina:agent-list-apps', () => agentRequest('/v1/apps'));
ipcMain.handle('lumina:agent-open-app', (_event, appAlias) => {
  if (typeof appAlias !== 'string' || !/^[a-zA-Z0-9_]{1,64}$/.test(appAlias)) throw new Error('Alias de aplicación no válido.');
  return agentRequest('/v1/apps/open', 'POST', { app: appAlias });
});
ipcMain.handle('lumina:agent-health', async () => {
  try {
    const response = await fetch(`${AGENT_ORIGIN}/health`, { signal: AbortSignal.timeout(2500) });
    if (!response.ok) return { connected: false, status: `HTTP ${response.status}` };
    return { connected: true, status: 'conectado' };
  } catch {
    return { connected: false, status: 'desconectado' };
  }
});
ipcMain.on('lumina:hide', () => mainWindow && mainWindow.hide());
ipcMain.on('lumina:toggle-chat', () => mainWindow && mainWindow.webContents.send('lumina:toggle-chat'));
ipcMain.on('lumina:chat-state', (_event, open) => {
  if (!mainWindow) return;
  const [width] = mainWindow.getSize();
  mainWindow.setSize(width, open ? 900 : 590, true);
});
ipcMain.on('lumina:open-external', (_event, url) => {
  // No arbitrary external navigation from the renderer; external links are not currently needed.
  if (typeof url === 'string' && /^https:\/\//i.test(url)) {
    const { shell } = require('electron');
    void shell.openExternal(url);
  }
});

app.whenReady().then(async () => {
  try {
    await startDesktopAgentIfNeeded();
    await startDevServer();
    createWindow();
    createTray();
    globalShortcut.register('CommandOrControl+Shift+L', toggleWindow);
  } catch (error) {
    console.error(error);
    app.quit();
  }
});

app.on('before-quit', () => {
  quitting = true;
  globalShortcut.unregisterAll();
  if (viteProcess && !viteProcess.killed) viteProcess.kill();
  if (desktopAgentProcess && !desktopAgentProcess.killed) desktopAgentProcess.kill();
});
