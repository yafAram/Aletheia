import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  buildAudioUrl,
  getEmotionState,
  getInitiativeState,
  sendChatMessage,
  synthesizeSpeech,
} from "./api/aletheiaApi";
import type { AletheiaMood, ChatResponse, EmotionState } from "./types";

type Message = {
  role: "user" | "aletheia";
  text: string;
};

function resolveVisualMood(
  emotion: EmotionState | null,
  isThinking: boolean,
  isSpeaking: boolean
): AletheiaMood {
  if (isSpeaking) return "speaking";
  if (isThinking) return "thinking";

  const stress = emotion?.stress ?? 0;
  const energy = emotion?.energy ?? 0.5;
  const affection = emotion?.affection ?? 0;
  const curiosity = emotion?.curiosity ?? 0.4;
  const mood = String(emotion?.mood ?? "idle").toLowerCase();

  if (stress >= 0.65) return "stressed";
  if (energy <= 0.32) return "tired";
  if (mood.includes("happy")) return "happy";
  if (affection >= 0.6) return "warm";
  if (curiosity >= 0.65) return "curious";

  return "idle";
}

function resolveVoiceEmotion(mood: AletheiaMood): string {
  if (mood === "happy") return "happy";
  if (mood === "warm") return "warm";
  if (mood === "tired") return "tired";
  if (mood === "stressed") return "comfort";
  if (mood === "curious") return "warm";
  return "auto";
}

function moodLabel(mood: AletheiaMood): string {
  const labels: Record<AletheiaMood, string> = {
    idle: "presente",
    thinking: "pensando",
    speaking: "hablando",
    happy: "animada",
    warm: "cálida",
    tired: "cansada",
    stressed: "atenta",
    curious: "curiosa",
  };

  return labels[mood];
}

function AletheiaPresence({ mood }: { mood: AletheiaMood }) {
  return (
    <section className={`presence presence--${mood}`}>
      <div className="aura" />

      <div className="twinTail twinTail--left" />
      <div className="twinTail twinTail--right" />

      <div className="character">
        <div className="hair hair--back" />
        <div className="head">
          <div className="bang bang--left" />
          <div className="bang bang--center" />
          <div className="bang bang--right" />

          <div className="eyes">
            <div className="eye eye--left">
              <span />
            </div>
            <div className="eye eye--right">
              <span />
            </div>
          </div>

          <div className="mouth" />
          <div className="cheek cheek--left" />
          <div className="cheek cheek--right" />
        </div>

        <div className="neck" />
        <div className="body">
          <div className="tie" />
          <div className="coreLight" />
        </div>
      </div>

      <div className="shadow" />
    </section>
  );
}

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "aletheia",
      text: "Estoy aquí, Aram. Todavía estoy aprendiendo a estar en pantalla, pero ya tengo un pequeño cuerpo de luz.",
    },
  ]);
  const [emotion, setEmotion] = useState<EmotionState | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initiativeHint, setInitiativeHint] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const visualMood = useMemo(
    () => resolveVisualMood(emotion, isThinking, isSpeaking),
    [emotion, isThinking, isSpeaking]
  );

  useEffect(() => {
    const interval = window.setInterval(async () => {
      try {
        const emotionState = await getEmotionState();
        setEmotion(emotionState);

        const initiative = await getInitiativeState();
        const actions = initiative?.actions ?? [];

        if (actions.length > 0) {
          const topAction = actions[0];

          if (topAction?.suggested_message) {
            setInitiativeHint(topAction.suggested_message);
          }
        }
      } catch {
        // La UI no debe romperse si la API tarda.
      }
    }, 5000);

    return () => window.clearInterval(interval);
  }, []);

  async function playAletheiaVoice(text: string) {
    const voiceEmotion = resolveVoiceEmotion(visualMood);
    const tts = await synthesizeSpeech(text, voiceEmotion);
    const audioUrl = buildAudioUrl(tts.audio_url);

    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    setIsSpeaking(true);

    audio.onended = () => {
      setIsSpeaking(false);
    };

    audio.onerror = () => {
      setIsSpeaking(false);
    };

    await audio.play();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanInput = input.trim();

    if (!cleanInput || isThinking) return;

    setMessages((current) => [
      ...current,
      {
        role: "user",
        text: cleanInput,
      },
    ]);

    setInput("");
    setIsThinking(true);
    setError(null);

    try {
      const result = await sendChatMessage(cleanInput);

      setLastResponse(result);
      setEmotion(result.emotion_state);

      setMessages((current) => [
        ...current,
        {
          role: "aletheia",
          text: result.response,
        },
      ]);

      await playAletheiaVoice(result.response);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Algo salió mal al hablar con Aletheia.";

      setError(message);
    } finally {
      setIsThinking(false);
    }
  }

  return (
    <main className="appShell">
      <section className="stage">
        <div className="statusPill">
          <span className={`statusDot statusDot--${visualMood}`} />
          Aletheia está {moodLabel(visualMood)}
        </div>

        <AletheiaPresence mood={visualMood} />

        {initiativeHint && (
          <div className="initiativeBubble">
            <span>Me dio por pensar...</span>
            <p>{initiativeHint}</p>
          </div>
        )}
      </section>

      <section className="panel">
        <header className="panelHeader">
          <div>
            <h1>Aletheia</h1>
            <p>Presencia local conectada a memoria, voz y vínculo.</p>
          </div>

          <div className="metrics">
            <span>Memoria: {lastResponse?.memory_items ?? "..."}</span>
            <span>Recuerdos: {lastResponse?.significant_memory_count ?? "..."}</span>
            <span>Vínculo: {lastResponse?.bond_event_count ?? "..."}</span>
          </div>
        </header>

        <div className="chatWindow">
          {messages.map((message, index) => (
            <article
              key={`${message.role}-${index}`}
              className={`message message--${message.role}`}
            >
              <span>{message.role === "user" ? "Tú" : "Aletheia"}</span>
              <p>{message.text}</p>
            </article>
          ))}

          {isThinking && (
            <article className="message message--aletheia">
              <span>Aletheia</span>
              <p>Déjame pensarlo un momento...</p>
            </article>
          )}
        </div>

        {error && <div className="errorBox">{error}</div>}

        <form className="inputBar" onSubmit={handleSubmit}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Háblale a Aletheia..."
          />
          <button type="submit" disabled={isThinking}>
            {isThinking ? "Pensando..." : "Enviar"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default App;