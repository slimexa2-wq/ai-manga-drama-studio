import unittest
import zipfile
import io
import json
from ultra_modules.batch_episode_zip_packager_audit_trace import pack_episodes_with_audit

class TestBatchEpisodeZipPackagerAuditTrace(unittest.TestCase):
    def test_normal_execution_with_audit(self):
        """测试正常数据打包，不应有任何回退日志"""
        episodes = [
            {
                "episode_number": 1,
                "title": "Awakening",
                "mp4_content": b"real_mp4_data",
                "srt_content": "1\n00:00:01,000 --> 00:00:02,000\nHello",
                "draft_content": {"version": "2.0"},
                "prompts": "prompt1"
            }
        ]

        zip_bytes, trace = pack_episodes_with_audit(episodes=episodes)
        self.assertIsInstance(zip_bytes, bytes)
        self.assertEqual(len(trace), 0, "Normal data should not trigger any fallback traces")

        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            files = zf.namelist()
            self.assertIn("Ep001_Awakening/video.mp4", files)
            self.assertIn("Ep001_Awakening/subtitles.srt", files)
            self.assertIn("Ep001_Awakening/draft_content.json", files)
            self.assertIn("Ep001_Awakening/prompts.txt", files)
            self.assertEqual(zf.read("Ep001_Awakening/video.mp4"), b"real_mp4_data")

    def test_dirty_data_self_healing_with_audit(self):
        """测试脏数据自愈：非字典、非列表"""
        # 非字典单集
        zip_bytes, trace = pack_episodes_with_audit(episodes="not_a_list")
        self.assertIsInstance(zip_bytes, bytes)
        self.assertTrue(any(t["field"] == "episodes" and t["reason"] == "Episodes is invalid type, fallback to empty list" for t in trace))

        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            self.assertIn("README.md", zf.namelist())

        # 字典被自动转为列表
        zip_bytes2, trace2 = pack_episodes_with_audit(episodes={"episode_number": 1})
        self.assertTrue(any(t["field"] == "episodes" and t["reason"] == "Episodes is dict, wrapping in list" for t in trace2))

        # 测试缺参 None (coverage improvement)
        zip_bytes_none, trace_none = pack_episodes_with_audit(episodes=None)
        self.assertIsInstance(zip_bytes_none, bytes)
        self.assertTrue(any(t["field"] == "episodes" and t["reason"] == "Episodes is None, fallback to empty list" for t in trace_none))

        # Test output_path param (coverage improvement)
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "test.zip")
            res, _ = pack_episodes_with_audit(episodes=[{"title": "File Test"}], output_path=out_file)
            self.assertTrue(res)
            self.assertTrue(os.path.exists(out_file))

        # 列表中有脏数据（非字典）和各类需要纠正的数据以提高覆盖率
        dirty_episodes = [
            "not_a_dict",
            {"title": "   ", "mp4_content": "fake_mp4_string"}, # title empty space, mp4 is string
            {"title": "Valid_Title!?"} # title needs sanitation
        ]
        zip_bytes3, trace3 = pack_episodes_with_audit(episodes=dirty_episodes)
        self.assertTrue(any(t["field"] == "episode_type" and t["reason"] == "Invalid episode type, auto-fallback to empty dict" for t in trace3))
        self.assertTrue(any(t["field"] == "title" and t["reason"] == "Title empty or invalid type, fallback to default" for t in trace3))
        self.assertTrue(any(t["field"] == "mp4_content" and t["reason"] == "Encoded string to bytes" for t in trace3))
        self.assertTrue(any(t["field"] == "title" and t["reason"] == "Sanitized invalid characters from title" for t in trace3))

        with zipfile.ZipFile(io.BytesIO(zip_bytes3), 'r') as zf:
            files = zf.namelist()
            self.assertTrue(any(f.startswith("Ep001_Episode_1/") for f in files))

    def test_missing_parameters_fallback_with_audit(self):
        """测试完全缺参兜底"""
        zip_bytes, trace = pack_episodes_with_audit(episodes=[{}])

        # Check all missing fallbacks are traced
        trace_fields = [t["field"] for t in trace]
        self.assertIn("title", trace_fields)
        self.assertIn("mp4_content", trace_fields)
        self.assertIn("srt_content", trace_fields)
        self.assertIn("draft_content", trace_fields)
        self.assertIn("prompts", trace_fields)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            self.assertEqual(zf.read("Ep001_Episode_1/video.mp4"), b"fake_mp4_header")
            self.assertEqual(zf.read("Ep001_Episode_1/subtitles.srt"), b"1\n00:00:00,000 --> 00:00:05,000\n[Auto-generated Subtitles]")
            draft_content = json.loads(zf.read("Ep001_Episode_1/draft_content.json").decode('utf-8'))
            self.assertEqual(draft_content, {"version": "1.0", "type": "auto-fallback-draft"})

    def test_extreme_boundary_cases_with_audit(self):
        """测试极端边界：异常的集数、异常的标题字符等"""
        episodes = [
            {
                "episode_number": "not_a_number",
                "title": "  !@#$%^&*()_+  ", # 全是非法字符
                "mp4_content": 12345, # 异常类型
                "srt_content": 12345, # 异常类型
                "draft_content": "not_a_dict_or_list",
                "prompts": {"role": "hero"} # Dict should be serialized
            }
        ]
        zip_bytes, trace = pack_episodes_with_audit(episodes=episodes)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            files = zf.namelist()
            self.assertTrue(any(f.startswith("Ep001_Episode_1/") for f in files))
            self.assertEqual(zf.read("Ep001_Episode_1/video.mp4"), b"fake_mp4_header")

        # Verify trace reasons
        trace_reasons = [t["reason"] for t in trace]
        self.assertIn("Invalid episode number type, fallback to index + 1", trace_reasons)
        self.assertIn("Title contains only invalid chars, fallback to default", trace_reasons)
        self.assertIn("Invalid mp4_content type, fallback to empty", trace_reasons)
        self.assertIn("Missing or invalid SRT content, fallback to default", trace_reasons)
        self.assertIn("Missing or invalid draft content, fallback to default JSON", trace_reasons)
        self.assertIn("Serialized dict/list to JSON string", trace_reasons)

    def test_tracer_diff_highlighting(self):
        """Verify the exact structure of diff traces"""
        episodes = [{"episode_number": "NaN"}]
        _, trace = pack_episodes_with_audit(episodes=episodes)

        # Find the episode_number trace
        ep_num_trace = next(t for t in trace if t["field"] == "episode_number")
        self.assertEqual(ep_num_trace["old_value"], "NaN")
        self.assertEqual(ep_num_trace["new_value"], "1")
        self.assertEqual(ep_num_trace["diff_highlight"], "Changed 'episode_number' from 'NaN' to '1'")
        self.assertEqual(ep_num_trace["episode_index"], 0)

if __name__ == '__main__':
    unittest.main()
