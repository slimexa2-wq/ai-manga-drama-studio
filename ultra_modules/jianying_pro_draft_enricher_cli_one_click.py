import json
import logging
import argparse
import sys
import uuid
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def _enrich_materials(materials: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to enrich materials with default effects and BGM."""
    enriched = dict(materials)

    # 1. BGM Injection
    audios = enriched.get('audios', [])
    if not isinstance(audios, list):
        audios = []

    has_bgm = any(isinstance(audio, dict) and audio.get('type') == 'bgm' for audio in audios)
    if not has_bgm:
        audios.append({
            "id": f"auto_bgm_{uuid.uuid4().hex[:8]}",
            "type": "bgm",
            "name": "default_cinematic_bgm.mp3",
            "volume": 0.5
        })
    enriched['audios'] = audios

    # 2. Text Effects (花字特效)
    texts = enriched.get('texts', [])
    if not isinstance(texts, list):
        texts = []

    for text_item in texts:
        if isinstance(text_item, dict):
            if 'effect_id' not in text_item or not text_item['effect_id']:
                text_item['effect_id'] = f"default_text_effect_{uuid.uuid4().hex[:8]}"
    enriched['texts'] = texts

    # 3. Transitions (震屏转场)
    transitions = enriched.get('transitions', [])
    if not isinstance(transitions, list):
        transitions = []

    has_shake = any(isinstance(t, dict) and t.get('name') == 'shake' for t in transitions)
    if not has_shake:
        transitions.append({
            "id": f"auto_transition_shake_{uuid.uuid4().hex[:8]}",
            "name": "shake",
            "duration": 500000  # microseconds
        })
    enriched['transitions'] = transitions

    return enriched

def _enrich_video_tracks(video_tracks: list) -> list:
    """Pure function to enrich video tracks with KenBurns."""
    if not isinstance(video_tracks, list):
        return []

    enriched_tracks = []
    for track in video_tracks:
        if isinstance(track, dict):
            enriched_track = dict(track)
            clips = enriched_track.get('clips', [])
            if not isinstance(clips, list):
                clips = []

            enriched_clips = []
            for clip in clips:
                if isinstance(clip, dict):
                    enriched_clip = dict(clip)
                    animations = enriched_clip.get('animations', [])
                    if not isinstance(animations, list):
                        animations = []

                    has_kenburns = any(isinstance(a, dict) and a.get('type') == 'kenburns' for a in animations)
                    if not has_kenburns:
                        animations.append({
                            "id": f"auto_anim_kenburns_{uuid.uuid4().hex[:8]}",
                            "type": "kenburns",
                            "start_scale": 1.0,
                            "end_scale": 1.1
                        })
                    enriched_clip['animations'] = animations
                    enriched_clips.append(enriched_clip)
                else:
                    enriched_clips.append(clip)
            enriched_track['clips'] = enriched_clips
            enriched_tracks.append(enriched_track)
        else:
            enriched_tracks.append(track)

    return enriched_tracks


class JianyingProDraftEnricherCliOneClick:
    """
    Zero-config CLI and programmatic interface for enriching draft_content.json
    with self-healing and default fallbacks.
    """

    def process_draft(self, draft_content: Any) -> Dict[str, Any]:
        """
        Enriches a single draft content structure.
        Uses extreme defensive programming (fallbacks, missing keys) to guarantee success.
        """
        if not isinstance(draft_content, dict):
            logger.warning("Input is not a dictionary. Initializing empty draft template.")
            draft_content = {}

        # Deep-copy-like mutation via pure functions
        enriched = dict(draft_content)

        materials = enriched.get('materials', {})
        if not isinstance(materials, dict):
            materials = {}
        enriched['materials'] = _enrich_materials(materials)

        video_track = enriched.get('video_track', [])
        enriched['video_track'] = _enrich_video_tracks(video_track)

        return enriched

    def run_file(self, file_path: str = "draft_content.json", output_path: str = None) -> None:
        """Read, enrich, and write back (or to output_path)."""
        data = {}

        # Self-healing: if file does not exist or is invalid JSON, use empty dict
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read JSON from {file_path} due to {e}. Using empty template.")
                data = {}
        else:
            logger.warning(f"File {file_path} does not exist. Using empty template.")
            data = {}

        enriched = self.process_draft(data)

        out = output_path if output_path else file_path

        try:
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(enriched, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully enriched draft at {out}")
        except IOError as e:
            logger.error(f"Failed to write enriched draft to {out}: {e}")

def cli_main() -> None:
    """
    Zero-parameter one-click CLI entry point.
    Defaults to processing 'draft_content.json' in current directory.
    """
    parser = argparse.ArgumentParser(description="One-click enricher for Jianying Pro draft_content.json.")
    parser.add_argument('--input', type=str, default='draft_content.json', help='Input draft JSON path')
    parser.add_argument('--output', type=str, default=None, help='Output draft JSON path (defaults to overwrite input)')
    args = parser.parse_args()

    enricher = JianyingProDraftEnricherCliOneClick()
    enricher.run_file(args.input, args.output)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli_main()
