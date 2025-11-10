"""
Audio synthesis system - converts Act narration to audio files.

This module ties together TTS providers and timing extraction to create
AudioSegment objects with precise timing data for synchronization.
"""

import hashlib
import json
from pathlib import Path
from typing import List, Optional

from src.primitives.models import Act, Script, AudioSegment
from src.style.config import StyleConfig
from src.audio.providers import get_provider, TTSProvider, WordTimestamp
from src.audio.timing import TimingExtractor


class AudioSynthesizer:
    """Synthesizes audio for Acts using TTS providers.

    Features:
    - Multiple TTS provider support (OpenAI, ElevenLabs)
    - Word-level timestamp extraction (or estimation)
    - Natural pause handling from punctuation
    - Caching to avoid regenerating unchanged audio
    """

    def __init__(
        self,
        provider: str = "openai",
        style: Optional[StyleConfig] = None,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None
    ):
        """Initialize audio synthesizer.

        Args:
            provider: TTS provider name ("openai" or "elevenlabs")
            style: StyleConfig for voice settings
            api_key: API key for TTS provider
            cache_dir: Directory for caching audio files
        """
        self.provider = get_provider(provider, api_key)
        self.style = style or StyleConfig.load_preset("default")
        self.cache_dir = cache_dir or Path(".audio_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Timing extractor for fallback
        self.timing_extractor = TimingExtractor(
            speaking_rate=self._get_speaking_rate()
        )

    def _get_speaking_rate(self) -> float:
        """Get speaking rate from style config.

        Returns:
            Words per minute
        """
        # Convert speed multiplier to WPM
        # Normal rate: 150 WPM
        # Speed 1.0 → 150 WPM
        # Speed 1.2 → 180 WPM
        # Speed 0.8 → 120 WPM
        base_rate = 150
        speed = self.style.voice.speed
        return base_rate * speed

    def synthesize_act(
        self,
        act: Act,
        output_path: Path,
        use_cache: bool = True
    ) -> AudioSegment:
        """Synthesize audio for a single Act.

        Args:
            act: Act to synthesize
            output_path: Where to save the audio file
            use_cache: If True, use cached audio if available

        Returns:
            AudioSegment with audio file and timing data
        """
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(act)
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                # Copy cached file to output path
                cached_audio, duration, timestamps = cached
                import shutil
                shutil.copy(cached_audio, output_path)

                return AudioSegment(
                    act_id=act.id,
                    audio_path=output_path,
                    duration=duration,
                    word_timestamps=self._timestamps_to_dict(timestamps) if timestamps else None,
                    provider=self.provider.__class__.__name__,
                    voice_id=self.style.voice.voice_id
                )

        # Synthesize audio
        audio_path, duration, word_timestamps = self.provider.synthesize(
            text=act.narration,
            voice=self.style.voice.voice_id,
            output_path=output_path,
            speed=self.style.voice.speed
        )

        # If no timestamps from provider, estimate them
        if word_timestamps is None:
            word_timestamps = self.timing_extractor.estimate_timestamps(
                text=act.narration,
                total_duration=duration,
                pause_markers=self.style.voice.pause_markers
            )

        # Cache result
        if use_cache:
            cache_key = self._get_cache_key(act)
            self._save_to_cache(cache_key, audio_path, duration, word_timestamps)

        return AudioSegment(
            act_id=act.id,
            audio_path=audio_path,
            duration=duration,
            word_timestamps=self._timestamps_to_dict(word_timestamps) if word_timestamps else None,
            provider=self.provider.__class__.__name__,
            voice_id=self.style.voice.voice_id
        )

    def synthesize_script(
        self,
        script: Script,
        output_dir: Path,
        use_cache: bool = True
    ) -> List[AudioSegment]:
        """Synthesize audio for all Acts in a Script.

        Args:
            script: Script with Acts to synthesize
            output_dir: Directory to save audio files
            use_cache: If True, use cached audio when available

        Returns:
            List of AudioSegments (one per Act)
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_segments = []

        for act in script.acts:
            output_path = output_dir / f"{act.id}.mp3"

            print(f"Synthesizing audio for {act.id}...")

            audio_segment = self.synthesize_act(act, output_path, use_cache)
            audio_segments.append(audio_segment)

            print(f"  ✓ Duration: {audio_segment.duration:.2f}s")

        return audio_segments

    def _get_cache_key(self, act: Act) -> str:
        """Generate cache key for an Act.

        Args:
            act: Act to cache

        Returns:
            Hash string for cache lookup
        """
        content = (
            f"{act.narration}|"
            f"{self.style.voice.voice_id}|"
            f"{self.style.voice.speed}|"
            f"{self.provider.__class__.__name__}"
        )
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(
        self,
        cache_key: str
    ) -> Optional[tuple[Path, float, Optional[List[WordTimestamp]]]]:
        """Get audio from cache.

        Args:
            cache_key: Cache key

        Returns:
            Tuple of (audio_path, duration, timestamps) or None if not cached
        """
        cache_audio = self.cache_dir / f"{cache_key}.mp3"
        cache_meta = self.cache_dir / f"{cache_key}.json"

        if not cache_audio.exists() or not cache_meta.exists():
            return None

        # Load metadata
        with open(cache_meta, "r") as f:
            meta = json.load(f)

        duration = meta["duration"]
        timestamps = None

        if "word_timestamps" in meta and meta["word_timestamps"]:
            timestamps = [
                WordTimestamp(**ts)
                for ts in meta["word_timestamps"]
            ]

        return cache_audio, duration, timestamps

    def _save_to_cache(
        self,
        cache_key: str,
        audio_path: Path,
        duration: float,
        word_timestamps: Optional[List[WordTimestamp]]
    ):
        """Save audio to cache.

        Args:
            cache_key: Cache key
            audio_path: Path to audio file
            duration: Audio duration
            word_timestamps: Word timestamps (optional)
        """
        cache_audio = self.cache_dir / f"{cache_key}.mp3"
        cache_meta = self.cache_dir / f"{cache_key}.json"

        # Copy audio file
        import shutil
        shutil.copy(audio_path, cache_audio)

        # Save metadata
        meta = {
            "duration": duration,
            "word_timestamps": [
                {"word": ts.word, "start": ts.start, "end": ts.end}
                for ts in (word_timestamps or [])
            ]
        }

        with open(cache_meta, "w") as f:
            json.dump(meta, f, indent=2)

    def _timestamps_to_dict(self, timestamps: List[WordTimestamp]) -> List[dict]:
        """Convert WordTimestamp objects to dicts for JSON serialization."""
        return [
            {"word": ts.word, "start": ts.start, "end": ts.end}
            for ts in timestamps
        ]
