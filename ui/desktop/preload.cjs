const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('luminaDesktop', {
  requestApi: (pathname, method, body) => ipcRenderer.invoke('lumina:api-request', { pathname, method, body }),
  agentHealth: () => ipcRenderer.invoke('lumina:agent-health'),
  agentConfigured: () => ipcRenderer.invoke('lumina:agent-configured'),
  saveAgentToken: (token) => ipcRenderer.invoke('lumina:agent-save-token', token),
  listAgentApps: () => ipcRenderer.invoke('lumina:agent-list-apps'),
  openAgentApp: (appAlias) => ipcRenderer.invoke('lumina:agent-open-app', appAlias),
  hide: () => ipcRenderer.send('lumina:hide'),
  toggleChat: () => ipcRenderer.send('lumina:toggle-chat'),
  setChatOpen: (open) => ipcRenderer.send('lumina:chat-state', Boolean(open)),
  onOpenChat: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('lumina:open-chat', handler);
    return () => ipcRenderer.removeListener('lumina:open-chat', handler);
  },
  onToggleChat: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('lumina:toggle-chat', handler);
    return () => ipcRenderer.removeListener('lumina:toggle-chat', handler);
  },
});
