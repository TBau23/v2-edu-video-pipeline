"""
Audio timing extraction and estimation.

Since many TTS APIs don't provide word-level timestamps, this module
provides fallback methods for timing estimation and forced alignment.
"""

from pathlib import Path
from typing import List, Optional
import re

from src.audio.providers import WordTimestamp


class TimingExtractor:
    """Extract or estimate word-level timing from audio + text."""

    # Average speaking rates (words per minute)
    SLOW_RATE = 120
    NORMAL_RATE = 150
    FAST_RATE = 180

    def __init__(self, speaking_rate: float = NORMAL_RATE):
        """Initialize timing extractor.

        Args:
            speaking_rate: Words per minute (default: 150)
        """
        self.speaking_rate = speaking_rate
        self.words_per_second = speaking_rate / 60.0

    def estimate_timestamps(
        self,
        text: str,
        total_duration: float,
        pause_markers: Optional[dict] = None
    ) -> List[WordTimestamp]:
        """Estimate word timestamps based on text and total duration.

        This is a fallback when TTS provider doesn't give timestamps.
        Not as accurate as forced alignment, but better than nothing.

        Args:
            text: Narration text
            total_duration: Total audio duration in seconds
            pause_markers: Dict of punctuation → pause duration (seconds)

        Returns:
            List of estimated WordTimestamp objects

        Note:
            This assumes relatively uniform speaking pace and accounts for
            punctuation pauses. For ±300ms accuracy, forced alignment is better.
        """
        if pause_markers is None:
            pause_markers = {
                ".": 0.5,
                ",": 0.3,
                "?": 0.6,
                "!": 0.6,
                ";": 0.4,
                ":": 0.3,
            }

        # Tokenize text into words and punctuation
        tokens = self._tokenize(text)

        # Calculate time per word (accounting for pauses)
        total_pause_time = sum(
            pause_markers.get(token, 0)
            for token in tokens
            if token in pause_markers
        )

        speaking_time = total_duration - total_pause_time
        word_tokens = [t for t in tokens if t not in pause_markers]

        if not word_tokens:
            return []

        time_per_word = speaking_time / len(word_tokens)

        # Build timestamps
        timestamps = []
        current_time = 0.0
        word_index = 0

        for token in tokens:
            if token in pause_markers:
                # Punctuation: add pause time
                current_time += pause_markers[token]
            else:
                # Word: create timestamp
                start = current_time
                end = current_time + time_per_word

                timestamps.append(WordTimestamp(
                    word=token,
                    start=start,
                    end=end
                ))

                current_time = end
                word_index += 1

        return timestamps

    def estimate_duration(self, text: str, pause_markers: Optional[dict] = None) -> float:
        """Estimate audio duration from text.

        Args:
            text: Narration text
            pause_markers: Dict of punctuation → pause duration

        Returns:
            Estimated duration in seconds
        """
        if pause_markers is None:
            pause_markers = {
                ".": 0.5,
                ",": 0.3,
                "?": 0.6,
                "!": 0.6,
            }

        tokens = self._tokenize(text)

        # Count words
        word_count = sum(1 for t in tokens if t not in pause_markers)

        # Calculate speaking time
        speaking_time = word_count / self.words_per_second

        # Add pause time
        pause_time = sum(
            pause_markers.get(token, 0)
            for token in tokens
            if token in pause_markers
        )

        return speaking_time + pause_time

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words and punctuation.

        Args:
            text: Input text

        Returns:
            List of tokens (words and punctuation marks)

        Example:
            "Hello, world!" → ["Hello", ",", "world", "!"]
        """
        # Split on whitespace and punctuation, keeping punctuation
        pattern = r"(\w+|[.,!?;:])"
        tokens = re.findall(pattern, text)
        return [t for t in tokens if t.strip()]

    def align_forced(
        self,
        audio_path: Path,
        text: str
    ) -> List[WordTimestamp]:
        """Perform forced alignment using external tool.

        This provides more accurate timing than estimation.

        Args:
            audio_path: Path to audio file
            text: Original text

        Returns:
            List of WordTimestamp objects

        Note:
            This requires an external alignment tool (Gentle, aeneas, etc.)
            For MVP, we'll leave this as a TODO and use estimation.
        """
        # TODO: Implement forced alignment
        # Options:
        # 1. Gentle (Docker-based, very accurate)
        # 2. aeneas (Python library, easier to install)
        # 3. Montreal Forced Aligner (research-grade)

        raise NotImplementedError(
            "Forced alignment not yet implemented. "
            "Use estimate_timestamps() as fallback."
        )


def add_natural_pauses(
    text: str,
    pause_markers: dict
) -> str:
    """Add pause markers to text for TTS that supports SSML.

    Args:
        text: Original text
        pause_markers: Dict of punctuation → pause duration (seconds)

    Returns:
        Text with <break> tags for pauses

    Example:
        "Hello, world." → "Hello<break time='0.3s'/> world<break time='0.5s'/>"

    Note:
        This is only useful if TTS provider supports SSML.
        OpenAI TTS doesn't support SSML currently.
    """
    result = text

    for punct, duration in pause_markers.items():
        # Replace punctuation with punctuation + pause
        pause_tag = f"{punct}<break time='{duration}s'/>"
        result = result.replace(punct, pause_tag)

    return result


def adjust_timing_for_sync(
    timestamps: List[WordTimestamp],
    target_duration: float
) -> List[WordTimestamp]:
    """Adjust timestamps to match target duration.

    Useful when audio duration doesn't match expectation due to
    TTS variations or speed adjustments.

    Args:
        timestamps: Original timestamps
        target_duration: Desired total duration

    Returns:
        Adjusted timestamps scaled to target duration
    """
    if not timestamps:
        return []

    # Current duration
    current_duration = timestamps[-1].end

    # Scale factor
    scale = target_duration / current_duration

    # Apply scaling
    adjusted = []
    for ts in timestamps:
        adjusted.append(WordTimestamp(
            word=ts.word,
            start=ts.start * scale,
            end=ts.end * scale
        ))

    return adjusted
