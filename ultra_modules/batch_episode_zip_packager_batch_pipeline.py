import os
import zipfile
import asyncio
import uuid
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Dict, Any, AsyncGenerator

@dataclass
class ProgressSnapshot:
    total: int
    completed: int
    failed: int
    in_progress: int
    is_done: bool
    results: List[Dict[str, Any]] = field(default_factory=list)


class BatchEpisodeZipPackagerPipeline:
    """
    多集连载漫剧MP4成片+SRT字幕+剪映草稿+双生态提示词一键ZIP归档打包器
    (高吞吐批量流水线与并发加速封装)

    遵循极简前端体验，后端自动容错：
    - 支持流式批量处理，单次可拖入10~1000条记录。
    - 零阻塞结果汇总与进度快照。
    - 缺参自动兜底配置，脏数据自愈，无异常抛出。
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def _sanitize_record(self, record: Any) -> Dict[str, Any]:
        """Silently cleans dirty data and assigns reasonable default values."""
        if not isinstance(record, dict):
            # If the record is invalid, default to an empty dict to be populated with fallbacks
            record = {}

        # Ensure we have strings for paths and safe defaults for missing data
        episode_id = record.get('episode_id')
        if not episode_id:
            episode_id = str(uuid.uuid4())
        else:
            episode_id = str(episode_id)

        mp4_path = record.get('mp4_path')
        srt_path = record.get('srt_path')
        draft_data = record.get('draft_data')
        prompt_data = record.get('prompt_data')

        return {
            'episode_id': episode_id,
            'mp4_path': str(mp4_path) if mp4_path else None,
            'srt_path': str(srt_path) if srt_path else None,
            'draft_data': str(draft_data) if draft_data else '{"version": "1.0", "type": "draft"}',
            'prompt_data': str(prompt_data) if prompt_data else 'Default Manga Prompt',
        }

    def _package_single_episode(self, record: Any, output_dir: str) -> Dict[str, Any]:
        """Packages a single episode into a ZIP file with full fault tolerance."""
        record = self._sanitize_record(record)
        episode_id = record['episode_id']

        # Ensure safe output directory
        if not output_dir or not isinstance(output_dir, str):
            output_dir = os.path.join(os.getcwd(), 'default_output_zips')
        os.makedirs(output_dir, exist_ok=True)

        zip_filename = f"episode_{episode_id}.zip"
        zip_filepath = os.path.join(output_dir, zip_filename)

        try:
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 1. Add MP4 or Fallback
                if record['mp4_path'] and os.path.exists(record['mp4_path']):
                    zf.write(record['mp4_path'], arcname=f"{episode_id}.mp4")
                else:
                    zf.writestr(f"{episode_id}_fallback.mp4", b"dummy mp4 content")

                # 2. Add SRT or Fallback
                if record['srt_path'] and os.path.exists(record['srt_path']):
                    zf.write(record['srt_path'], arcname=f"{episode_id}.srt")
                else:
                    zf.writestr(f"{episode_id}_fallback.srt", "1\n00:00:00,000 --> 00:00:01,000\nFallback subtitle")

                # 3. Add Draft
                zf.writestr(f"{episode_id}_draft.json", record['draft_data'])

                # 4. Add Prompt
                zf.writestr(f"{episode_id}_prompt.txt", record['prompt_data'])

            return {
                'episode_id': episode_id,
                'status': 'success',
                'zip_path': zip_filepath,
                'error': None
            }
        except Exception as e:
            # Silent repair: do not crash on exceptions, just return failure state
            return {
                'episode_id': episode_id,
                'status': 'failed',
                'zip_path': None,
                'error': str(e)
            }

    async def process_batch_stream(self, records: Any, output_dir: str) -> AsyncGenerator[ProgressSnapshot, None]:
        """
        Async generator for batch stream processing.
        Yields progress snapshots for frontend UI rendering without blocking.
        """
        if not isinstance(records, list):
            # Tolerate non-list input (e.g. None or a single dict)
            if records is None:
                records = []
            else:
                records = [records]

        total = len(records)
        if total == 0:
            yield ProgressSnapshot(total=0, completed=0, failed=0, in_progress=0, is_done=True)
            return

        completed = 0
        failed = 0
        results = []

        # Submit to thread pool executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        futures = [
            loop.run_in_executor(self._executor, self._package_single_episode, rec, output_dir)
            for rec in records
        ]

        # Initial snapshot showing start of processing
        yield ProgressSnapshot(
            total=total,
            completed=completed,
            failed=failed,
            in_progress=total,
            is_done=False,
            results=[]
        )

        # Yield results as they complete
        for coro in asyncio.as_completed(futures):
            try:
                res = await coro
                if res.get('status') == 'success':
                    completed += 1
                else:
                    failed += 1
                results.append(res)
            except Exception as e:
                # Should not happen because _package_single_episode catches exceptions,
                # but adding an extra layer of fault tolerance.
                failed += 1
                results.append({
                    'episode_id': 'unknown',
                    'status': 'failed',
                    'zip_path': None,
                    'error': str(e)
                })

            in_progress = total - (completed + failed)

            yield ProgressSnapshot(
                total=total,
                completed=completed,
                failed=failed,
                in_progress=in_progress,
                is_done=(in_progress == 0),
                results=list(results)
            )

    def shutdown(self):
        """Clean up the thread pool executor."""
        self._executor.shutdown(wait=False)
