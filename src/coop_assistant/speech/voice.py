"""Speech in/out. Speech recognition is always local; speech output prefers ElevenLabs and falls back to Piper."""

import json
import os
import tempfile
import urllib.request
import wave

from coop_assistant.config import (
    ELEVENLABS_LANGS as ELEVEN_LANGS,
    ELEVENLABS_MODEL as ELEVEN_MODEL,
    ELEVENLABS_TIMEOUT as ELEVEN_TIMEOUT,
    ELEVENLABS_VOICE_ID as ELEVEN_VOICE,
    MODEL_DIR as HERE,
    PIPER_VOICES as VOICES,
    WHISPER_SIZE,
)

HOTWORDS = "coffee, parchment, cherry, grade A, grade B, Nyeri, Kiambu, Murang'a, Kirinyaga, shillings, kg"

_stt = None
_tts = {}


def _load_audio(path):
    # faster-whisper's own decoder passes a kwarg that PyAV 19 rejects, so decode here.
    import av
    import numpy as np
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    chunks = []
    with av.open(path) as container:
        for frame in container.decode(audio=0):
            chunks += [f.to_ndarray() for f in resampler.resample(frame)]
        chunks += [f.to_ndarray() for f in resampler.resample(None)]
    return np.concatenate(chunks, axis=1).flatten().astype(np.float32) / 32768.0


def transcribe(audio_path, language=None):
    """Returns (text, language_code, probability)."""
    global _stt
    if _stt is None:
        from faster_whisper import WhisperModel
        _stt = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8",
                            download_root=str(HERE / "models"), local_files_only=True)
    segments, info = _stt.transcribe(_load_audio(audio_path), language=language, beam_size=5, vad_filter=True,
                                     hotwords=HOTWORDS)
    return " ".join(s.text.strip() for s in segments).strip(), info.language, info.language_probability


def _eleven(text, lang):
    payload = {"text": text, "model_id": ELEVEN_MODEL,
               "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True}}
    if "v2_5" in ELEVEN_MODEL:
        payload["language_code"] = lang
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}?output_format=pcm_16000", body,
        {"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=ELEVEN_TIMEOUT) as resp:
        pcm = resp.read()
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm)
    return out


def speak(text, lang):
    """Returns (wav path or None, engine name). ElevenLabs when configured and reachable, else local Piper."""
    if os.environ.get("ELEVENLABS_API_KEY") and lang in ELEVEN_LANGS:
        try:
            return _eleven(text, lang), "elevenlabs"
        except (OSError, ValueError) as e:
            print("ElevenLabs unavailable, using local voice:", e)
    return _piper(text, lang), "piper"


def _piper(text, lang):
    name = VOICES.get(lang)
    model = HERE / "voices" / f"{name}.onnx" if name else None
    if not model or not model.exists():
        return None
    if lang not in _tts:
        from piper import PiperVoice
        _tts[lang] = PiperVoice.load(str(model))
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(out, "wb") as wf:
        _tts[lang].synthesize_wav(text, wf)
    return out
