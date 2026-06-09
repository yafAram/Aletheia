from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4
import json
import subprocess
import wave

from vosk import KaldiRecognizer, Model


@dataclass(slots=True)
class SttResult:
    text: str
    confidence: float
    duration_seconds: float
    words: list[dict]
    raw: dict

    def as_dict(self) -> dict:
        return asdict(self)


class VoskSttEngine:
    """Motor STT local con Vosk.

    Acepta audio común y lo convierte internamente a:
    - WAV
    - mono
    - 16 kHz
    - PCM 16-bit
    """

    def __init__(self, model_path: str, sample_rate: int = 16000) -> None:
        self.model_path = Path(model_path)
        self.sample_rate = sample_rate
        self._model: Model | None = None

    def transcribe(self, audio_path: str) -> SttResult:
        normalized_path = self._normalize_audio(audio_path)
        return self.transcribe_wav(str(normalized_path))

    def transcribe_wav(self, audio_path: str) -> SttResult:
        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._get_model()

        with wave.open(str(path), "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            total_frames = wf.getnframes()
            duration_seconds = total_frames / float(frame_rate)

            if channels != 1:
                raise ValueError("Vosk STT requires mono WAV audio.")

            if sample_width != 2:
                raise ValueError("Vosk STT requires 16-bit PCM WAV audio.")

            recognizer = KaldiRecognizer(model, frame_rate)
            recognizer.SetWords(True)

            chunks: list[dict] = []

            while True:
                data = wf.readframes(4000)

                if len(data) == 0:
                    break

                if recognizer.AcceptWaveform(data):
                    chunks.append(json.loads(recognizer.Result()))

            final_result = json.loads(recognizer.FinalResult())
            chunks.append(final_result)

        text_parts: list[str] = []
        words: list[dict] = []

        for chunk in chunks:
            chunk_text = chunk.get("text", "").strip()

            if chunk_text:
                text_parts.append(chunk_text)

            if "result" in chunk and isinstance(chunk["result"], list):
                words.extend(chunk["result"])

        text = " ".join(text_parts).strip()
        confidence = self._calculate_confidence(words)

        return SttResult(
            text=text,
            confidence=confidence,
            duration_seconds=round(duration_seconds, 3),
            words=words,
            raw={
                "chunks": chunks,
                "frame_rate": frame_rate,
                "channels": channels,
                "sample_width": sample_width,
            },
        )

    def _normalize_audio(self, audio_path: str) -> Path:
        source_path = Path(audio_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        output_path = source_path.parent / f"{uuid4()}_normalized.wav"

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-ac",
            "1",
            "-ar",
            str(self.sample_rate),
            "-sample_fmt",
            "s16",
            str(output_path),
        ]

        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed to normalize audio: {completed.stderr}"
            )

        return output_path

    def _get_model(self) -> Model:
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Vosk model path does not exist: {self.model_path}"
            )

        self._model = Model(str(self.model_path))
        return self._model

    def _calculate_confidence(self, words: list[dict]) -> float:
        confidences = [
            float(word.get("conf", 0.0))
            for word in words
            if "conf" in word
        ]

        if not confidences:
            return 0.0

        return round(sum(confidences) / len(confidences), 3)