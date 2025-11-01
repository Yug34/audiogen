from __future__ import annotations

from pathlib import Path


def audio_to_musicxml(audio_path: str) -> str:
    """Stub: Convert an audio file to MusicXML drum tabs.

    Returns a MusicXML string. Replace with model loading and inference.
    """
    # Validate input path exists early to fail fast
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"Processing audio file: {audio_path}")
    # TODO: load model, perform inference, generate MusicXML
    # Placeholder minimal MusicXML structure
    return "<score-partwise version=\"3.1\"></score-partwise>"


