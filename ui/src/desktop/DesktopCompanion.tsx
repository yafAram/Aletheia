import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { desktopApi } from './desktopApi';

type Mood = 'idle' | 'thinking' | 'speaking' | 'happy' | 'curious' | 'tired';
type ChatResult = { response: string; emotion_state?: { mood?: string; energy?: number; curiosity?: number; affection?: number }; memory_items?: number };
type TtsResult = { audio_url: string };
type ChatMessage = { role: 'you' | 'lumina'; text: string };
type AgentHealth = { connected: boolean; status: string };
type AgentApp = { id: string; available: boolean };

function LuminaAvatar({ mood, onClick }: { mood: Mood; onClick: () => void }) {
  return <button className={`luminaAvatar mood-${mood}`} onClick={onClick} aria-label="Abrir chat con Lumina" title="Hablar con Lumina">
    <span className="avatarAura" />
    <span className="hairBack" />
    <span className="tail tailLeft"><i /><i /><i /></span>
    <span className="tail tailRight"><i /><i /><i /></span>
    <span className="avatarHead">
      <span className="bang bangLeft" /><span className="bang bangCenter" /><span className="bang bangRight" />
      <span className="ear earLeft" /><span className="ear earRight" />
      <span className="eye eyeLeft"><i /></span><span className="eye eyeRight"><i /></span>
      <span className="blush blushLeft" /><span className="blush blushRight" /><span className="avatarMouth" />
    </span>
    <span className="avatarNeck" />
    <span className="avatarBody"><i className="collar" /><i className="tie" /><i className="bodyGem" /></span>
    <span className="avatarSpark sparkOne">✦</span><span className="avatarSpark sparkTwo">✧</span>
  </button>;
}

