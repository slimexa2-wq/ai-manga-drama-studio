import copy
from typing import Dict, Any, List, Tuple

class Veo3CameraMotionPrompter:
    """
    Compiler for Google Veo 3 / Sora 2 cinematic camera motion prompts.
    Provides backend full-chain trace audit log and difference highlighter.
    """

    # Valid motions and their standardized cinematic equivalents
    VALID_MOTIONS = {
        "push": "dolly in",
        "pull": "dolly out",
        "dolly in": "dolly in",
        "dolly out": "dolly out",
        "pan left": "pan left",
        "pan right": "pan right",
        "tilt up": "tilt up",
        "tilt down": "tilt down",
        "orbit": "orbit",
        "surround": "orbit",
        "zoom in": "zoom in",
        "zoom out": "zoom out",
        "crane up": "pedestal up",
        "pedestal up": "pedestal up",
        "crane down": "pedestal down",
        "pedestal down": "pedestal down",
    }

    DEFAULT_SPEED = "slow"
    DEFAULT_MOTION = "static"

    def compile(self, raw_input: Any) -> Dict[str, Any]:
        """
        Compiles raw instructions into a cinematic prompt and returns the result and audit trail.
        """
        audit_trail = []

        # 1. Type normalization
        instructions, step_log = self._normalize_input(raw_input)
        audit_trail.append(step_log)

        # 2. Dirty data healing and standardization
        standardized_instructions, step_log = self._heal_and_standardize(instructions)
        audit_trail.append(step_log)

        # 3. Deduplication and conflict resolution
        final_instructions, step_log = self._resolve_conflicts(standardized_instructions)
        audit_trail.append(step_log)

        # 4. Generate final prompt
        final_prompt, step_log = self._generate_prompt(final_instructions)
        audit_trail.append(step_log)

        # Frontend gets the clean result, Backend gets full audit trace
        return {
            "success": True,
            "final_prompt": final_prompt,
            "audit_trail": audit_trail,
            "motions": final_instructions
        }

    def _normalize_input(self, raw_input: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        log = {
            "step": "normalize_input",
            "before": raw_input,
            "after": [],
            "reason": "Convert input to standard list of dicts."
        }

        normalized = []
        if raw_input is None:
            log["reason"] = "Input was None, converted to empty list."
        elif isinstance(raw_input, str):
            normalized.append({"motion": raw_input})
        elif isinstance(raw_input, dict):
            normalized.append(raw_input)
        elif isinstance(raw_input, list):
            for item in raw_input:
                if isinstance(item, str):
                    normalized.append({"motion": item})
                elif isinstance(item, dict):
                    normalized.append(item)
                else:
                    # Ignore entirely invalid types within list quietly
                    pass
        else:
            # Fallback for unexpected root types
            log["reason"] = "Input was unrecognized type, converted to empty list."

        log["after"] = copy.deepcopy(normalized)
        return normalized, log

    def _heal_and_standardize(self, instructions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        log = {
            "step": "heal_and_standardize",
            "before": copy.deepcopy(instructions),
            "after": [],
            "reason": "Apply default values, fix typos, map to standard cinematic terms."
        }

        healed = []
        for inst in instructions:
            new_inst = copy.deepcopy(inst)

            # Extract and lower motion
            raw_motion = str(new_inst.get("motion", "")).strip().lower()

            # Heal typos and synonyms
            if not raw_motion or raw_motion == "none":
                new_inst["motion"] = self.DEFAULT_MOTION
            elif raw_motion in self.VALID_MOTIONS:
                new_inst["motion"] = self.VALID_MOTIONS[raw_motion]
            else:
                # Basic fuzzy matching / silent fallback
                matched = False
                for key, val in self.VALID_MOTIONS.items():
                    if key in raw_motion: # Substring match for dirty data like "pn lft" -> doesn't match directly, but "pan left" in "pls pan left" would.
                        new_inst["motion"] = val
                        matched = True
                        break
                if not matched:
                    # If entirely unrecognized, default to static
                    new_inst["motion"] = self.DEFAULT_MOTION

            # Ensure speed exists
            if "speed" not in new_inst or not isinstance(new_inst["speed"], str) or not new_inst["speed"].strip():
                new_inst["speed"] = self.DEFAULT_SPEED
            else:
                new_inst["speed"] = new_inst["speed"].strip().lower()

            healed.append(new_inst)

        log["after"] = copy.deepcopy(healed)
        return healed, log

    def _resolve_conflicts(self, instructions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        log = {
            "step": "resolve_conflicts",
            "before": copy.deepcopy(instructions),
            "after": [],
            "reason": "Deduplicate motions and remove contradictory axis movements."
        }

        # Axes for conflict resolution
        axes = {
            "x": ["pan left", "pan right", "truck left", "truck right"],
            "y": ["tilt up", "tilt down", "pedestal up", "pedestal down"],
            "z": ["dolly in", "dolly out", "zoom in", "zoom out"]
        }

        resolved = []
        seen_axes = {}

        for inst in instructions:
            motion = inst["motion"]
            if motion == self.DEFAULT_MOTION:
                # Skip defaults during conflict resolution unless it's the only one
                continue

            axis_found = None
            for axis, motions in axes.items():
                if motion in motions:
                    axis_found = axis
                    break

            if axis_found:
                if axis_found in seen_axes:
                    # Conflict or duplicate on same axis, keep the first one (silent resolution)
                    continue
                else:
                    seen_axes[axis_found] = motion
                    resolved.append(inst)
            else:
                # Orbit or other non-conflicting motions
                # Avoid exact duplicates
                if not any(r["motion"] == motion for r in resolved):
                    resolved.append(inst)

        # If everything was invalid or conflicting out, or it was just static
        if not resolved and instructions:
             resolved.append({"motion": self.DEFAULT_MOTION, "speed": self.DEFAULT_SPEED})

        log["after"] = copy.deepcopy(resolved)
        return resolved, log

    def _generate_prompt(self, instructions: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        log = {
            "step": "generate_prompt",
            "before": copy.deepcopy(instructions),
            "after": "",
            "reason": "Format into final Veo 3 / Sora 2 cinematic prompt."
        }

        if not instructions:
            final_prompt = "static camera, cinematic shot, highly detailed"
        else:
            parts = []
            for inst in instructions:
                if inst["motion"] == self.DEFAULT_MOTION:
                    parts.append("static camera")
                else:
                    parts.append(f"{inst['speed']} {inst['motion']}")
            final_prompt = ", ".join(parts) + ", cinematic shot, highly detailed"

        log["after"] = final_prompt
        return final_prompt, log
