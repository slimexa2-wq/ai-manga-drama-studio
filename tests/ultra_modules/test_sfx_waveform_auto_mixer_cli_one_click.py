import os
import shutil
import unittest
from unittest.mock import patch
import json

from ultra_modules.sfx_waveform_auto_mixer_cli_one_click import (
    SFXWaveformAutoMixer,
    run_auto_mixer_cli_one_click,
    _safe_str,
    _safe_float,
    _safe_dict,
    _safe_list
)

class TestSFXWaveformAutoMixer(unittest.TestCase):

    def setUp(self):
        self.test_dir = "./test_sfx_output"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_normal_operation(self):
        """Test standard configuration correctly produces mixed audio metadata and waveforms."""
        mixer = SFXWaveformAutoMixer(config={"output_dir": self.test_dir})
        mixer.add_track({"name": "bass1", "type": "bass_drop", "volume": 0.8})
        mixer.add_track({"name": "swoosh1", "type": "swoosh", "volume": 1.0})

        result = mixer.process()
        # Accept fallback_mix if ffmpeg is not installed on system
        self.assertIn(result["status"], ["success", "fallback_mix"])
        self.assertEqual(len(result["generated_files"]), 2)

        # Check files are created
        for f in result["generated_files"]:
            self.assertTrue(os.path.exists(f))

        self.assertIn("ffmpeg", result["mix_command"])
        self.assertIn("-filter_complex amix=inputs=2:duration=longest", result["mix_command"])

    def test_missing_parameters_fallback(self):
        """Test calling without parameters falls back to sensible defaults."""
        mixer = SFXWaveformAutoMixer()
        self.assertEqual(mixer.output_dir, "./sfx_output")
        self.assertEqual(mixer.default_volume, 1.0)
        self.assertEqual(mixer.tracks, [])

        # add_track without params
        mixer.add_track(None)
        self.assertEqual(len(mixer.tracks), 1)
        self.assertEqual(mixer.tracks[0]["name"], "track_0")
        self.assertEqual(mixer.tracks[0]["type"], "bass_drop")
        self.assertEqual(mixer.tracks[0]["volume"], 1.0)

        if os.path.exists("./sfx_output"):
            shutil.rmtree("./sfx_output")

    def test_dirty_data_self_healing(self):
        """Test non-dictionary inputs, invalid lists, and malformed strings are healed."""
        # Config with dirty data
        mixer = SFXWaveformAutoMixer(config={
            "output_dir": 123,
            "default_volume": "not a float",
            "tracks": "not a list"
        })
        self.assertEqual(mixer.output_dir, "123")
        self.assertEqual(mixer.default_volume, 1.0)
        self.assertEqual(mixer.tracks, [])

        # Track with dirty data
        mixer.add_track({
            "name": None,
            "type": 456,
            "volume": None
        })
        self.assertEqual(mixer.tracks[0]["name"], "track_0")
        self.assertEqual(mixer.tracks[0]["type"], "456")
        self.assertEqual(mixer.tracks[0]["volume"], 1.0)

        # Test helper functions directly
        self.assertEqual(_safe_str(None, "default"), "default")

        class MockObj:
            def __str__(self):
                raise Exception("Cannot str")

        self.assertEqual(_safe_str(MockObj(), "fallback"), "fallback")
        self.assertEqual(_safe_float(None, 2.0), 2.0)
        self.assertEqual(_safe_float("invalid", 3.0), 3.0)
        self.assertEqual(_safe_dict(None, {"a": 1}), {"a": 1})
        self.assertEqual(_safe_dict("not dict", {"b": 2}), {"b": 2})
        self.assertEqual(_safe_list(None, [1]), [1])
        self.assertEqual(_safe_list("not list", [2]), [2])

    def test_export_metadata_edge_cases(self):
        """Test edge cases in metadata export."""
        mixer = SFXWaveformAutoMixer(config={"output_dir": self.test_dir})

        # Export as JSON
        json_path = mixer.export_metadata({"key": "val"}, "json")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data, {"key": "val"})

        # Export as CSV
        csv_path = mixer.export_metadata({"col1": 1, "col2": "test"}, "csv")
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, 'r') as f:
            content = f.read()
            self.assertIn("col1,col2", content)
            self.assertIn("1,test", content)

        # Export failure fallback
        with patch('builtins.open', side_effect=Exception("IO Error")):
            result = mixer.export_metadata({"key": "val"}, "json")
            self.assertEqual(result, "")

    def test_extreme_boundary_and_exceptions(self):
        """Test system exception fallback strategies (like file IO errors on synthesis)."""
        # Directory creation failure
        with patch('os.makedirs', side_effect=Exception("Permission Denied")):
            mixer = SFXWaveformAutoMixer(config={"output_dir": "/invalid_dir_no_permission"})
            self.assertEqual(mixer.output_dir, ".") # fallback to current dir

        # File synthesis failure
        mixer = SFXWaveformAutoMixer(config={"output_dir": self.test_dir})
        mixer.add_track({"name": "test_track"})
        with patch('builtins.open', side_effect=Exception("Mock IO Error")):
            result = mixer.process()
            self.assertEqual(result["generated_files"], [])
            self.assertEqual(result["mix_command"], "")

    def test_one_click_cli(self):
        """Test the one-click CLI entry point."""
        # Redirect output and clean up after
        with patch('builtins.print') as mock_print:
            run_auto_mixer_cli_one_click()
            mock_print.assert_called()

        if os.path.exists("./sfx_output"):
            shutil.rmtree("./sfx_output")

if __name__ == '__main__':
    unittest.main()