export default function DesktopCompanion() {
  const [chatOpen, setChatOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: 'lumina', text: '¡Hola! Estoy aquí. Pulsa sobre mí cuando quieras conversar. ✨' }]);
  const [mood, setMood] = useState<Mood>('idle');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [agent, setAgent] = useState<AgentHealth>({ connected: false, status: 'comprobando' });
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [agentSettingsOpen, setAgentSettingsOpen] = useState(false);
  const [agentTokenDraft, setAgentTokenDraft] = useState('');
  const [agentConfigured, setAgentConfigured] = useState(false);
  const [agentApps, setAgentApps] = useState<AgentApp[]>([]);
  const [selectedAgentApp, setSelectedAgentApp] = useState('');
  const [agentMessage, setAgentMessage] = useState('');
  const [agentBusy, setAgentBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const chatOpenRef = useRef(false);
  function updateChatOpen(open: boolean | ((current: boolean) => boolean)) {
    const next = typeof open === 'function' ? open(chatOpenRef.current) : open;
    chatOpenRef.current = next;
    setChatOpen(next);
    window.luminaDesktop?.setChatOpen(next);
  }
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const bridge = window.luminaDesktop;
    if (!bridge) return;
    const offOpen = bridge.onOpenChat(() => updateChatOpen(true));
    const offToggle = bridge.onToggleChat(() => updateChatOpen((open) => !open));
    return () => { offOpen(); offToggle(); };
  }, []);

  useEffect(() => {
    let active = true;
    const check = async () => {
      try {
        await desktopApi('/api/emotion');
        if (active) setBackendOnline(true);
      } catch { if (active) setBackendOnline(false); }
      try {
        const status = window.luminaDesktop ? await window.luminaDesktop.agentHealth() : { connected: false, status: 'solo escritorio' };
        const configured = window.luminaDesktop ? await window.luminaDesktop.agentConfigured() : false;
        if (active) { setAgent(status); setAgentConfigured(configured); }
      } catch { if (active) setAgent({ connected: false, status: 'desconectado' }); }
    };
    void check();
    const id = window.setInterval(check, 12000);
    return () => { active = false; window.clearInterval(id); };
  }, []);

  useEffect(() => {
    if (chatOpen) {
      const id = window.setTimeout(() => inputRef.current?.focus(), 120);
      return () => window.clearTimeout(id);
    }
  }, [chatOpen]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, busy]);

  function moodFromResponse(result: ChatResult): Mood {
    const moodName = String(result.emotion_state?.mood ?? '').toLowerCase();
    if (moodName.includes('happy') || moodName.includes('feliz')) return 'happy';
    if ((result.emotion_state?.curiosity ?? 0) >= 0.65) return 'curious';
    if ((result.emotion_state?.energy ?? 1) < 0.3) return 'tired';
    return 'idle';
  }

  async function speak(text: string) {
    if (!voiceEnabled) return;
    try {
      const tts = await desktopApi<TtsResult>('/api/tts/speak', 'POST', { text, emotion: mood });
      const url = new URL(tts.audio_url, 'http://127.0.0.1:8000').toString();
      const audio = new Audio(url);
      setMood('speaking');
      audio.onended = () => setMood('idle');
      audio.onerror = () => setMood('idle');
      await audio.play();
    } catch {
      setMood('idle');
      // El chat sigue funcionando aunque TTS no esté configurado o disponible.
    }
  }


  async function saveAgentToken() {
    if (!window.luminaDesktop) return;
    setAgentBusy(true); setAgentMessage('');
    try {
      await window.luminaDesktop.saveAgentToken(agentTokenDraft);
      setAgentTokenDraft(''); setAgentConfigured(true); setAgentMessage('Token guardado localmente.');
      const result = await window.luminaDesktop.listAgentApps();
      setAgentApps(result.items); setSelectedAgentApp(result.items.find((item) => item.available)?.id ?? '');
    } catch (agentError) {
      setAgentMessage(agentError instanceof Error ? agentError.message : 'No se pudo guardar el token.');
    } finally { setAgentBusy(false); }
  }

  async function loadAgentApps() {
    if (!window.luminaDesktop) return;
    setAgentBusy(true); setAgentMessage('');
    try {
      const result = await window.luminaDesktop.listAgentApps();
      setAgentApps(result.items); setSelectedAgentApp(result.items.find((item) => item.available)?.id ?? '');
      setAgentMessage(`${result.total} aplicaciones autorizadas en ${result.platform}.`);
    } catch (agentError) {
      setAgentMessage(agentError instanceof Error ? agentError.message : 'No pude consultar las aplicaciones.');
    } finally { setAgentBusy(false); }
  }

  async function openAgentApp() {
    if (!window.luminaDesktop || !selectedAgentApp) return;
    setAgentBusy(true); setAgentMessage('');
    try {
      const result = await window.luminaDesktop.openAgentApp(selectedAgentApp);
      setAgentMessage(`Solicitud enviada: ${result.app}.`);
    } catch (agentError) {
      setAgentMessage(agentError instanceof Error ? agentError.message : 'No pude abrir esa aplicación.');
    } finally { setAgentBusy(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setMessages((current) => [...current, { role: 'you', text }]);
    setDraft(''); setBusy(true); setError(''); setMood('thinking');
    try {
      const result = await desktopApi<ChatResult>('/api/chat', 'POST', { message: text, use_memory: true });
      setMessages((current) => [...current, { role: 'lumina', text: result.response }]);
      setMood(moodFromResponse(result));
      await speak(result.response);
    } catch (requestError) {
      setMood('idle');
      setError(requestError instanceof Error ? requestError.message : 'No pude conectar con Aletheia.');
    } finally { setBusy(false); }
  }

  return <main className={`desktopRoot ${chatOpen ? 'chatIsOpen' : ''}`}>
    <div className="dragHandle"><span className={`connectionDot ${backendOnline ? 'online' : backendOnline === false ? 'offline' : ''}`} />
      <span>LUMINA <small>{backendOnline ? 'en línea' : backendOnline === false ? 'API desconectada' : 'conectando'}</small></span>
      <button className="chromeButton" onClick={() => window.luminaDesktop?.hide()} title="Ocultar a la bandeja" aria-label="Ocultar">−</button>
    </div>
    <div className="avatarStage"><LuminaAvatar mood={busy ? 'thinking' : mood} onClick={() => updateChatOpen((open) => !open)} />
      <div className="avatarCaption">{busy ? 'Estoy pensando…' : mood === 'speaking' ? 'Estoy hablando' : 'Pulsa para conversar'}</div>
    </div>
    {chatOpen && <section className="chatPanel">
      <header className="chatHeader"><div><strong>Habla conmigo</strong><span>Tu compañera local</span></div>
        <button className="chromeButton" onClick={() => updateChatOpen(false)} aria-label="Cerrar chat">×</button></header>
      <div className="chatMessages" ref={chatRef}>
        {messages.map((message, index) => <article className={`bubble bubble-${message.role}`} key={`${index}-${message.role}`}><span>{message.role === 'you' ? 'Tú' : 'Lumina'}</span><p>{message.text}</p></article>)}
        {busy && <article className="bubble bubble-lumina"><span>Lumina</span><p className="thinkingDots">Pensando<span> · </span><span>· </span><span>·</span></p></article>}
        {error && <p className="chatError">{error}</p>}
      </div>
      <form className="chatComposer" onSubmit={submit}>
        <input ref={inputRef} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Escribe un mensaje…" aria-label="Mensaje para Lumina" />
        <button type="submit" disabled={!draft.trim() || busy} aria-label="Enviar mensaje">➤</button>
      </form>
      <footer className="chatFooter"><span>Agente: {agent.connected ? 'conectado' : 'desconectado'}</span>
        <label><input type="checkbox" checked={voiceEnabled} onChange={(event) => setVoiceEnabled(event.target.checked)} /> Voz</label>
        <button type="button" className="agentSettingsToggle" onClick={() => setAgentSettingsOpen((open) => !open)}>{agentSettingsOpen ? 'Cerrar agente' : 'Agente ⚙'}</button>
      </footer>
      {agentSettingsOpen && <section className="agentSettings">
        {!agentConfigured && <form className="agentTokenForm" onSubmit={(event) => { event.preventDefault(); void saveAgentToken(); }}>
          <label htmlFor="agent-token">Token del agente</label>
          <input id="agent-token" type="password" autoComplete="off" value={agentTokenDraft} onChange={(event) => setAgentTokenDraft(event.target.value)} placeholder="Pega ALETHEIA_DESKTOP_TOKEN" />
          <button type="submit" disabled={agentBusy || agentTokenDraft.trim().length < 20}>Guardar</button>
        </form>}
        {agentConfigured && <div className="agentAppForm">
          <button type="button" onClick={() => void loadAgentApps()} disabled={agentBusy}>Cargar aplicaciones</button>
          <select aria-label="Aplicación autorizada" value={selectedAgentApp} onChange={(event) => setSelectedAgentApp(event.target.value)}>
            <option value="">Selecciona una aplicación</option>
            {agentApps.map((item) => <option key={item.id} value={item.id} disabled={!item.available}>{item.id}{item.available ? '' : ' (no instalada)'}</option>)}
          </select>
          <button type="button" onClick={() => void openAgentApp()} disabled={agentBusy || !selectedAgentApp}>Abrir</button>
        </div>}
        {agentMessage && <p className="agentMessage" role="status">{agentMessage}</p>}
        <p className="agentSafetyNote">Solo se pueden abrir aplicaciones incluidas en la lista permitida del agente. El token se guarda en la configuración local de Lumina.</p>
      </section>}
    </section>}
    {!chatOpen && <div className="quickActions"><button onClick={() => updateChatOpen(true)}>✎ Escribir</button><button onClick={() => window.luminaDesktop?.hide()}>Ocultar</button></div>}
  </main>;
}
