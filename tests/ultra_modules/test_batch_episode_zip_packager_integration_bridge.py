import unittest
import zipfile
import io
import json
from ultra_modules.batch_episode_zip_packager_integration_bridge import SchemaConverter, BatchEpisodeZipPackager, bridge_and_package

class TestBatchEpisodeZipPackagerIntegrationBridge(unittest.TestCase):

    def test_schema_conversion_normal(self):
        # 1. Normal data test
        raw_data = {
            "settings": {"res": "1920x1080", "frame_rate": "60"},
            "eps": [
                {
                    "episode_id": "ep1",
                    "name": "First Ep",
                    "video_file": "vid1.mp4",
                    "subtitle_file": "sub1.srt",
                    "jianying_draft": {"foo": "bar"},
                    "ai_prompts": {"p1": "v1"}
                }
            ]
        }
        converted = SchemaConverter.convert(raw_data)
        self.assertEqual(converted["version"], "2.0")
        self.assertEqual(converted["global_settings"]["resolution"], "1920x1080")
        self.assertEqual(converted["global_settings"]["fps"], 60)
        self.assertEqual(len(converted["episodes"]), 1)
        ep = converted["episodes"][0]
        self.assertEqual(ep["id"], "ep1")
        self.assertEqual(ep["title"], "First Ep")
        self.assertEqual(ep["mp4_path"], "vid1.mp4")
        self.assertEqual(ep["srt_path"], "sub1.srt")
        self.assertEqual(ep["draft_json"], {"foo": "bar"})
        self.assertEqual(ep["prompts"], {"p1": "v1"})

    def test_schema_conversion_dirty_and_missing(self):
        # 2. Dirty data and missing parameters self-healing
        raw_data = {
            "global_settings": {"fps": "not_an_int"},
            "episodes": [
                "not_a_dict", # should be skipped
                {
                    # missing all keys
                },
                {
                    "id": "123",
                    "draft_json": "not_a_dict",
                    "prompts": "not_a_dict"
                }
            ]
        }
        converted = SchemaConverter.convert(raw_data)
        self.assertEqual(converted["global_settings"]["resolution"], "1080x1920") # default
        self.assertEqual(converted["global_settings"]["fps"], 30) # default fallback for wrong type
        self.assertEqual(len(converted["episodes"]), 2)

        ep1 = converted["episodes"][0]
        self.assertEqual(ep1["id"], "ep_2")
        self.assertEqual(ep1["title"], "Episode ep_2")
        self.assertEqual(ep1["draft_json"], {})

        ep2 = converted["episodes"][1]
        self.assertEqual(ep2["id"], "123")
        self.assertEqual(ep2["draft_json"], {})
        self.assertEqual(ep2["prompts"], {})

    def test_schema_conversion_extreme_boundary(self):
        # 3. Extreme boundary: raw_data is None or list instead of dict, or invalid settings/episodes types
        converted1 = SchemaConverter.convert(None)
        self.assertEqual(converted1["version"], "2.0")
        self.assertEqual(len(converted1["episodes"]), 0)

        converted2 = SchemaConverter.convert({"global_settings": "not_dict", "episodes": "not_list"})
        self.assertEqual(converted2["global_settings"]["fps"], 30)
        self.assertEqual(len(converted2["episodes"]), 0)

    def test_packager_normal_and_deduplication(self):
        # 4. Packaging and deduplication
        raw_data = {
            "episodes": [
                {"id": "ep1", "mp4_path": "exist.mp4", "srt_path": "exist.srt"},
                {"id": "ep1"} # Duplicate ID
            ]
        }

        clean_schema = SchemaConverter.convert(raw_data)
        self.assertEqual(clean_schema["episodes"][1]["id"], "ep1_dedup_1")

        def mock_reader(path):
            if path == "exist.mp4":
                return b"real_mp4"
            elif path == "exist.srt":
                return "real_srt" # testing string auto-encode
            return None

        zip_bytes = BatchEpisodeZipPackager.package_to_memory(clean_schema, mock_reader)

        # Verify ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            files = zf.namelist()
            self.assertIn("schema_manifest.json", files)
            self.assertIn("episode_ep1/video.mp4", files)
            self.assertIn("episode_ep1_dedup_1/video.mp4", files)

            # test mock reader content
            self.assertEqual(zf.read("episode_ep1/video.mp4"), b"real_mp4")
            self.assertEqual(zf.read("episode_ep1/subtitles.srt"), b"real_srt")

            # test dummy fallback content
            self.assertEqual(zf.read("episode_ep1_dedup_1/video.mp4"), b"dummy_mp4_data")
            self.assertIn(b"Dummy Subtitle", zf.read("episode_ep1_dedup_1/subtitles.srt"))

    def test_bridge_one_click(self):
        # 5. One click bridge API test, also test file reading fallback
        raw_data = {"episodes": [{"id": "test_one_click"}]}

        # pass file_reader_callable=lambda x: None to avoid disk IO, but test default logic
        zip_bytes = bridge_and_package(raw_data, file_reader_callable=lambda x: None)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            files = zf.namelist()
            self.assertIn("episode_test_one_click/draft_content.json", files)
            draft_content = json.loads(zf.read("episode_test_one_click/draft_content.json"))
            self.assertTrue(draft_content.get("empty"))

    def test_default_reader_success_and_exception(self):
        # Test default reader exception handling and success
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"real_data")
            tmp_path = tmp.name

        try:
            raw_data = {"episodes": [{"id": "ep1", "mp4_path": "non_existent_file.mp4", "srt_path": tmp_path}]}
            clean_schema = SchemaConverter.convert(raw_data)
            zip_bytes = BatchEpisodeZipPackager.package_to_memory(clean_schema)
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                self.assertEqual(zf.read("episode_ep1/video.mp4"), b"dummy_mp4_data")
                self.assertEqual(zf.read("episode_ep1/subtitles.srt"), b"real_data")
        finally:
            os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
