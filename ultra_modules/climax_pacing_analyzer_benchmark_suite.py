import time
import random
import math
import concurrent.futures
from ultra_modules.climax_pacing_analyzer_core_engine import analyze_pacing_curve

def generate_synthetic_fixtures(size=1000, edge_case_ratio=0.1):
    """
    Generates synthetic script pacing data, injecting dirty data, missing fields,
    and out-of-bound edge cases according to the ratio.
    """
    data = []
    num_edge_cases = int(size * edge_case_ratio)

    # 1. Normal Data Generation
    for _ in range(size - num_edge_cases):
        score = random.uniform(10, 90)
        data.append({
            'emotion_score': score,
            'timestamp': f"2023-10-01T{random.randint(10,23)}:{random.randint(10,59)}:00Z",
            'text': f"Normal dialogue segment {random.randint(1, 1000)}"
        })

    # 2. Edge Case Generation
    for _ in range(num_edge_cases):
        case_type = random.choice([
            'missing_score',
            'nan_score',
            'str_score',
            'out_of_bounds',
            'empty_dict',
            'none_obj',
            'garbled_text',
            'cross_boundary_date'
        ])

        if case_type == 'missing_score':
            data.append({'timestamp': '2024-01-01T00:00:00Z'})
        elif case_type == 'nan_score':
            data.append({'emotion_score': float('nan')})
        elif case_type == 'str_score':
            data.append({'emotion_score': "unparseable_string"})
        elif case_type == 'out_of_bounds':
            data.append({'emotion_score': 9999.99}) # Over the 100 limit
        elif case_type == 'empty_dict':
            data.append({})
        elif case_type == 'none_obj':
            data.append(None)
        elif case_type == 'garbled_text':
            data.append({'emotion_score': 50, 'text': ""})
        elif case_type == 'cross_boundary_date':
            data.append({'emotion_score': 50, 'timestamp': "2023-12-31T23:59:59Z"})

    random.shuffle(data)
    return data

def run_benchmark_suite(data_size=10000, concurrency=100, timeout=10.0, edge_case_ratio=0.1):
    """
    Runs a high-concurrency benchmark on analyze_pacing_curve using synthetic data.
    Ensures zero crashes and logs millisecond-level processing times.
    """
    data = generate_synthetic_fixtures(size=data_size, edge_case_ratio=edge_case_ratio)

    # Split data into chunks for concurrent execution
    chunk_size = max(1, data_size // concurrency)
    chunks = [data[i:i + chunk_size] for i in range(0, data_size, chunk_size)]

    start_time = time.time()
    results = []

    # Run concurrency pipeline
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(analyze_pacing_curve, chunk): chunk for chunk in chunks}

        try:
            for future in concurrent.futures.as_completed(futures, timeout=timeout):
                results.append(future.result())
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Benchmark failed to complete within {timeout} seconds.")

    end_time = time.time()

    total_ms = (end_time - start_time) * 1000.0
    avg_ms = total_ms / len(chunks) if chunks else 0

    return {
        'total_time_ms': total_ms,
        'average_chunk_time_ms': avg_ms,
        'processed_chunks': len(results),
        'status': 'success'
    }
