"""
TTS provider abstraction and implementations.

Supports multiple TTS providers (OpenAI, ElevenLabs) with a unified interface.
Providers are responsible for converting text to audio and extracting timing data.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib

from openai import OpenAI


@dataclass
class WordTimestamp:
    """Word-level timestamp data."""
    word: str
    start: float  # seconds
    end: float    # seconds


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str,
        output_path: Path,
        **kwargs
    ) -> Tuple[Path, float, Optional[List[WordTimestamp]]]:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice: Voice ID/name
            output_path: Where to save the audio file
            **kwargs: Provider-specific options

        Returns:
            Tuple of (audio_path, duration, word_timestamps)
            word_timestamps may be None if provider doesn't support them

        Raises:
            Exception: If synthesis fails
        """
        pass

    def get_cache_key(self, text: str, voice: str, **kwargs) -> str:
        """Generate cache key for this synthesis request.

        Args:
            text: Text to synthesize
            voice: Voice ID
            **kwargs: Additional parameters

        Returns:
            Hash string for caching
        """
        content = f"{text}|{voice}|{kwargs}"
        return hashlib.md5(content.encode()).hexdigest()


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS provider.

    Uses OpenAI's text-to-speech API.
    """

    SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    SUPPORTED_MODELS = ["tts-1", "tts-1-hd"]

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI TTS provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = OpenAI(api_key=api_key)

    def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        output_path: Path = None,
        model: str = "tts-1",
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[Path, float, Optional[List[WordTimestamp]]]:
        """Synthesize speech using OpenAI TTS.

        Args:
            text: Text to synthesize
            voice: Voice name (alloy, echo, fable, onyx, nova, shimmer)
            output_path: Output file path
            model: TTS model ("tts-1" or "tts-1-hd")
            speed: Speed factor (0.25 to 4.0)

        Returns:
            (audio_path, duration, word_timestamps)

        Note:
            OpenAI TTS API doesn't currently provide word-level timestamps.
            We return None for timestamps and will need forced alignment if needed.
        """
        # Validate voice
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(
                f"Unsupported voice: {voice}. "
                f"Supported: {', '.join(self.SUPPORTED_VOICES)}"
            )

        # Validate model
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported: {', '.join(self.SUPPORTED_MODELS)}"
            )

        # Ensure output path
        if output_path is None:
            output_path = Path(f"temp_{self.get_cache_key(text, voice)}.mp3")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Call OpenAI TTS API
        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="mp3"
            )

            # Write audio to file
            with open(output_path, "wb") as f:
                f.write(response.content)

            # Get duration using audio library
            duration = self._get_audio_duration(output_path)

            # OpenAI doesn't provide word timestamps yet
            # We'll return None and handle timing extraction separately
            word_timestamps = None

            return output_path, duration, word_timestamps

        except Exception as e:
            raise Exception(f"OpenAI TTS synthesis failed: {e}")

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        try:
            # Use pydub to get duration
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            return len(audio) / 1000.0  # milliseconds to seconds

        except ImportError:
            # Fallback: estimate based on text length
            # This is very rough: ~150 words/min = 2.5 words/sec
            # For now, return placeholder
            print("Warning: pydub not installed, duration estimation may be inaccurate")
            return 10.0  # placeholder

        except Exception as e:
            print(f"Warning: Could not determine audio duration: {e}")
            return 10.0  # placeholder


class ElevenLabsTTSProvider(TTSProvider):
    """ElevenLabs TTS provider.

    Uses ElevenLabs API for higher quality synthesis.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize ElevenLabs TTS provider.

        Args:
            api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env var)
        """
        if api_key is None:
            api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ElevenLabs API key required. Set ELEVENLABS_API_KEY environment variable "
                "or pass api_key parameter."
            )

        try:
            from elevenlabs.client import ElevenLabs
            self.client = ElevenLabs(api_key=api_key)
        except ImportError:
            raise ImportError(
                "elevenlabs package not installed. "
                "Install with: pip install elevenlabs"
            )

    def synthesize(
        self,
        text: str,
        voice: str,
        output_path: Path = None,
        model: str = "eleven_monolingual_v1",
        **kwargs
    ) -> Tuple[Path, float, Optional[List[WordTimestamp]]]:
        """Synthesize speech using ElevenLabs.

        Args:
            text: Text to synthesize
            voice: Voice ID
            output_path: Output file path
            model: Model ID

        Returns:
            (audio_path, duration, word_timestamps)

        Note:
            ElevenLabs may provide timing data depending on API version.
            Check documentation for latest features.
        """
        # Ensure output path
        if output_path is None:
            output_path = Path(f"temp_{self.get_cache_key(text, voice)}.mp3")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Call ElevenLabs API
        try:
            # Generate audio
            audio_generator = self.client.generate(
                text=text,
                voice=voice,
                model=model
            )

            # Write to file
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)

            # Get duration
            duration = self._get_audio_duration(output_path)

            # Check if timing data available
            # TODO: Check if ElevenLabs provides timing in response
            word_timestamps = None

            return output_path, duration, word_timestamps

        except Exception as e:
            raise Exception(f"ElevenLabs TTS synthesis failed: {e}")

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            return len(audio) / 1000.0
        except Exception as e:
            print(f"Warning: Could not determine audio duration: {e}")
            return 10.0


def get_provider(provider_name: str, api_key: Optional[str] = None) -> TTSProvider:
    """Factory function to get a TTS provider.

    Args:
        provider_name: Provider name ("openai" or "elevenlabs")
        api_key: API key (optional, will use env var if not provided)

    Returns:
        TTSProvider instance

    Raises:
        ValueError: If provider name is unknown
    """
    provider_name = provider_name.lower()

    if provider_name == "openai":
        return OpenAITTSProvider(api_key=api_key)
    elif provider_name == "elevenlabs":
        return ElevenLabsTTSProvider(api_key=api_key)
    else:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            "Supported: 'openai', 'elevenlabs'"
        )
