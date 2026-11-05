export type DesktopApiResponse = Record<string, unknown>;

type LuminaDesktopBridge = {
  requestApi: (pathname: string, method: string, body?: unknown) => Promise<unknown>;
  agentHealth: () => Promise<{ connected: boolean; status: string }>;
  agentConfigured: () => Promise<boolean>;
  saveAgentToken: (token: string) => Promise<{ saved: boolean }>;
  listAgentApps: () => Promise<{ items: { id: string; available: boolean }[]; platform: string; total: number }>;
  openAgentApp: (appAlias: string) => Promise<{ status: string; app: string; platform: string }>;
  hide: () => void;
  toggleChat: () => void;
  setChatOpen: (open: boolean) => void;
  onOpenChat: (callback: () => void) => () => void;
  onToggleChat: (callback: () => void) => () => void;
};

declare global {
  interface Window { luminaDesktop?: LuminaDesktopBridge }
}

export async function desktopApi<T>(pathname: string, method = 'GET', body?: unknown): Promise<T> {
  if (window.luminaDesktop) {
    return await window.luminaDesktop.requestApi(pathname, method, body) as T;
  }
  const response = await fetch(`http://127.0.0.1:8000${pathname}`, {
    method,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let result: unknown;
  try { result = text ? JSON.parse(text) : null; } catch { result = text; }
  if (!response.ok) throw new Error(typeof result === 'string' ? result : JSON.stringify(result));
  return result as T;
}
