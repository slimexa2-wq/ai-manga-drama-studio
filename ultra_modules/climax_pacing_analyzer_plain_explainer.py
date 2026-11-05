import json
from typing import Dict, Any

class ClimaxPacingAnalyzerPlainExplainer:
    """
    Translates complex pacing analysis results into plain, easy-to-understand language.
    Features extreme zero-config fault tolerance and dirty data self-healing.
    """
    def __init__(self):
        # Default analysis template for missing or totally corrupted data
        self._default_analysis = {
            "has_curve": False,
            "overall_rating": "Unknown",
            "scores": {
                "suppression": 0,
                "buildup": 0,
                "payoff": 0,
                "suspense": 0
            }
        }

    def _heal_data(self, data: Any) -> Dict[str, Any]:
        """Silently heal dirty data and ensure a valid dict structure."""
        if not isinstance(data, dict):
            # If it's completely wrong type, return default structure
            return self._default_analysis.copy()

        # If it's a dict, we need to ensure it has the expected nested structure.
        # Sometimes the 'analysis' key is passed directly, sometimes it's wrapped in another dict.
        analysis_data = data.get("analysis", data)
        if not isinstance(analysis_data, dict):
            analysis_data = {}

        healed = {
            "has_curve": bool(analysis_data.get("has_curve", False)),
            "overall_rating": str(analysis_data.get("overall_rating", "Needs Improvement")),
            "scores": {
                "suppression": 0,
                "buildup": 0,
                "payoff": 0,
                "suspense": 0
            }
        }

        scores_data = analysis_data.get("scores", {})
        if isinstance(scores_data, dict):
            for key in healed["scores"]:
                try:
                    val = scores_data.get(key, 0)
                    healed["scores"][key] = int(val) if val is not None else 0
                except (ValueError, TypeError):
                    pass # Silent fallback to 0

        return healed

    def _generate_plain_text(self, healed_data: Dict[str, Any]) -> str:
        """Generate the plain language summary based on healed data."""
        scores = healed_data["scores"]

        text_parts = []

        # Overall vibe
        if healed_data["has_curve"]:
            text_parts.append("📈 **整体节奏很好，有明显的起伏。**")
        else:
            text_parts.append("📉 **节奏有些平缓，建议增加冲突和反转。**")

        # Suppression (压抑)
        if scores["suppression"] > 0:
            text_parts.append(f"😖 前期有 {scores['suppression']} 处压抑情节，主角受尽委屈，仇恨值拉满。")
        else:
            text_parts.append("🤔 前期缺乏压抑，主角没受啥委屈，可能导致后面打脸不够爽。")

        # Buildup (蓄力)
        if scores["buildup"] > 0:
            text_parts.append(f"⏳ 中间有 {scores['buildup']} 处蓄力情节，主角在暗中默默变强。")

        # Payoff (爆发打脸)
        if scores["payoff"] > 0:
            text_parts.append(f"💥 高潮有 {scores['payoff']} 处爆发打脸，瞬间爽文即视感，非常解压！")
        else:
            text_parts.append("💤 缺少爆发打脸情节，高潮不够劲爆，读者可能会觉得憋屈。")

        # Suspense (悬念)
        if scores["suspense"] > 0:
            text_parts.append(f"❓ 结尾留了 {scores['suspense']} 处悬念，很抓人，读者会忍不住看下一集。")
        else:
            text_parts.append("🛑 结尾没有明显悬念，容易让人看完就走。")

        return "\n".join(text_parts)

    def explain(self, raw_result: Any) -> Dict[str, Any]:
        """
        Main entry point for generating the plain language explanation.
        Always returns a valid dictionary.
        """
        healed_data = self._heal_data(raw_result)
        plain_text = self._generate_plain_text(healed_data)

        html_output = f"<div class='pacing-card'>{'<br>'.join(plain_text.split(chr(10)))}</div>"

        return {
            "markdown": plain_text,
            "html": html_output,
            "json": {
                "summary": plain_text,
                "is_good": healed_data["has_curve"],
                "rating": healed_data["overall_rating"]
            }
        }

# Global singleton for one-click simplicity
_explainer = ClimaxPacingAnalyzerPlainExplainer()

def generate_plain_explanation(analysis_result: Any) -> Dict[str, Any]:
    """
    Frontend one-click entry point. Extremely simple to use.
    Just pass whatever you have, and it will return a formatted explanation.
    """
    return _explainer.explain(analysis_result)
