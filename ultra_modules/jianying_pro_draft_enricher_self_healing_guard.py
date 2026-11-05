import time
import copy
import json
from typing import Dict, Any, Optional

def enrich_draft_content(draft_content: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Pure function to enrich draft content with text effects, transitions, KenBurns, and BGM.
    Performs silent self-healing for missing/dirty data.
    """
    if params is None:
        params = {}

    # Deep copy to remain pure
    enriched = copy.deepcopy(draft_content)

    # Self-healing default values
    effects = params.get('effects', True)
    transitions = params.get('transitions', True)
    ken_burns = params.get('ken_burns', True)
    bgm = params.get('bgm', "default_bgm.mp3")

    if not isinstance(enriched, dict):
        enriched = {}

    if 'tracks' not in enriched or not isinstance(enriched['tracks'], list):
        enriched['tracks'] = []

    # Self-healing: ensure tracks are all dicts before processing
    valid_tracks = []
    for t in enriched['tracks']:
        if isinstance(t, dict):
            valid_tracks.append(t)
    enriched['tracks'] = valid_tracks

    # Inject BGM
    if bgm:
        bgm_track = next((t for t in enriched['tracks'] if t.get('type') == 'audio'), None)
        if not bgm_track:
            enriched['tracks'].append({'type': 'audio', 'segments': [{'file': bgm, 'volume': 1.0}]})
        else:
            if 'segments' not in bgm_track or not isinstance(bgm_track['segments'], list):
                bgm_track['segments'] = []
            bgm_track['segments'].append({'file': bgm, 'volume': 1.0})

    # Enrich existing tracks
    for track in enriched['tracks']:
        if not isinstance(track, dict):
            continue

        if track.get('type') == 'video':
            segments = track.get('segments', [])
            if not isinstance(segments, list):
                segments = []
                track['segments'] = segments

            for segment in segments:
                if not isinstance(segment, dict):
                    continue

                # KenBurns
                if ken_burns:
                    if 'animations' not in segment or not isinstance(segment['animations'], list):
                        segment['animations'] = []
                    # Check if KenBurns already exists
                    has_ken_burns = any(a.get('name') == 'KenBurns' for a in segment['animations'] if isinstance(a, dict))
                    if not has_ken_burns:
                         segment['animations'].append({'name': 'KenBurns', 'duration': segment.get('duration', 3000)})

                # Transitions
                if transitions:
                     if 'transition' not in segment:
                         segment['transition'] = {'name': 'shake', 'duration': 500}

        elif track.get('type') == 'text':
             segments = track.get('segments', [])
             if not isinstance(segments, list):
                 segments = []
                 track['segments'] = segments

             for segment in segments:
                 if not isinstance(segment, dict):
                     continue
                 if effects:
                     if 'style' not in segment or not isinstance(segment['style'], dict):
                         segment['style'] = {}
                     segment['style']['effect'] = 'flower_text'

    return enriched

class JianyingProDraftEnricherSelfHealingGuard:
    """
    Stateful class to manage the 5-second snapshot undo mechanism.
    """
    def __init__(self, undo_window_seconds: int = 5):
        self.undo_window_seconds = undo_window_seconds
        self.snapshots = [] # List of tuples: (timestamp, draft_content)

    def apply_enrichment(self, draft_content: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Applies enrichment and saves a snapshot.
        """
        # Save snapshot before modification
        current_time = time.time()
        self.snapshots.append((current_time, copy.deepcopy(draft_content)))

        # Cleanup old snapshots
        self._cleanup_snapshots(current_time)

        return enrich_draft_content(draft_content, params)

    def undo(self) -> Optional[Dict[str, Any]]:
        """
        Reverts to the most recent valid snapshot within the time window.
        """
        current_time = time.time()
        self._cleanup_snapshots(current_time)

        if not self.snapshots:
            return None # Or raise an exception, or return some default state. Returning None signifies no valid undo state.

        # Pop the latest state
        _, previous_state = self.snapshots.pop()
        return previous_state

    def _cleanup_snapshots(self, current_time: float):
        """
        Removes snapshots older than the time window.
        """
        self.snapshots = [
            (ts, state) for ts, state in self.snapshots
            if (current_time - ts) <= self.undo_window_seconds
        ]
