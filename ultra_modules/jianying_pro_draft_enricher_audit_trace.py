import json
import uuid
import copy
from typing import Dict, Any, List, Optional, Union

class JianyingProDraftEnricherAuditTrace:
    """
    Robust backend class for enriching Jianying Pro draft content JSON.
    Handles missing params, dirty data healing, text style updates, transitions, KenBurns zoom, BGM injection.
    Logs every action to an audit trail and captures a snapshot for undo purposes.
    """

    def __init__(self, draft_content: Union[str, Dict[str, Any]]):
        """
        Initializes the enricher with draft content.
        :param draft_content: JSON string or dictionary representing the draft content.
        """
        self.audit_log: List[Dict[str, Any]] = []
        self._initial_snapshot = None
        self.draft_data = self._parse_and_heal(draft_content)

        # Save snapshot for undo after initial parsing
        self._save_snapshot()

    def _parse_and_heal(self, draft_content: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parses and heals dirty data, applying defaults to missing structures."""
        # 1. Parse JSON if string
        if isinstance(draft_content, str):
            try:
                data = json.loads(draft_content)
                self._audit_log("PARSE_JSON", {"status": "success", "message": "Successfully parsed JSON string."})
            except json.JSONDecodeError as e:
                self._audit_log("PARSE_JSON", {"status": "error", "message": f"Failed to parse JSON: {e}. Using empty default."})
                data = {}
        else:
            data = copy.deepcopy(draft_content)
            self._audit_log("PARSE_DICT", {"status": "success", "message": "Loaded draft content dictionary."})

        # 2. Heal dirty data and apply missing parameter fallbacks (defaults to reasonable values)
        # We need a structure with at least tracks and materials
        if not isinstance(data, dict):
            self._audit_log("HEAL_DATA", {"issue": "Root is not a dict", "fix": "Initialized empty dict"})
            data = {}

        if "materials" not in data or not isinstance(data["materials"], dict):
            self._audit_log("HEAL_DATA", {"issue": "Missing or invalid 'materials'", "fix": "Created empty 'materials' dict"})
            data["materials"] = {}

        materials_collections = ["texts", "transitions", "audios", "video_effects", "materials"]
        for col in materials_collections:
            if col not in data["materials"] or not isinstance(data["materials"][col], list):
                self._audit_log("HEAL_DATA", {"issue": f"Missing or invalid materials collection '{col}'", "fix": f"Created empty list for '{col}'"})
                data["materials"][col] = []

        if "tracks" not in data or not isinstance(data["tracks"], list):
            self._audit_log("HEAL_DATA", {"issue": "Missing or invalid 'tracks'", "fix": "Created empty 'tracks' list"})
            data["tracks"] = []

        return data

    def _save_snapshot(self):
        """Saves a snapshot of the current state for undo capabilities."""
        self._initial_snapshot = copy.deepcopy(self.draft_data)
        self._audit_log("SNAPSHOT_SAVED", {"message": "Initial snapshot saved for one-click undo."})

    def undo(self) -> Dict[str, Any]:
        """Restores the state to the initial snapshot."""
        if self._initial_snapshot is not None:
            self.draft_data = copy.deepcopy(self._initial_snapshot)
            self._audit_log("UNDO_ACTION", {"message": "Restored to initial snapshot."})
        return self.draft_data

    def _audit_log(self, action: str, details: Dict[str, Any]):
        """Logs an action to the audit trail."""
        log_entry = {
            "action": action,
            "details": details,
            "timestamp": "captured_at_runtime" # Simplified for this example
        }
        self.audit_log.append(log_entry)

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Returns the audit log."""
        return self.audit_log

    def apply_text_styles(self, stroke_color: str = "#000000", shadow_color: str = "#000000", stroke_width: float = 0.08, shadow_alpha: float = 0.8):
        """Silently applies text styles to all texts in the draft."""
        texts = self.draft_data.get("materials", {}).get("texts", [])
        updated_count = 0
        for txt in texts:
            if not isinstance(txt, dict):
                continue

            # Apply reasonable defaults if the text object is missing fields
            txt_content = txt.get("content", "{}")
            try:
                # Try to parse Jianying's nested JSON string format
                content_obj = json.loads(txt_content)
            except json.JSONDecodeError:
                content_obj = {"text": txt_content}

            txt["text_color"] = txt.get("text_color", "#FFFFFF")

            # Apply styles
            txt["has_stroke"] = True
            txt["stroke_color"] = stroke_color
            txt["stroke_width"] = stroke_width

            txt["has_shadow"] = True
            txt["shadow_color"] = shadow_color
            txt["shadow_alpha"] = shadow_alpha

            updated_count += 1

        self._audit_log("APPLY_TEXT_STYLES", {
            "stroke_color": stroke_color,
            "shadow_color": shadow_color,
            "updated_items": updated_count
        })

    def inject_transition(self, transition_name: str = "shake", duration: int = 500000):
        """Silently injects a transition effect between consecutive video segments on the main track."""
        tracks = self.draft_data.get("tracks", [])
        transitions_materials = self.draft_data.setdefault("materials", {}).setdefault("transitions", [])

        main_track = next((t for t in tracks if isinstance(t, dict) and t.get("type") == "video"), None)
        if not main_track:
            self._audit_log("INJECT_TRANSITION", {"status": "skipped", "reason": "No main video track found."})
            return

        segments = main_track.get("segments", [])
        injected_count = 0

        for i in range(len(segments) - 1):
            seg1 = segments[i]
            seg2 = segments[i+1]

            if not isinstance(seg1, dict) or not isinstance(seg2, dict):
                continue

            # Create a transition material
            trans_id = str(uuid.uuid4())
            transitions_materials.append({
                "id": trans_id,
                "type": "transition",
                "name": transition_name,
                "duration": duration
            })

            # Link it between the segments (Jianying usually attaches transition to the right segment or track level, we simulate it on the segment)
            seg1["extra_material_refs"] = seg1.get("extra_material_refs", [])
            seg1["extra_material_refs"].append(trans_id)
            injected_count += 1

        self._audit_log("INJECT_TRANSITION", {
            "transition_name": transition_name,
            "injected_count": injected_count
        })

    def inject_ken_burns(self, zoom_factor: float = 1.1):
        """Silently injects Ken Burns (pan/zoom) effects into video segments."""
        tracks = self.draft_data.get("tracks", [])
        applied_count = 0
        for track in tracks:
            if not isinstance(track, dict) or track.get("type") != "video":
                continue

            for seg in track.get("segments", []):
                if not isinstance(seg, dict):
                    continue

                seg.setdefault("clip", {})
                clip = seg["clip"]
                if not isinstance(clip, dict):
                    clip = {}
                    seg["clip"] = clip

                # Setup animation for zoom
                clip.setdefault("scale", {"x": 1.0, "y": 1.0})
                clip["scale"] = {"x": zoom_factor, "y": zoom_factor}
                clip["animation"] = {"type": "ken_burns", "zoom": zoom_factor}
                applied_count += 1

        self._audit_log("INJECT_KEN_BURNS", {
            "zoom_factor": zoom_factor,
            "applied_count": applied_count
        })

    def inject_bgm(self, audio_path: str, volume: float = 0.5):
        """Silently injects a background music track."""
        if not audio_path:
            self._audit_log("INJECT_BGM", {"status": "skipped", "reason": "Empty audio_path provided."})
            return

        tracks = self.draft_data.get("tracks", [])
        audios_materials = self.draft_data.setdefault("materials", {}).setdefault("audios", [])

        audio_id = str(uuid.uuid4())
        audios_materials.append({
            "id": audio_id,
            "type": "audio",
            "path": audio_path,
            "name": audio_path.split("/")[-1]
        })

        bgm_track = {
            "id": str(uuid.uuid4()),
            "type": "audio",
            "segments": [
                {
                    "id": str(uuid.uuid4()),
                    "material_id": audio_id,
                    "volume": volume,
                    "target_timerange": {"start": 0, "duration": 999999999} # Infinite duration as default placeholder
                }
            ]
        }

        tracks.append(bgm_track)
        self._audit_log("INJECT_BGM", {
            "audio_path": audio_path,
            "volume": volume,
            "audio_id": audio_id
        })


def enrich_jianying_draft(
    draft_content: Union[str, Dict[str, Any]],
    bgm_path: Optional[str] = None,
    zoom_factor: float = 1.1,
    transition_name: str = "shake",
    stroke_color: str = "#000000"
) -> Dict[str, Any]:
    """
    Zero-friction frontend wrapper for enriching a Jianying Pro draft.
    Provides a simple one-click entry point. Missing parameters use reasonable defaults.
    Backend handles all dirty data and logs everything for audit.

    :param draft_content: The original draft JSON string or dictionary.
    :param bgm_path: Optional path to background music.
    :param zoom_factor: Zoom factor for KenBurns effect.
    :param transition_name: Name of the transition to inject.
    :param stroke_color: Stroke color for texts.
    :return: The fully enriched draft dictionary ready for saving.
    """
    enricher = JianyingProDraftEnricherAuditTrace(draft_content)

    enricher.apply_text_styles(stroke_color=stroke_color)
    enricher.inject_transition(transition_name=transition_name)
    enricher.inject_ken_burns(zoom_factor=zoom_factor)

    if bgm_path:
        enricher.inject_bgm(audio_path=bgm_path)

    return enricher.draft_data
