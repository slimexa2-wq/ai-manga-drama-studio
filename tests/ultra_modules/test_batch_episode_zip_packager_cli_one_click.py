import unittest
import os
import zipfile
import tempfile
import json
import argparse
from unittest.mock import patch, mock_open
from ultra_modules.batch_episode_zip_packager_cli_one_click import package_episodes, _heal_input_data, main

class TestBatchEpisodeZipPackager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_zip = os.path.join(self.test_dir, "test_output.zip")

    def tearDown(self):
        if os.path.exists(self.output_zip):
            os.remove(self.output_zip)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def _verify_zip_contents(self, zip_path, expected_episode_count):
        self.assertTrue(os.path.exists(zip_path))
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            namelist = zipf.namelist()
            for i in range(1, expected_episode_count + 1):
                ep_dir = f"Episode_{i:03d}/"
                self.assertIn(f"{ep_dir}video.mp4", namelist)
                self.assertIn(f"{ep_dir}subtitles.srt", namelist)
                self.assertIn(f"{ep_dir}draft_content.json", namelist)
                self.assertIn(f"{ep_dir}prompts.txt", namelist)

    def test_1_normal_execution(self):
        """Test with a normal list of dictionaries."""
        input_data = [
            {"episode": 1, "title": "Ep 1", "content": "Content 1"},
            {"episode": 2, "title": "Ep 2", "content": "Content 2"}
        ]
        result_path = package_episodes(input_data, self.output_zip)
        self.assertEqual(result_path, self.output_zip)
        self._verify_zip_contents(result_path, 2)

    def test_2_zero_parameter_execution(self):
        """Test with absolutely no parameters."""
        result_path = package_episodes()
        self.assertTrue(os.path.exists(result_path))
        self._verify_zip_contents(result_path, 1)
        os.remove(result_path)

    def test_3_dirty_data_self_healing_json_string(self):
        """Test healing of a JSON string."""
        input_data = '[{"episode": 1, "title": "Ep 1"}, {"content": "Missing Title and Ep"}]'
        result_path = package_episodes(input_data, self.output_zip)
        self._verify_zip_contents(result_path, 2)

        # Verify specific healed content
        with zipfile.ZipFile(result_path, 'r') as zipf:
            srt_content = zipf.read("Episode_002/subtitles.srt").decode('utf-8')
            self.assertIn("Episode 2", srt_content) # Auto-generated title
            self.assertIn("Missing Title and Ep", srt_content)

    def test_4_dirty_data_self_healing_broken_json(self):
        """Test healing of a broken JSON string."""
        input_data = '[{"episode": 1, "title": "Ep 1"' # Broken JSON
        result_path = package_episodes(input_data, self.output_zip)
        self._verify_zip_contents(result_path, 1)

    def test_5_dirty_data_self_healing_mixed_list(self):
        """Test healing of a list with mixed types."""
        input_data = [{"episode": 1}, "Just a string", 123]
        result_path = package_episodes(input_data, self.output_zip)
        self._verify_zip_contents(result_path, 3)

    def test_6_file_input_json(self):
        """Test reading from a JSON file."""
        json_file_path = os.path.join(self.test_dir, "input.json")
        with open(json_file_path, "w") as f:
            json.dump([{"episode": 1, "title": "File Title"}], f)

        result_path = package_episodes(json_file_path, self.output_zip)
        self._verify_zip_contents(result_path, 1)
        os.remove(json_file_path)

    def test_7_file_input_mock_excel(self):
        """Test reading from a mock Excel file."""
        excel_file_path = os.path.join(self.test_dir, "input.xlsx")
        # Create empty file
        open(excel_file_path, "w").close()

        result_path = package_episodes(excel_file_path, self.output_zip)
        self._verify_zip_contents(result_path, 1)
        os.remove(excel_file_path)

    def test_8_extreme_boundary_cases(self):
        """Test with extreme boundaries like empty string, None, int."""
        cases = ["", None, 12345, {}, []]
        for idx, case in enumerate(cases):
            output = os.path.join(self.test_dir, f"out_{idx}.zip")
            result_path = package_episodes(case, output)
            self._verify_zip_contents(result_path, 1)
            os.remove(result_path)

    def test_9_exception_handling_in_zip(self):
        """Test fallback when zip creation fails (e.g., bad path permission)."""
        # A directory path instead of a file path will cause an IsADirectoryError or PermissionError
        bad_path = self.test_dir
        result_path = package_episodes(None, bad_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertNotEqual(result_path, bad_path)

        with zipfile.ZipFile(result_path, 'r') as zipf:
             self.assertIn("error.txt", zipf.namelist())
        os.remove(result_path)

    def test_10_json_string_dict(self):
        """Test JSON string that represents a single dict."""
        input_data = '{"episode": 1, "title": "Dict Title"}'
        result = _heal_input_data(input_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], "Dict Title")

    def test_11_json_string_with_non_dict(self):
        """Test JSON string list with non-dict elements."""
        input_data = '["string1", "string2"]'
        result = _heal_input_data(input_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['episode'], 1)
        self.assertEqual(result[1]['episode'], 2)

    def test_12_cli_main(self):
        """Test CLI main function."""
        with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(input=None, output=self.output_zip)):
            with patch('builtins.print') as mock_print:
                main()
                mock_print.assert_called_with(f"Successfully packaged to: {self.output_zip}")
                self._verify_zip_contents(self.output_zip, 1)

    def test_13_file_input_json_broken_read(self):
        """Test reading from a JSON file but reading fails."""
        json_file_path = os.path.join(self.test_dir, "input_broken.json")
        with open(json_file_path, "w") as f:
            f.write("Broken File Content")

        # We need to simulate a read error, or json decoding error.
        # The code catches all exceptions on file read/heal.
        # Let's mock open to raise Exception
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = Exception("Mocked read error")
            result = _heal_input_data(json_file_path)
            self.assertEqual(result[0]['title'], "Auto Generated Episode")
        os.remove(json_file_path)

if __name__ == '__main__':
    unittest.main()
