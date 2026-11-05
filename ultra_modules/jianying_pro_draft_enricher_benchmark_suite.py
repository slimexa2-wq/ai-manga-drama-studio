import time
import json
import uuid
import random
from typing import Dict, Any, List, Optional

class JianyingDraftEnricher:
    """
    Enriches Jianying Pro draft files (draft_content.json) with text effects,
    transitions, KenBurns effects, and BGM.
    Designed for high performance and fault tolerance (auto-healing).
    """

    def __init__(self):
        # Configuration could be loaded here if needed.
        pass

    def enrich_draft(self, draft_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for enriching a draft.
        """
        if draft_content is None or not isinstance(draft_content, dict):
            # Fallback to an empty draft structure if dirty or missing data
            draft_content = self._get_default_draft()

        enriched = draft_content.copy()

        # Apply various enrichments
        enriched = self._apply_text_effects(enriched)
        enriched = self._apply_transitions(enriched)
        enriched = self._apply_kenburns(enriched)
        enriched = self._apply_bgm(enriched)

        return enriched

    def _get_default_draft(self) -> Dict[str, Any]:
        """Returns a minimal valid draft structure."""
        return {
            "id": str(uuid.uuid4()),
            "materials": {
                "texts": [],
                "transitions": [],
                "audios": [],
                "canvases": []
            },
            "tracks": []
        }

    def _apply_text_effects(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Adds text effects to any text materials found, or provides defaults if missing."""
        materials = draft.get("materials", {})
        texts = materials.get("texts", [])

        if not isinstance(texts, list):
            texts = []

        for text_item in texts:
            if not isinstance(text_item, dict):
                continue

            # Auto-heal missing or invalid text content
            content = text_item.get("content", "")
            if not isinstance(content, str) or not content:
                text_item["content"] = "Default Text"

            # Inject text effects (e.g., stroke, shadow)
            text_item["text_effects"] = [
                {
                    "id": str(uuid.uuid4()),
                    "type": "stroke",
                    "color": "#000000",
                    "width": 2
                }
            ]

        materials["texts"] = texts
        draft["materials"] = materials
        return draft

    def _apply_transitions(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Applies a default 'shake' transition if none exist."""
        materials = draft.get("materials", {})
        transitions = materials.get("transitions", [])

        if not isinstance(transitions, list):
            transitions = []

        if not transitions:
             transitions.append({
                 "id": str(uuid.uuid4()),
                 "type": "shake",
                 "duration": 500 # ms
             })

        materials["transitions"] = transitions
        draft["materials"] = materials
        return draft

    def _apply_kenburns(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Applies KenBurns camera movement to canvases/images."""
        materials = draft.get("materials", {})
        canvases = materials.get("canvases", [])

        if not isinstance(canvases, list):
             canvases = []

        for canvas in canvases:
             if not isinstance(canvas, dict):
                 continue
             canvas["camera_movement"] = {
                 "type": "kenburns",
                 "start_scale": 1.0,
                 "end_scale": 1.1,
                 "duration": 3000
             }

        materials["canvases"] = canvases
        draft["materials"] = materials
        return draft

    def _apply_bgm(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Injects a default BGM if audio track is empty."""
        materials = draft.get("materials", {})
        audios = materials.get("audios", [])

        if not isinstance(audios, list):
            audios = []

        if not audios:
            audios.append({
                "id": str(uuid.uuid4()),
                "type": "bgm",
                "path": "default_bgm.mp3",
                "volume": 0.5
            })

        materials["audios"] = audios
        draft["materials"] = materials
        return draft

class SyntheticFixtureGenerator:
    """
    Generates synthetic draft datasets (fixtures) including edge cases:
    nulls, gibberish, massive concurrency simulation, cross-year boundaries.
    """

    @staticmethod
    def generate_normal_draft() -> Dict[str, Any]:
        return {
            "id": "draft_normal_1",
            "materials": {
                "texts": [{"id": "t1", "content": "Hello World"}],
                "transitions": [],
                "audios": [],
                "canvases": [{"id": "c1", "type": "image"}]
            },
            "tracks": []
        }

    @staticmethod
    def generate_dirty_draft() -> Dict[str, Any]:
        """Draft with nulls, wrong types, and missing keys."""
        return {
            "id": None,
            "materials": {
                "texts": [{"id": "t1", "content": None}, "not_a_dict"],
                "transitions": "not_a_list",
                # audios missing entirely
            }
            # tracks missing
        }

    @staticmethod
    def generate_gibberish_draft() -> Dict[str, Any]:
        """Draft with random gibberish strings."""
        return {
             "id": "draft_gibberish",
             "materials": {
                 "texts": [{"id": "t1", "content": "锟斤拷\x00\x01\x02" * 10}],
                 "transitions": [{"type": "!@#$%^&*()"}],
                 "audios": [{"path": "/dev/null/\0"}],
                 "canvases": [{"type": "NaN"}]
             }
        }

    @staticmethod
    def generate_massive_draft(items_count: int = 10000) -> Dict[str, Any]:
        """Draft to test performance with many items."""
        return {
            "id": "draft_massive",
            "materials": {
                "texts": [{"id": f"t_{i}", "content": f"Text {i}"} for i in range(items_count)],
                "transitions": [{"id": f"tr_{i}", "type": "shake"} for i in range(items_count)],
                "audios": [{"id": f"a_{i}", "path": f"audio_{i}.mp3"} for i in range(items_count)],
                "canvases": [{"id": f"c_{i}", "type": "image"} for i in range(items_count)]
            },
            "tracks": []
        }

    @staticmethod
    def generate_cross_boundary_draft() -> Dict[str, Any]:
        """Draft simulating cross-year/month boundary data (e.g., timestamps)."""
        return {
            "id": "draft_boundary",
             "metadata": {
                 "created_at": "2023-12-31T23:59:59Z",
                 "updated_at": "2024-01-01T00:00:01Z"
             },
             "materials": {
                 "texts": [],
                 "transitions": [],
                 "audios": [],
                 "canvases": []
             }
        }


class BenchmarkSuite:
    """
    Performance benchmarking for JianyingDraftEnricher.
    """

    @staticmethod
    def run_benchmark(enricher: JianyingDraftEnricher, items_count: int = 10000) -> float:
        """
        Runs the enricher against a massive draft and returns the execution time in milliseconds.
        """
        draft = SyntheticFixtureGenerator.generate_massive_draft(items_count)

        start_time = time.perf_counter()
        enricher.enrich_draft(draft)
        end_time = time.perf_counter()

        # Return time in milliseconds
        return (end_time - start_time) * 1000
