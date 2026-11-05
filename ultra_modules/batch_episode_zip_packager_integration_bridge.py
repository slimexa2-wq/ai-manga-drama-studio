import zipfile
import io
import json
import logging
from typing import Dict, Any, List

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaConverter:
    """
    Seamlessly converts schemas from old to new formats, handling dirty data and missing parameters silently.
    """
    @staticmethod
    def convert(data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            # Extreme boundary: not a dict
            return {
                "version": "2.0",
                "episodes": [],
                "global_settings": {"resolution": "1080x1920", "fps": 30}
            }

        converted = {
            "version": "2.0",
            "episodes": [],
            "global_settings": {
                "resolution": "1080x1920",
                "fps": 30
            }
        }

        # Handle global settings mappings and fallbacks
        gs = data.get("global_settings") or data.get("settings") or {}
        if not isinstance(gs, dict):
            gs = {}
        converted["global_settings"]["resolution"] = gs.get("resolution", gs.get("res", "1080x1920"))
        try:
            converted["global_settings"]["fps"] = int(gs.get("fps", gs.get("frame_rate", 30)))
        except (ValueError, TypeError):
            converted["global_settings"]["fps"] = 30

        # Handle episodes mappings
        episodes_raw = data.get("episodes") or data.get("eps") or []
        if not isinstance(episodes_raw, list):
            episodes_raw = []

        seen_ids = set()

        for ep_idx, ep in enumerate(episodes_raw):
            if not isinstance(ep, dict):
                continue

            # Map fields with defaults
            ep_id = str(ep.get("id", ep.get("episode_id", f"ep_{ep_idx + 1}")))

            # Deduplication
            if ep_id in seen_ids:
                logger.warning(f"Duplicate episode ID found: {ep_id}. Generating a unique one.")
                ep_id = f"{ep_id}_dedup_{ep_idx}"
            seen_ids.add(ep_id)

            converted_ep = {
                "id": ep_id,
                "title": str(ep.get("title", ep.get("name", f"Episode {ep_id}"))),
                "mp4_path": str(ep.get("mp4_path", ep.get("video_file", ""))),
                "srt_path": str(ep.get("srt_path", ep.get("subtitle_file", ""))),
                "draft_json": ep.get("draft_json", ep.get("jianying_draft", {})),
                "prompts": ep.get("prompts", ep.get("ai_prompts", {}))
            }

            # Ensure draft_json and prompts are dicts
            if not isinstance(converted_ep["draft_json"], dict):
                converted_ep["draft_json"] = {}
            if not isinstance(converted_ep["prompts"], dict):
                converted_ep["prompts"] = {}

            converted["episodes"].append(converted_ep)

        return converted

class BatchEpisodeZipPackager:
    """
    Packages episodes into a ZIP file.
    Heals missing files with dummy content or skips gracefully.
    """
    @staticmethod
    def package_to_memory(schema_data: Dict[str, Any], file_reader_callable=None) -> bytes:
        """
        Creates a ZIP archive in memory containing all episodes' assets.
        file_reader_callable: a function(path: str) -> bytes, for testing. If None, tries to read from disk.
        """
        zip_buffer = io.BytesIO()

        # We define a default file reader if none provided
        def default_reader(path: str) -> bytes:
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception:
                return None

        reader = file_reader_callable or default_reader

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Save the schema itself
            zip_file.writestr("schema_manifest.json", json.dumps(schema_data, indent=2))

            for ep in schema_data.get("episodes", []):
                ep_id = ep.get("id", "unknown")
                base_dir = f"episode_{ep_id}/"

                # MP4
                mp4_path = ep.get("mp4_path", "")
                mp4_content = None
                if mp4_path:
                    mp4_content = reader(mp4_path)
                if not mp4_content:
                    logger.warning(f"Missing MP4 for {ep_id}. Healing with dummy content.")
                    mp4_content = b"dummy_mp4_data"
                zip_file.writestr(f"{base_dir}video.mp4", mp4_content)

                # SRT
                srt_path = ep.get("srt_path", "")
                srt_content = None
                if srt_path:
                    srt_content = reader(srt_path)
                if not srt_content:
                    logger.warning(f"Missing SRT for {ep_id}. Healing with empty subtitle.")
                    srt_content = b"1\n00:00:00,000 --> 00:00:01,000\n[Dummy Subtitle]"

                # For robustness, handle if srt_content is a string vs bytes
                if isinstance(srt_content, str):
                    srt_content = srt_content.encode('utf-8')

                zip_file.writestr(f"{base_dir}subtitles.srt", srt_content)

                # Jianying Draft
                draft = ep.get("draft_json", {})
                if not draft:
                    draft = {"version": "1.0", "empty": True}
                zip_file.writestr(f"{base_dir}draft_content.json", json.dumps(draft, indent=2))

                # Prompts
                prompts = ep.get("prompts", {})
                zip_file.writestr(f"{base_dir}prompts.json", json.dumps(prompts, indent=2))

        return zip_buffer.getvalue()

def bridge_and_package(raw_input_data: Any, file_reader_callable=None) -> bytes:
    """
    One-click bridge function.
    Converts any dirty input data to standard schema and outputs a ZIP archive containing all assets.
    """
    logger.info("Starting bridge_and_package process.")
    clean_schema = SchemaConverter.convert(raw_input_data)
    zip_bytes = BatchEpisodeZipPackager.package_to_memory(clean_schema, file_reader_callable)
    logger.info("Packaging complete.")
    return zip_bytes
