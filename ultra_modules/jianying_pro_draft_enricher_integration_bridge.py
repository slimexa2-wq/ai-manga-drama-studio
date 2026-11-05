import copy
import logging

# Set up logging for audit trails
logger = logging.getLogger(__name__)

class JianyingProDraftEnricherIntegrationBridge:
    """
    Bridge for enriching Jianying Pro Draft configurations.
    Handles floral text effects, shake transitions, KenBurns camera movements, and BGM injections.
    Features cross-system seamless data bridging and automatic forward compatibility for schema versions.
    Zero-friction design: auto-heals dirty data and fills missing parameters with sensible defaults.
    """

    # Schema mapping configuration for backward compatibility
    # Maps legacy keys to current expected keys
    LEGACY_SCHEMA_MAP = {
        'track_list': 'tracks',
        'text_materials': 'texts',
        'audio_materials': 'audios',
        'effect_materials': 'effects',
        'transition_materials': 'transitions'
    }

    @staticmethod
    def _heal_data_type(data, key, expected_type, default_val):
        """Silently heal dirty data ensuring it matches the expected type."""
        val = data.get(key, None)
        if val is None or not isinstance(val, expected_type):
            data[key] = copy.deepcopy(default_val)
        return data[key]

    @staticmethod
    def _apply_schema_compatibility(draft: dict) -> dict:
        """
        Automatically identifies legacy version fields and silently maps them
        to the current schema to ensure forward compatibility.
        """
        for legacy_key, modern_key in JianyingProDraftEnricherIntegrationBridge.LEGACY_SCHEMA_MAP.items():
            if legacy_key in draft and modern_key not in draft:
                draft[modern_key] = draft.pop(legacy_key)
            elif legacy_key in draft and modern_key in draft:
                # If both exist, merge or favor modern, here we drop legacy to clean up
                draft.pop(legacy_key)
        return draft

    @staticmethod
    def enrich(draft: dict = None, config: dict = None) -> dict:
        """
        Enriches the draft with effects, transitions, camera movements, and BGM based on config.

        :param draft: The Jianying Pro draft_content.json payload.
        :param config: The enrichment configuration.
        :return: The enriched draft payload.
        """
        # 1. Missing parameter fallbacks (reasonable defaults)
        if draft is None or not isinstance(draft, dict):
            logger.warning("Invalid or missing draft provided. Initializing empty draft.")
            draft = {}

        # Deep copy to avoid mutating the original input if it's referenced elsewhere
        draft = copy.deepcopy(draft)

        if config is None or not isinstance(config, dict):
            logger.info("Missing config provided. Using sensible defaults.")
            config = {}

        # 2. Schema version auto-forward compatibility
        draft = JianyingProDraftEnricherIntegrationBridge._apply_schema_compatibility(draft)

        # 3. Dirty data auto-healing for core skeleton
        materials = JianyingProDraftEnricherIntegrationBridge._heal_data_type(draft, 'materials', dict, {})
        tracks = JianyingProDraftEnricherIntegrationBridge._heal_data_type(draft, 'tracks', list, [])

        # Heal specific material lists
        texts = JianyingProDraftEnricherIntegrationBridge._heal_data_type(materials, 'texts', list, [])
        audios = JianyingProDraftEnricherIntegrationBridge._heal_data_type(materials, 'audios', list, [])
        effects = JianyingProDraftEnricherIntegrationBridge._heal_data_type(materials, 'effects', list, [])
        transitions = JianyingProDraftEnricherIntegrationBridge._heal_data_type(materials, 'transitions', list, [])

        # 4. Processing config injections

        # BGM Injection
        bgm_enabled = config.get('enable_bgm', True) # Default to true
        if bgm_enabled:
            bgm_path = config.get('bgm_path', 'default_bgm.mp3')
            # Add audio material
            bgm_material_id = f"audio_{len(audios)}"
            audios.append({
                "id": bgm_material_id,
                "type": "audio",
                "path": str(bgm_path),
                "name": "BGM"
            })

            # Find or create audio track
            audio_track = next((t for t in tracks if isinstance(t, dict) and t.get('type') == 'audio'), None)
            if not audio_track:
                audio_track = {"id": f"track_{len(tracks)}", "type": "audio", "segments": []}
                tracks.append(audio_track)

            # Auto-heal segments in audio track
            segments = JianyingProDraftEnricherIntegrationBridge._heal_data_type(audio_track, 'segments', list, [])
            segments.append({
                "id": f"segment_{len(segments)}",
                "material_id": bgm_material_id,
                "start": 0,
                "duration": config.get('bgm_duration', 10000) # Default duration
            })

        # Text Effects (Floral Text)
        floral_text_enabled = config.get('enable_floral_text', False)
        if floral_text_enabled:
            for text_mat in texts:
                if isinstance(text_mat, dict):
                    # Auto-heal effects property
                    text_effects = JianyingProDraftEnricherIntegrationBridge._heal_data_type(text_mat, 'effects', list, [])
                    text_effects.append({
                        "name": "Floral",
                        "type": "floral_text_effect",
                        "intensity": config.get('floral_intensity', 0.8)
                    })

        # Transitions (Shake)
        shake_transition_enabled = config.get('enable_shake_transition', False)
        if shake_transition_enabled:
            transition_id = f"transition_{len(transitions)}"
            transitions.append({
                "id": transition_id,
                "name": "Shake",
                "type": "shake_transition",
                "duration": config.get('shake_duration', 500)
            })

            # Apply to video tracks between segments
            for track in tracks:
                if isinstance(track, dict) and track.get('type') == 'video':
                    segments = track.get('segments')
                    if isinstance(segments, list) and len(segments) > 1:
                        # Append transition to first segment for simplicity in demonstration
                        first_segment = segments[0]
                        if isinstance(first_segment, dict):
                            seg_transitions = JianyingProDraftEnricherIntegrationBridge._heal_data_type(first_segment, 'transitions', list, [])
                            seg_transitions.append(transition_id)

        # KenBurns Camera Movements
        kenburns_enabled = config.get('enable_ken_burns', False)
        if kenburns_enabled:
            effect_id = f"effect_{len(effects)}"
            effects.append({
                "id": effect_id,
                "name": "KenBurns",
                "type": "ken_burns_movement",
                "scale_start": config.get('kb_scale_start', 1.0),
                "scale_end": config.get('kb_scale_end', 1.2)
            })

            # Apply to all video segments
            for track in tracks:
                if isinstance(track, dict) and track.get('type') == 'video':
                    segments = track.get('segments')
                    if isinstance(segments, list):
                        for segment in segments:
                            if isinstance(segment, dict):
                                seg_effects = JianyingProDraftEnricherIntegrationBridge._heal_data_type(segment, 'effects', list, [])
                                seg_effects.append(effect_id)

        return draft
