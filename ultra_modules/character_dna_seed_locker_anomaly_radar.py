import math
from typing import List, Dict, Any, Union

def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert any value to a float, returning default on failure."""
    if val is None:
        return default
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f_val
    except (ValueError, TypeError):
        return default

def scan_dna_anomalies(dna_records: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Scans a list of character DNA records (e.g. across 100 episodes) for consistency.
    Uses Z-score / IQR principles to flag top anomalies (Top 3% Red, next 7% Yellow, rest Green).

    Zero-friction invocation: missing or None dna_records defaults to an empty scan result.
    Invalid values are auto-healed to 0.0.
    """
    if not dna_records:
        return {
            "status": "success",
            "message": "No data provided, everything looks good.",
            "results": []
        }

    # Auto-heal and normalize data
    cleaned_data = []
    for idx, record in enumerate(dna_records):
        if not isinstance(record, dict):
            record = {}
        # Expecting some continuous metrics to evaluate, like color shifts, prompt deviation scores, etc.
        # We'll use a unified 'deviation_score' for the radar to analyze.
        raw_score = record.get("deviation_score", 0.0)
        score = _safe_float(raw_score)
        cleaned_data.append({
            "id": record.get("id", f"record_{idx}"),
            "episode": record.get("episode", idx + 1),
            "deviation_score": score,
            "original_record": record
        })

    n = len(cleaned_data)

    # If all items are identical or fewer than 2 items, there is no anomaly distribution possible
    scores = [item["deviation_score"] for item in cleaned_data]
    mean = sum(scores) / n
    variance = sum((x - mean) ** 2 for x in scores) / n
    std_dev = math.sqrt(variance)

    # Sort descending by deviation score to find Top 3% and next 7%
    sorted_items = sorted(cleaned_data, key=lambda x: x["deviation_score"], reverse=True)

    top_3_pct_count = max(1, math.ceil(n * 0.03)) if n >= 34 else (1 if n > 0 else 0)
    top_10_pct_count = max(1, math.ceil(n * 0.10)) if n >= 10 else (1 if n > 0 else 0)

    # If std_dev is 0, nothing is an anomaly
    if std_dev == 0.0:
        top_3_pct_count = 0
        top_10_pct_count = 0

    results = []
    for i, item in enumerate(sorted_items):
        marker = "Green"
        reason = "正常"

        if i < top_3_pct_count:
            marker = "Red"
            reason = "严重偏离标准DNA！建议立即人工核查（可能是换脸失败或描述词污染）。"
        elif i < top_10_pct_count:
            marker = "Yellow"
            reason = "轻微偏离标准DNA，可以留意，但不影响大局。"

        # Additional Z-score info for internal debugging/log, though the prompt requires simple explanations
        z_score = (item["deviation_score"] - mean) / std_dev if std_dev > 0 else 0.0

        results.append({
            "id": item["id"],
            "episode": item["episode"],
            "marker": marker,
            "reason": reason,
            "deviation_score": item["deviation_score"],
            "z_score": z_score
        })

    # Restore original order based on episode or ID if possible, but sorting by anomaly is usually better for review
    # We will return them sorted by anomaly severity
    return {
        "status": "success",
        "message": f"Scanned {n} records. Found {top_3_pct_count} red anomalies and {max(0, top_10_pct_count - top_3_pct_count)} yellow warnings.",
        "results": results,
        "metrics": {
            "mean": mean,
            "std_dev": std_dev
        }
    }

if __name__ == '__main__': # pragma: no cover
    # Extremely simple test run for CLI sanity check
    sample_data = [
        {"id": "ep1", "deviation_score": 1.2},
        {"id": "ep2", "deviation_score": 1.5},
        {"id": "ep3", "deviation_score": 9.8}, # Anomaly
        {"id": "ep4", "deviation_score": 1.1},
        {"id": "ep5", "deviation_score": 1.3},
    ] * 20 # 100 records

    print(scan_dna_anomalies(sample_data))
