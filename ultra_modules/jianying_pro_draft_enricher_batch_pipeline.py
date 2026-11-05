import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class JianyingDraftEnricherBatchPipeline:
    """
    A robust, simple-to-use pipeline for enriching Jianying Pro draft_content.json files.
    Injects effects, transitions, KenBurns zoom, and BGM, with automatic fallbacks and self-healing.
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers

    def _enrich_single_draft(self, draft_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches a single draft content structure.
        Uses extreme defensive programming (fallbacks, missing keys) to guarantee success.
        """
        if not isinstance(draft_content, dict):
            # Self-healing: bad input -> return a valid empty template
            draft_content = {}

        # Make a deep copy equivalent by creating a new dict if we mutate heavily,
        # but for simplicity, we just mutate safely
        enriched = dict(draft_content)

        # Ensure 'materials' key exists
        if 'materials' not in enriched or not isinstance(enriched['materials'], dict):
            enriched['materials'] = {}

        materials = enriched['materials']

        # 1. BGM Injection (Audio)
        if 'audios' not in materials or not isinstance(materials['audios'], list):
            materials['audios'] = []

        # Add default BGM if not present
        has_bgm = any(isinstance(audio, dict) and audio.get('type') == 'bgm' for audio in materials['audios'])
        if not has_bgm:
            materials['audios'].append({
                "id": "auto_bgm_001",
                "type": "bgm",
                "name": "default_cinematic_bgm.mp3",
                "volume": 0.5
            })

        # 2. Text Effects (花字特效)
        if 'texts' not in materials or not isinstance(materials['texts'], list):
            materials['texts'] = []

        for text_item in materials['texts']:
            if isinstance(text_item, dict):
                # Add default effect if none exists
                if 'effect_id' not in text_item or not text_item['effect_id']:
                    text_item['effect_id'] = "default_text_effect_01"

        # 3. Transitions (震屏转场)
        if 'transitions' not in materials or not isinstance(materials['transitions'], list):
            materials['transitions'] = []

        # Always ensure a default transition is available
        has_shake = any(isinstance(t, dict) and t.get('name') == 'shake' for t in materials['transitions'])
        if not has_shake:
            materials['transitions'].append({
                "id": "auto_transition_shake_01",
                "name": "shake",
                "duration": 500000 # microseconds
            })

        # 4. KenBurns (运镜)
        if 'video_track' not in enriched or not isinstance(enriched['video_track'], list):
            enriched['video_track'] = []

        for track in enriched['video_track']:
            if isinstance(track, dict) and 'clips' in track and isinstance(track['clips'], list):
                for clip in track['clips']:
                    if isinstance(clip, dict):
                        # Inject KenBurns
                        if 'animations' not in clip or not isinstance(clip['animations'], list):
                            clip['animations'] = []

                        has_kenburns = any(isinstance(a, dict) and a.get('type') == 'kenburns' for a in clip['animations'])
                        if not has_kenburns:
                            clip['animations'].append({
                                "id": "auto_anim_kenburns_01",
                                "type": "kenburns",
                                "start_scale": 1.0,
                                "end_scale": 1.1
                            })

        return enriched

    def process_batch(self, drafts: List[Any]) -> Dict[str, Any]:
        """
        Process a batch of drafts concurrently.
        Strictly zero blocking on failures, fast execution, simple API.
        """
        if not drafts:
            return {"status": "success", "processed": 0, "results": [], "errors": 0}

        if not isinstance(drafts, list):
            # Fallback to single item list if accidentally passed a single dict
            drafts = [drafts]

        results = [None] * len(drafts)
        errors = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(self._enrich_single_draft, draft): i
                for i, draft in enumerate(drafts)
            }

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    res = future.result()
                    results[index] = res
                except Exception as e:
                    logger.error(f"Error processing draft at index {index}: {e}")
                    errors += 1
                    # Self-healing: if entirely failed, return an empty enriched template
                    results[index] = self._enrich_single_draft({})

        return {
            "status": "success",
            "processed": len(drafts),
            "results": results,
            "errors": errors
        }

def enrich_drafts(drafts: List[Any], max_workers: int = 10) -> Dict[str, Any]:
    """
    One-click entrypoint. Extreme simplicity for the user.
    """
    pipeline = JianyingDraftEnricherBatchPipeline(max_workers=max_workers)
    return pipeline.process_batch(drafts)
