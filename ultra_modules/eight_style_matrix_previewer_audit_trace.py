import time
import uuid
import copy
from typing import List, Dict, Any, Tuple

# 8大画风定义
STYLES = (
    "修仙",
    "都市逆袭",
    "韩漫财阀",
    "热血少年",
    "中式规则怪谈",
    "赛博朋克",
    "末日废土",
    "欧美超英"
)

def _generate_audit_log(step: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """内部函数：生成审计日志，包含时间戳、唯一标识、步骤和详细信息。"""
    return {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "step": step,
        "details": details
    }

def _normalize_input(input_data: Any) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """清洗、自愈脏数据，缺参自动设合理默认值，并静默记录去重/修复依据。"""
    audit_logs = []

    if not isinstance(input_data, dict):
        base_prompt = str(input_data) if input_data is not None else ""
        normalized = {"base_prompt": base_prompt}
        audit_logs.append(_generate_audit_log("type_fix", {"original_type": str(type(input_data)), "action": "converted to dict"}))
    else:
        normalized = copy.deepcopy(input_data)

    # 缺参默认兜底
    if not normalized.get("base_prompt") or not str(normalized.get("base_prompt")).strip():
        normalized["base_prompt"] = "默认主角"
        audit_logs.append(_generate_audit_log("fallback_default", {"field": "base_prompt", "value": "默认主角"}))

    if not normalized.get("resolution"):
        normalized["resolution"] = "1024x1024"
        audit_logs.append(_generate_audit_log("fallback_default", {"field": "resolution", "value": "1024x1024"}))

    # 去重/修复脏数据，例如处理过多的空格或特殊符号
    original_prompt = str(normalized["base_prompt"])
    cleaned_prompt = " ".join(original_prompt.split())
    if cleaned_prompt != original_prompt:
        normalized["base_prompt"] = cleaned_prompt
        audit_logs.append(_generate_audit_log("deduplication", {
            "field": "base_prompt",
            "action": "removed extra whitespaces",
            "from": original_prompt,
            "to": cleaned_prompt
        }))

    return normalized, audit_logs

def _transform_to_style(base_data: Dict[str, Any], style: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """将基础数据折算为指定画风，返回单项净结果及折算审计日志。"""
    prompt = base_data["base_prompt"]
    resolution = base_data["resolution"]

    style_prompt = f"[{style}风格] {prompt}"

    result = {
        "style": style,
        "prompt": style_prompt,
        "resolution": resolution,
        "preview_url": f"https://mock-image-server.local/preview?style={style}&prompt={prompt}"
    }

    # 记录每一步折算依据与差异高亮对比
    audit_log = _generate_audit_log("style_transformation", {
        "target_style": style,
        "diff_highlights": {
            "added": [f"[{style}风格] "],
            "removed": [],
            "changed": {}
        },
        "base_data": base_data
    })

    return result, audit_log

def process_preview_matrix(input_data: Any) -> Dict[str, Any]:
    """
    核心纯函数：一键同屏对比器入口。
    前端仅需调用此函数，返回清爽的净结果，以及后台静默记录的全链路可追溯审计日志。
    """
    normalized_data, init_logs = _normalize_input(input_data)

    matrix_results = []
    audit_trace = init_logs.copy()

    for style in STYLES:
        result, step_log = _transform_to_style(normalized_data, style)
        matrix_results.append(result)
        audit_trace.append(step_log)

    return {
        "frontend_result": {
            "matrix": matrix_results,
            "base_data": normalized_data
        },
        "_audit_trace": audit_trace
    }

class EightStyleMatrixPreviewer:
    """
    八大画风一键同屏对比器（后台全链路可追溯审计日志与差异高亮对比器）。
    该类为封装的对外接口，无状态。
    """
    @staticmethod
    def generate(input_data: Any) -> Dict[str, Any]:
        """
        生成8大画风的预览矩阵，内部实现为无副作用的纯函数。
        """
        return process_preview_matrix(input_data)
