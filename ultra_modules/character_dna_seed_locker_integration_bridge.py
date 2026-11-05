import copy

class CharacterDnaSeedLockerIntegrationBridge:
    """
    Cross-episode Character Visual DNA (hair color/eye color/clothing/style suffix/fixed seed)
    Hard Locker & Schema Version Forward Compatibility Converter.

    Adheres strictly to the principles:
    - Zero configuration auto-mapping
    - Silent fix for dirty data
    - Auto-fallback for missing parameters
    - Extreme simple usage via bridge_dna_schema
    """

    DEFAULT_DNA = {
        "hair_color": "black",
        "eye_color": "black",
        "clothing": "casual wear",
        "style_suffix": "anime style, masterpiece, best quality",
        "fixed_seed": 42
    }

    def bridge_dna_schema(self, payload: dict) -> dict:
        """
        Automatically identifies legacy/new schema differences and silently maps them.
        Heals dirty data and applies defaults for missing params.
        """
        if not isinstance(payload, dict):
            # Extreme boundary: not a dict at all. Auto fallback to a fresh dict with defaults.
            return {"character_dna": copy.deepcopy(self.DEFAULT_DNA)}

        result = copy.deepcopy(payload)

        # Determine where the DNA info is located or initialize it
        if "character_dna" not in result:
            result["character_dna"] = {}
        elif not isinstance(result["character_dna"], dict):
            # Dirty data self-healing: if it's there but corrupted, overwrite it.
            result["character_dna"] = {}

        dna_section = result["character_dna"]

        # 1. Map legacy fields to new fields
        # Legacy fields might have been placed directly in payload or under different names in dna_section
        legacy_mappings = {
            "hair": "hair_color",
            "eye": "eye_color",
            "clothes": "clothing",
            "outfit": "clothing",
            "style": "style_suffix",
            "seed": "fixed_seed"
        }

        # Check payload level legacy fields and migrate them to dna_section if they exist
        for legacy, new_key in legacy_mappings.items():
            if legacy in result:
                val = result.pop(legacy)
                # Only use legacy value if new key is missing in dna_section
                if new_key not in dna_section:
                    dna_section[new_key] = val

            if legacy in dna_section:
                val = dna_section.pop(legacy)
                if new_key not in dna_section:
                    dna_section[new_key] = val

        # 2. Dirty data self-healing & type casting
        # fixed_seed should be int
        if "fixed_seed" in dna_section:
            try:
                # Handle dirty strings or floats
                if dna_section["fixed_seed"] is None:
                    dna_section["fixed_seed"] = self.DEFAULT_DNA["fixed_seed"]
                else:
                    dna_section["fixed_seed"] = int(float(dna_section["fixed_seed"]))
            except (ValueError, TypeError):
                dna_section["fixed_seed"] = self.DEFAULT_DNA["fixed_seed"]

        # All other fields should be valid strings. Heal empty/None/invalid types.
        for key in ["hair_color", "eye_color", "clothing", "style_suffix"]:
            if key in dna_section:
                val = dna_section[key]
                if not isinstance(val, str) or not str(val).strip():
                    # Invalid type or empty string -> remove to trigger fallback
                    dna_section.pop(key)

        # 3. Auto-fallback for missing parameters
        for key, default_val in self.DEFAULT_DNA.items():
            if key not in dna_section:
                dna_section[key] = default_val

        return result
