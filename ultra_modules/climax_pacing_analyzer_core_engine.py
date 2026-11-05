import numbers
import math

def analyze_pacing_curve(script_data=None, config=None):
    """
    Analyzes the script pacing curve and applies climax encryption.
    Pure function, highly fault-tolerant, defaults provided for everything.
    """
    # 1. Zero-configuration defaults & missing param fallbacks
    if config is None:
        config = {}
    if not isinstance(config, dict):
        config = {}

    default_config = {
        'min_score': 0.0,
        'max_score': 100.0,
        'climax_boost': 1.5,
        'suspense_drop': 0.8
    }
    for k, v in default_config.items():
        if k not in config or not isinstance(config[k], numbers.Number) or math.isnan(config[k]):
            config[k] = v

    # 2. Silent data repair for script_data
    if script_data is None:
        script_data = []

    # If a dict is passed instead of list, wrap it
    if isinstance(script_data, dict):
        script_data = [script_data]

    # If not a list (e.g. string, int), fallback to empty list
    if not isinstance(script_data, list):
        script_data = []

    repaired_data = []
    for item in script_data:
        if not isinstance(item, dict):
            continue

        score = item.get('emotion_score', 50.0) # default mid score
        if not isinstance(score, numbers.Number) or math.isnan(score):
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = 50.0

        # clamp to boundaries
        min_score = config['min_score']
        max_score = config['max_score']
        score = max(min_score, min(max_score, score))

        new_item = item.copy()
        new_item['emotion_score'] = score
        repaired_data.append(new_item)

    # 3. Algorithm: Identify rhythm stages and encrypt (boost/drop) emotions
    # Stages: repression -> charge -> climax -> suspense
    # Simple logic based on flow:
    # We will compute a running derivative (diff) to classify stages.

    n = len(repaired_data)
    result = []

    for i in range(n):
        current_item = repaired_data[i]
        score = current_item['emotion_score']

        # Determine stage heuristically
        stage = 'repression' # default

        if i > 0:
            prev_score = repaired_data[i-1]['emotion_score']
            diff = score - prev_score

            if score > 80:
                stage = 'climax'
            elif diff > 10:
                stage = 'charge'
            elif diff < -10 and prev_score > 70:
                stage = 'suspense'
            else:
                if score < 40:
                    stage = 'repression'
                else:
                    stage = 'charge' if diff > 0 else 'suspense'

        # If it's the very first item, just guess based on absolute value
        else:
            if score > 80: stage = 'climax'
            elif score < 40: stage = 'repression'
            else: stage = 'charge'

        # 4. Climax Encryption / Boosting
        encrypted_score = score
        if stage == 'climax':
            encrypted_score = score * config['climax_boost']
        elif stage == 'suspense':
            encrypted_score = score * config['suspense_drop']

        # Final clamp after encryption
        encrypted_score = max(config['min_score'], min(config['max_score'], encrypted_score))

        final_item = current_item.copy()
        final_item['rhythm_stage'] = stage
        final_item['encrypted_score'] = encrypted_score

        result.append(final_item)

    return {
        'analyzed_script': result,
        'diagnostics': {
            'total_scenes': len(result),
            'climax_count': sum(1 for x in result if x['rhythm_stage'] == 'climax')
        }
    }
