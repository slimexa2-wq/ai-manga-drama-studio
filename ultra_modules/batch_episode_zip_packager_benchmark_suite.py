import io
import zipfile
import uuid
import datetime
from concurrent.futures import ThreadPoolExecutor

class BatchEpisodeZipPackager:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or "/tmp/ai_manga_drama_studio_exports"

    def sanitize_string(self, text, default_val="default"):
        if text is None:
            return default_val
        if not isinstance(text, str):
            text = str(text)

        clean_text = "".join(c for c in text if c.isprintable())
        return clean_text.strip() or default_val

    def generate_synthetic_fixtures(self, num_episodes=None, cross_year_month=None, dirty_data=None):
        """
        Generate synthetic fixtures (episodes) for benchmarking.
        """
        if num_episodes is None or not isinstance(num_episodes, int) or num_episodes <= 0:
            num_episodes = 10

        episodes = []
        for i in range(num_episodes):
            ep_name = f"Episode_{i+1}"

            if dirty_data:
                if i % 4 == 0:
                    ep_name = None
                elif i % 4 == 1:
                    ep_name = "Episode_!@#$%^&*()_\x00\x01\x02\n\t"
                elif i % 4 == 2:
                    ep_name = ""
                elif i % 4 == 3:
                    ep_name = 12345 # Not a string

            if cross_year_month:
                timestamp = datetime.datetime(2023, 12, 31, 23, 59, 59) + datetime.timedelta(seconds=i)
            else:
                timestamp = datetime.datetime.now()

            episodes.append({
                "title": ep_name,
                "mp4_content": b"mock_mp4_content",
                "srt_content": b"mock_srt_content",
                "draft_content": b"mock_draft_content",
                "prompt_content": b"mock_prompt_content",
                "timestamp": timestamp
            })
        return episodes

    def package_episodes(self, episodes=None, concurrency=None):
        """
        Package multiple episodes into a single ZIP archive in memory,
        returning the ZIP byte content.
        """
        if episodes is None or not isinstance(episodes, list):
            episodes = self.generate_synthetic_fixtures(num_episodes=1)

        if not isinstance(concurrency, int) or concurrency <= 0:
            concurrency = min(32, max(4, len(episodes)))

        zip_buffer = io.BytesIO()

        def prepare_episode(ep):
            try:
                if ep is None or not isinstance(ep, dict):
                    ep = {}

                title_raw = ep.get("title")
                title = self.sanitize_string(title_raw, default_val=f"Untitled_{uuid.uuid4().hex[:8]}")

                timestamp = ep.get("timestamp")
                if not isinstance(timestamp, datetime.datetime):
                    timestamp = datetime.datetime.now()
                ts_str = timestamp.strftime("%Y%m%d_%H%M%S")

                prefix = f"{title}_{ts_str}"

                mp4 = ep.get("mp4_content")
                if not isinstance(mp4, bytes): mp4 = b""

                srt = ep.get("srt_content")
                if not isinstance(srt, bytes): srt = b""

                draft = ep.get("draft_content")
                if not isinstance(draft, bytes): draft = b"{}"

                prompt = ep.get("prompt_content")
                if not isinstance(prompt, bytes): prompt = b""

                return [
                    (f"{prefix}/{title}.mp4", mp4),
                    (f"{prefix}/{title}.srt", srt),
                    (f"{prefix}/draft_content.json", draft),
                    (f"{prefix}/prompts.txt", prompt)
                ]
            except Exception:
                fallback_name = f"Fallback_{uuid.uuid4().hex[:8]}"
                return [(f"{fallback_name}/error.log", b"Error preparing episode.")]

        prepared_files = []
        if concurrency > 1 and len(episodes) > 1:
            try:
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    results = executor.map(prepare_episode, episodes)
                    for res in results:
                        prepared_files.extend(res)
            except Exception:
                # Fallback to sequential if threading fails
                for ep in episodes:
                    prepared_files.extend(prepare_episode(ep))
        else:
            for ep in episodes:
                prepared_files.extend(prepare_episode(ep))

        try:
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path, content in prepared_files:
                    safe_path = "".join(c for c in file_path if c.isprintable() and c not in '\\:*?"<>|')
                    if not safe_path:
                        safe_path = f"Unknown_{uuid.uuid4().hex[:8]}"
                    zip_file.writestr(safe_path, content)
        except Exception:
            return b""

        return zip_buffer.getvalue()

class BenchmarkSuite:
    def __init__(self):
        self.packager = BatchEpisodeZipPackager()

    def run_benchmark(self):
        start_time = datetime.datetime.now()

        # Test large concurrency
        episodes = self.packager.generate_synthetic_fixtures(num_episodes=1000, cross_year_month=True, dirty_data=True)
        zip_bytes = self.packager.package_episodes(episodes=episodes, concurrency=100)

        end_time = datetime.datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "episodes_processed": len(episodes),
            "zip_size_bytes": len(zip_bytes),
            "duration_ms": duration_ms
        }
