"""Audio synthesis module."""

from src.audio.synthesizer import AudioSynthesizer
from src.audio.providers import (
    TTSProvider,
    OpenAITTSProvider,
    ElevenLabsTTSProvider,
    WordTimestamp,
    get_provider
)
from src.audio.timing import (
    TimingExtractor,
    add_natural_pauses,
    adjust_timing_for_sync
)

__all__ = [
    "AudioSynthesizer",
    "TTSProvider",
    "OpenAITTSProvider",
    "ElevenLabsTTSProvider",
    "WordTimestamp",
    "get_provider",
    "TimingExtractor",
    "add_natural_pauses",
    "adjust_timing_for_sync",
]
