import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  buildAudioUrl,
  getEmotionState,
  getInitiativeState,
  getPendingInitiatives,
  markInitiativeDelivered,
  dismissInitiative,
  setInitiativeAutonomy,
  getGoals,
  createGoal,
  completeGoal,
  sendChatMessage,
  synthesizeSpeech,
} from "./api/aletheiaApi";
import type { AletheiaMood, ChatResponse, EmotionState, Goal, InitiativeAction } from "./types";

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
  const [initiativeActionId, setInitiativeActionId] = useState<string | null>(null);
  const [autonomyEnabled, setAutonomyEnabled] = useState(true);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [goalDraft, setGoalDraft] = useState("");
  const [goalError, setGoalError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const shownInitiativeIds = useRef<Set<string>>(new Set());

  const visualMood = useMemo(
    () => resolveVisualMood(emotion, isThinking, isSpeaking),
    [emotion, isThinking, isSpeaking]
  );

  useEffect(() => {
    let active = true;
    let timeoutId: number | undefined;
    let polling = false;

    async function pollCompanionState() {
      if (!active || polling) return;
      polling = true;

      try {
        const [emotionState, initiativeState, pending, goalResponse] =
          await Promise.all([
            getEmotionState(),
            getInitiativeState(),
            getPendingInitiatives(),
            getGoals(),
          ]);

        if (!active) return;
        setEmotion(emotionState);
        setAutonomyEnabled(Boolean(initiativeState?.state?.autonomy_enabled ?? true));
        setGoals(goalResponse.items ?? []);

        const action = (pending.items ?? []).find(
          (item: InitiativeAction) => !shownInitiativeIds.current.has(item.id)
        );
        if (action) {
          shownInitiativeIds.current.add(action.id);
          setInitiativeHint(action.suggested_message);
          setInitiativeActionId(action.id);
          try {
            await markInitiativeDelivered(action.id);
          } catch {
            // La iniciativa ya se muestra; el backend la volverá a ofrecer si falla el acuse.
          }
        }
      } catch {
        // La interfaz permanece disponible aunque el backend esté temporalmente ocupado.
      } finally {
        polling = false;
        if (active) timeoutId = window.setTimeout(pollCompanionState, 5000);
      }
    }

    void pollCompanionState();
    return () => {
      active = false;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
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
    setInitiativeHint(null);
    setInitiativeActionId(null);
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

  async function handleDismissInitiative() {
    const actionId = initiativeActionId;
    setInitiativeHint(null);
    setInitiativeActionId(null);
    if (!actionId) return;
    try {
      await dismissInitiative(actionId);
    } catch {
      // No bloqueamos la conversación por un fallo de confirmación.
    }
  }

  function handleRespondToInitiative() {
    inputRef.current?.focus();
  }

  async function handleToggleAutonomy() {
    const nextValue = !autonomyEnabled;
    setAutonomyEnabled(nextValue);
    try {
      const result = await setInitiativeAutonomy(nextValue);
      setAutonomyEnabled(Boolean(result.state.autonomy_enabled));
    } catch {
      setAutonomyEnabled(!nextValue);
      setError("No pude actualizar la iniciativa autónoma.");
    }
  }

  async function handleCreateGoal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const description = goalDraft.trim();
    if (!description) return;
    setGoalError(null);
    try {
      const goal = await createGoal(description);
      setGoals((current) => [goal, ...current.filter((item) => item.id !== goal.id)]);
      setGoalDraft("");
    } catch (goalRequestError) {
      setGoalError(
        goalRequestError instanceof Error
          ? goalRequestError.message
          : "No pude guardar ese objetivo."
      );
    }
  }

  async function handleCompleteGoal(goalId: string) {
    try {
      await completeGoal(goalId);
      setGoals((current) =>
        current.map((goal) =>
          goal.id === goalId ? { ...goal, status: "completed" } : goal
        )
      );
    } catch {
      setGoalError("No pude marcar el objetivo como completado.");
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
          <div className="initiativeBubble" role="status">
            <span>Una pregunta que quería retomar</span>
            <p>{initiativeHint}</p>
            <div className="initiativeActions">
              <button type="button" onClick={handleRespondToInitiative}>Responder</button>
              <button type="button" className="quietButton" onClick={handleDismissInitiative}>Ahora no</button>
            </div>
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
            <button
              type="button"
              className={`autonomyToggle ${autonomyEnabled ? "isEnabled" : ""}`}
              onClick={handleToggleAutonomy}
              aria-pressed={autonomyEnabled}
            >
              Iniciativa: {autonomyEnabled ? "activa" : "pausada"}
            </button>
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

        <section className="goalsPanel" aria-label="Objetivos compartidos">
          <div className="goalsHeading">
            <span>En lo que estamos trabajando</span>
            <span>{goals.filter((goal) => goal.status === "active").length} activos</span>
          </div>
          {goals.filter((goal) => goal.status === "active").slice(0, 3).map((goal) => (
            <div className="goalItem" key={goal.id}>
              <p>{goal.description}</p>
              <button type="button" onClick={() => void handleCompleteGoal(goal.id)}>Listo</button>
            </div>
          ))}
          <form className="goalForm" onSubmit={handleCreateGoal}>
            <input
              value={goalDraft}
              onChange={(event) => setGoalDraft(event.target.value)}
              placeholder="Añadir un objetivo o proyecto..."
              maxLength={180}
              aria-label="Nuevo objetivo"
            />
            <button type="submit" disabled={!goalDraft.trim()}>Añadir</button>
          </form>
          {goalError && <p className="goalError">{goalError}</p>}
        </section>

        {error && <div className="errorBox">{error}</div>}

        <form className="inputBar" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
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