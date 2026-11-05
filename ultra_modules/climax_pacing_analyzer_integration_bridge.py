import logging
from typing import Any, Dict, List

# Setup silent audit logging
logger = logging.getLogger("climax_pacing_bridge_audit")
logger.setLevel(logging.INFO)
# Prevent logs from polluting stdout unless specifically configured
logger.propagate = False
if not logger.handlers:
    # Just a dummy handler for audit trace memory
    logger.addHandler(logging.NullHandler())

class ClimaxPacingAnalyzerIntegrationBridge:
    """
    Integration Bridge for Climax Pacing Analyzer.
    Provides automatic cross-system data contract bridging, schema version forward
    compatibility, zero-configuration fault tolerance, and silent dirty data healing.
    """

    def __init__(self):
        self._audit_history: List[str] = []

    def _audit_log(self, message: str) -> None:
        """Silently logs audit information for trace/debugging."""
        logger.info(f"[AUDIT] {message}")
        self._audit_history.append(message)

    def get_audit_history(self) -> List[str]:
        """Returns the audit log history for testing or debugging."""
        return list(self._audit_history)

    def _convert_schema(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps old schema fields to the new v2 schema automatically.
        Old fields: 'curve_detected', 'score_breakdown', 'overall_grade'
        New fields: 'has_curve', 'scores', 'overall_rating'
        """
        self._audit_log("Starting schema conversion.")
        new_data = {}

        # map has_curve
        if "has_curve" in raw_data:
            new_data["has_curve"] = bool(raw_data["has_curve"])
        elif "curve_detected" in raw_data:
            self._audit_log("Mapped 'curve_detected' to 'has_curve'")
            new_data["has_curve"] = bool(raw_data["curve_detected"])
        else:
            new_data["has_curve"] = False

        # map overall_rating
        if "overall_rating" in raw_data:
            new_data["overall_rating"] = str(raw_data["overall_rating"])
        elif "overall_grade" in raw_data:
            self._audit_log("Mapped 'overall_grade' to 'overall_rating'")
            new_data["overall_rating"] = str(raw_data["overall_grade"])
        else:
            new_data["overall_rating"] = "Unknown"

        # map scores
        scores = {}
        if "scores" in raw_data and isinstance(raw_data["scores"], dict):
            raw_scores = raw_data["scores"]
        elif "score_breakdown" in raw_data and isinstance(raw_data["score_breakdown"], dict):
            self._audit_log("Mapped 'score_breakdown' to 'scores'")
            raw_scores = raw_data["score_breakdown"]
        else:
            raw_scores = {}

        # old/new score mapping
        # new: suppression, buildup, payoff, suspense
        # old: repression_count, charge_count, climax_count, suspense_count
        mapping = {
            "suppression": ["suppression", "repression_count"],
            "buildup": ["buildup", "charge_count"],
            "payoff": ["payoff", "climax_count"],
            "suspense": ["suspense", "suspense_count"]
        }

        for new_key, old_keys in mapping.items():
            val = 0
            for old_key in old_keys:
                if old_key in raw_scores:
                    try:
                        val = int(raw_scores[old_key])
                        if old_key != new_key:
                            self._audit_log(f"Mapped score '{old_key}' to '{new_key}'")
                        break
                    except (ValueError, TypeError):
                        pass
            scores[new_key] = val

        new_data["scores"] = scores
        return new_data

    def bridge_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        Main entry point. Takes any raw data, heals it, converts schemas,
        and returns a standardized payload for the backend core engine.
        """
        self._audit_log("Received bridge_data request.")

        # 1. Fault Tolerance and Dirty Data Healing
        if not isinstance(raw_data, dict):
            self._audit_log(f"Dirty data detected: Expected dict, got {type(raw_data).__name__}. Falling back to default.")
            # Default schema
            raw_data = {}

        # 2. Schema version automatic forward compatibility
        standardized_data = self._convert_schema(raw_data)

        # 3. Add any standard wrapper
        final_payload = {
            "version": "v2",
            "analysis": standardized_data,
            "status": "success"
        }

        self._audit_log("Successfully completed bridge_data process.")
        return final_payload

# Global singleton for easy frontend one-click access
_bridge = ClimaxPacingAnalyzerIntegrationBridge()

def process_integration_payload(raw_payload: Any) -> Dict[str, Any]:
    """
    Exposed functional interface for extreme simplicity.
    """
    return _bridge.bridge_data(raw_payload)
