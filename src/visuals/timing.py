"""
Visual timing and synchronization with audio.

Handles matching visual trigger words to audio timestamps and calculating
precise timing for when visuals should appear.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

from src.primitives.models import VisualSpec, AudioSegment

logger = logging.getLogger(__name__)


@dataclass
class SyncPoint:
    """Timing information for one visual."""
    visual_index: int           # Index in Act.visuals list
    visual_spec: VisualSpec     # The visual to render
    start_time: float           # When to show (seconds from Act start)
    duration: float             # How long to show
    trigger_word: Optional[str] = None  # Word that triggered it
    trigger_time: Optional[float] = None  # When trigger word was spoken


class VisualTimingCalculator:
    """Calculates when visuals should appear based on audio timing."""

    def __init__(self, default_lead_time: float = 0.5):
        """Initialize timing calculator.

        Args:
            default_lead_time: Default seconds to show visual BEFORE trigger word
        """
        self.default_lead_time = default_lead_time

    def calculate_sync_points(
        self,
        visuals: List[VisualSpec],
        audio: Optional[AudioSegment],
        fallback_duration: float = 10.0
    ) -> List[SyncPoint]:
        """Calculate when each visual should appear.

        Strategy:
        1. If visual has trigger_words and audio has timestamps: sync to audio
        2. Otherwise: sequential timing (divide time equally)

        Args:
            visuals: List of visual specs
            audio: Audio segment with word timestamps (if available)
            fallback_duration: Duration to use if no audio provided

        Returns:
            List of SyncPoints with timing for each visual
        """
        if not visuals:
            return []

        # Parse word timestamps from audio
        word_timestamps = []
        if audio and audio.word_timestamps:
            word_timestamps = self._parse_word_timestamps(audio.word_timestamps)
            target_duration = audio.duration
        else:
            target_duration = fallback_duration

        sync_points = []
        current_time = 0.0

        for i, visual in enumerate(visuals):
            # Try to find trigger word in audio
            trigger_time = None
            trigger_word = None

            if visual.trigger_words and word_timestamps:
                trigger_time, trigger_word = self._find_trigger_time(
                    visual.trigger_words,
                    word_timestamps,
                    used_times=[sp.trigger_time for sp in sync_points if sp.trigger_time]
                )

            # Calculate start time
            if trigger_time is not None:
                # Sync to audio: show BEFORE trigger word
                lead = visual.lead_time or self.default_lead_time
                start_time = max(0, trigger_time - lead)
            else:
                # Sequential: show after previous visual
                start_time = current_time

            # Calculate duration
            duration = visual.duration or (target_duration / len(visuals))

            sync_points.append(SyncPoint(
                visual_index=i,
                visual_spec=visual,
                start_time=start_time,
                duration=duration,
                trigger_word=trigger_word,
                trigger_time=trigger_time
            ))

            # Update current time for next sequential visual
            current_time = start_time + duration

        return sync_points

    def _find_trigger_time(
        self,
        trigger_words: List[str],
        word_timestamps: List[Dict[str, Any]],
        used_times: List[float]
    ) -> tuple[Optional[float], Optional[str]]:
        """Find first occurrence of trigger word in timestamps.

        Args:
            trigger_words: List of words to search for
            word_timestamps: Audio word timestamps
            used_times: Already used trigger times (avoid reusing)

        Returns:
            (trigger_time, trigger_word) or (None, None) if not found
        """
        # Normalize trigger words to lowercase
        trigger_words_lower = [w.lower() for w in trigger_words]

        for ts in word_timestamps:
            word = ts.get("word", "").lower().strip()
            start = ts.get("start")

            # Check if this word matches any trigger
            if word in trigger_words_lower:
                # Check if already used
                if start not in used_times:
                    logger.debug(f"Found trigger word '{word}' at {start}s")
                    return start, word

        logger.debug(f"No trigger word found for: {trigger_words}")
        return None, None

    def _parse_word_timestamps(
        self,
        word_timestamps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse word timestamps from AudioSegment.

        Args:
            word_timestamps: Raw timestamp data

        Returns:
            Normalized list of {word, start, end} dicts
        """
        parsed = []

        for ts in word_timestamps:
            # Handle different formats
            if isinstance(ts, dict):
                parsed.append({
                    "word": ts.get("word", ""),
                    "start": ts.get("start", 0.0),
                    "end": ts.get("end", 0.0)
                })

        return parsed


def calculate_timing_accuracy(
    sync_points: List[SyncPoint],
    expected_times: List[float]
) -> Dict[str, float]:
    """Measure timing accuracy between expected and actual.

    Args:
        sync_points: Calculated sync points
        expected_times: Expected trigger times

    Returns:
        Dict with accuracy metrics (mean_error, max_error, etc.)
    """
    if len(sync_points) != len(expected_times):
        return {"error": "Mismatched lengths"}

    errors = []
    for sp, expected in zip(sync_points, expected_times):
        if sp.trigger_time is not None:
            error = abs(sp.trigger_time - expected)
            errors.append(error)

    if not errors:
        return {"mean_error": 0.0, "max_error": 0.0}

    return {
        "mean_error": sum(errors) / len(errors),
        "max_error": max(errors),
        "min_error": min(errors),
        "num_synced": len(errors)
    }
