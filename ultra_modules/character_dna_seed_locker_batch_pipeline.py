import concurrent.futures
import threading
import uuid

class CharacterDnaSeedLockerBatchPipeline:
    """
    全剧角色视觉DNA跨100集硬锁定器（高吞吐批量流水线与并发加速封装）
    """

    DEFAULT_HAIR = "black hair"
    DEFAULT_EYE = "black eyes"
    DEFAULT_CLOTHING = "casual wear"
    DEFAULT_STYLE = "anime style, masterpiece, best quality, ultra-detailed"
    DEFAULT_SEED = 424242

    def __init__(self, max_workers=20):
        self.max_workers = max_workers
        self._jobs = {}
        self._jobs_lock = threading.Lock()

    def _heal_and_lock(self, record):
        """
        极度严密复杂的后台容错处理，同时保证调用侧极简
        脏数据自愈、缺参默认兜底、强制类型转换
        """
        if not isinstance(record, dict):
            record = {}

        locked_dna = {}

        # 1. char_id
        raw_char_id = record.get('char_id')
        if not raw_char_id or not isinstance(raw_char_id, (str, int)) or str(raw_char_id).strip() == "":
            locked_dna['char_id'] = f"char_{uuid.uuid4().hex[:8]}"
        else:
            locked_dna['char_id'] = str(raw_char_id).strip()

        # 2. hair_color
        raw_hair = record.get('hair_color')
        if raw_hair and isinstance(raw_hair, str) and raw_hair.strip():
            locked_dna['hair_color'] = raw_hair.strip()
        else:
            locked_dna['hair_color'] = self.DEFAULT_HAIR

        # 3. eye_color
        raw_eye = record.get('eye_color')
        if raw_eye and isinstance(raw_eye, str) and raw_eye.strip():
            locked_dna['eye_color'] = raw_eye.strip()
        else:
            locked_dna['eye_color'] = self.DEFAULT_EYE

        # 4. clothing
        raw_clothing = record.get('clothing')
        if raw_clothing and isinstance(raw_clothing, str) and raw_clothing.strip():
            locked_dna['clothing'] = raw_clothing.strip()
        else:
            locked_dna['clothing'] = self.DEFAULT_CLOTHING

        # 5. style_suffix
        raw_style = record.get('style_suffix')
        if raw_style and isinstance(raw_style, str) and raw_style.strip():
            locked_dna['style_suffix'] = raw_style.strip()
        else:
            locked_dna['style_suffix'] = self.DEFAULT_STYLE

        # 6. seed (Must be integer for hard locking across 100 episodes)
        raw_seed = record.get('seed')
        try:
            locked_dna['seed'] = int(raw_seed)
        except (ValueError, TypeError):
            locked_dna['seed'] = self.DEFAULT_SEED

        # Construct final locked prompt formula
        locked_dna['locked_prompt'] = (
            f"1girl/1boy, {locked_dna['hair_color']}, {locked_dna['eye_color']}, "
            f"{locked_dna['clothing']}, {locked_dna['style_suffix']}"
        )

        return locked_dna

    def process_batch_sync(self, records):
        """同步批量处理，返回保持顺序的锁定DNA列表"""
        if not isinstance(records, list):
            records = [records]

        results = [None] * len(records)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(self._heal_and_lock, record): i
                for i, record in enumerate(records)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                results[index] = future.result()

        return results

    def submit_batch_async(self, records):
        """零阻塞异步提交，返回 job_id，可用于快照查询"""
        if not isinstance(records, list):
            records = [records]

        job_id = f"job_{uuid.uuid4().hex}"
        total = len(records)

        with self._jobs_lock:
            self._jobs[job_id] = {
                'total': total,
                'completed': 0,
                'status': 'running' if total > 0 else 'completed',
                'results': [None] * total
            }

        if total == 0:
            return job_id

        def _worker():
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_index = {
                    executor.submit(self._heal_and_lock, record): i
                    for i, record in enumerate(records)
                }
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    res = future.result()
                    with self._jobs_lock:
                        self._jobs[job_id]['results'][index] = res
                        self._jobs[job_id]['completed'] += 1
                        if self._jobs[job_id]['completed'] == total:
                            self._jobs[job_id]['status'] = 'completed'

        thread = threading.Thread(target=_worker)
        thread.daemon = True
        thread.start()

        return job_id

    def get_job_snapshot(self, job_id):
        """获取任务进度快照与当前零阻塞结果汇总"""
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            return {
                'job_id': job_id,
                'total': job['total'],
                'completed': job['completed'],
                'progress_pct': (job['completed'] / job['total'] * 100) if job['total'] > 0 else 100.0,
                'status': job['status'],
                'results': list(job['results'])
            }

    def process_stream(self, records):
        """流式处理，处理完一个 yield 一个（不保证原顺序）"""
        if not isinstance(records, list):
            records = [records]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._heal_and_lock, record) for record in records]
            for future in concurrent.futures.as_completed(futures):
                yield future.result()
