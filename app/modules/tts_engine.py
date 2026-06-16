from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4
import subprocess


@dataclass(slots=True)
class VoiceStyle:
    emotion: str
    length_scale: float
    noise_scale: float
    noise_w: float
    volume: float
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class TtsResult:
    text: str
    emotion: str
    audio_path: str
    filename: str
    voice_style: dict

    def as_dict(self) -> dict:
        return asdict(self)


class VoiceStyleMapper:
    """Convierte estados emocionales de Aletheia en parámetros de voz.

    Piper no cambia emociones como un actor humano completo.
    Esta capa crea una aproximación mediante ritmo, variación y texto preparado.
    """

    def resolve(self, emotion: str | None) -> VoiceStyle:
        clean_emotion = (emotion or "neutral").strip().lower()

        styles = {
            "neutral": VoiceStyle(
                emotion="neutral",
                length_scale=1.00,
                noise_scale=0.667,
                noise_w=0.80,
                volume=1.00,
                description="voz estable y clara",
            ),
            "warm": VoiceStyle(
                emotion="warm",
                length_scale=1.04,
                noise_scale=0.62,
                noise_w=0.78,
                volume=1.00,
                description="voz cálida, cercana y tranquila",
            ),
            "happy": VoiceStyle(
                emotion="happy",
                length_scale=0.92,
                noise_scale=0.74,
                noise_w=0.86,
                volume=1.04,
                description="voz más ligera, animada y expresiva",
            ),
            "excited": VoiceStyle(
                emotion="excited",
                length_scale=0.88,
                noise_scale=0.78,
                noise_w=0.90,
                volume=1.06,
                description="voz rápida, viva y con energía",
            ),
            "sad": VoiceStyle(
                emotion="sad",
                length_scale=1.18,
                noise_scale=0.54,
                noise_w=0.70,
                volume=0.92,
                description="voz más lenta, baja y suave",
            ),
            "tired": VoiceStyle(
                emotion="tired",
                length_scale=1.14,
                noise_scale=0.56,
                noise_w=0.72,
                volume=0.94,
                description="voz pausada y con poca energía",
            ),
            "angry": VoiceStyle(
                emotion="angry",
                length_scale=0.96,
                noise_scale=0.70,
                noise_w=0.82,
                volume=1.05,
                description="voz firme, corta y contenida",
            ),
            "sarcastic": VoiceStyle(
                emotion="sarcastic",
                length_scale=1.08,
                noise_scale=0.60,
                noise_w=0.76,
                volume=1.00,
                description="voz con pausas secas y énfasis sutil",
            ),
            "nervous": VoiceStyle(
                emotion="nervous",
                length_scale=0.94,
                noise_scale=0.72,
                noise_w=0.88,
                volume=0.98,
                description="voz un poco más rápida y menos estable",
            ),
            "comfort": VoiceStyle(
                emotion="comfort",
                length_scale=1.10,
                noise_scale=0.58,
                noise_w=0.74,
                volume=0.96,
                description="voz suave para acompañar o calmar",
            ),
        }

        return styles.get(clean_emotion, styles["neutral"])

    def from_emotion_state(self, emotion_state: dict | None) -> VoiceStyle:
        if not emotion_state:
            return self.resolve("neutral")

        mood = str(emotion_state.get("mood", "neutral")).lower()
        stress = float(emotion_state.get("stress", 0.0))
        affection = float(emotion_state.get("affection", 0.0))
        energy = float(emotion_state.get("energy", 0.5))

        if stress >= 0.70:
            return self.resolve("nervous")

        if mood in {"happy"}:
            return self.resolve("happy")

        if mood in {"warm"} or affection >= 0.65:
            return self.resolve("warm")

        if mood in {"tired"} or energy <= 0.30:
            return self.resolve("tired")

        if mood in {"stressed"}:
            return self.resolve("comfort")

        return self.resolve(mood)


class PiperTtsEngine:
    """Motor TTS local usando Piper.

    Genera archivos WAV a partir de texto.
    """

    def __init__(
        self,
        model_path: str,
        config_path: str,
        output_dir: str = "/app/storage/tts",
    ) -> None:
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.style_mapper = VoiceStyleMapper()

    def synthesize(
        self,
        text: str,
        emotion: str | None = None,
        emotion_state: dict | None = None,
    ) -> TtsResult:
        clean_text = text.strip()

        if not clean_text:
            raise ValueError("Text cannot be empty for TTS.")

        self._validate_files()

        if emotion and emotion != "auto":
            style = self.style_mapper.resolve(emotion)
        else:
            style = self.style_mapper.from_emotion_state(emotion_state)

        prepared_text = self._prepare_text(clean_text, style)

        filename = f"{uuid4()}.wav"
        output_path = self.output_dir / filename

        self._run_piper_with_style(
            text=prepared_text,
            output_path=output_path,
            style=style,
        )

        return TtsResult(
            text=clean_text,
            emotion=style.emotion,
            audio_path=str(output_path),
            filename=filename,
            voice_style=style.as_dict(),
        )

    def _validate_files(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Piper model not found: {self.model_path}")

        if not self.config_path.exists():
            raise FileNotFoundError(f"Piper config not found: {self.config_path}")

    def _run_piper_with_style(
        self,
        text: str,
        output_path: Path,
        style: VoiceStyle,
    ) -> None:
        command = [
            "piper",
            "--model",
            str(self.model_path),
            "--config",
            str(self.config_path),
            "--output_file",
            str(output_path),
            "--length-scale",
            str(style.length_scale),
            "--noise-scale",
            str(style.noise_scale),
            "--noise-w",
            str(style.noise_w),
        ]

        completed = subprocess.run(
            command,
            input=text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if completed.returncode == 0:
            return

        # Fallback por si alguna versión de Piper no acepta parámetros de estilo.
        fallback_command = [
            "piper",
            "--model",
            str(self.model_path),
            "--config",
            str(self.config_path),
            "--output_file",
            str(output_path),
        ]

        fallback = subprocess.run(
            fallback_command,
            input=text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if fallback.returncode != 0:
            raise RuntimeError(
                "Piper failed to synthesize audio. "
                f"Original error: {completed.stderr}. "
                f"Fallback error: {fallback.stderr}"
            )

    def _prepare_text(self, text: str, style: VoiceStyle) -> str:
        emotion = style.emotion

        if emotion == "happy":
            return text.replace(".", "… ").strip()

        if emotion == "excited":
            return text.replace(".", "! ").strip()

        if emotion == "sad":
            return text.replace(",", "...").replace(".", "...").strip()

        if emotion == "tired":
            return text.replace(",", "...").replace(".", "...").strip()

        if emotion == "angry":
            return text.replace("...", ".").strip()

        if emotion == "sarcastic":
            return text.replace(",", "...").replace(".", "...").strip()

        if emotion == "comfort":
            return text.replace(".", "... ").strip()

        return text