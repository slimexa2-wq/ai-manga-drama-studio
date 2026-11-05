import unittest
import os
import shutil
import json
import csv
from ultra_modules.ego_dual_cloud_dispatcher_cli_one_click import EgoDualCloudDispatcher

class TestEgoDualCloudDispatcherCLIOneClick(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_output_dispatcher"
        self.dispatcher = EgoDualCloudDispatcher(max_workers=2, output_dir=self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_01_normal_execution(self):
        """Test normal execution with standard task format"""
        tasks = [{"text": "Hello world", "type": "scene"}]
        results = self.dispatcher.dispatch_tasks(tasks)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["input"]["text"], "Hello world")
        self.assertEqual(results[0]["input"]["type"], "scene")

        self.assertIn("google_ultra", results[0]["results"])
        self.assertIn("chatgpt_plus", results[0]["results"])

        json_path = self.dispatcher.export_results(results, format_type="json", filename="normal")
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)

    def test_02_dirty_data_self_healing(self):
        """Test handling of invalid schemas, lists of strings, None inputs"""
        dirty_tasks = [
            None,
            "String as task",
            ["List", "as", "task"],
            {"content": "Content instead of text"},
            {"unrelated": "data"}
        ]

        results = self.dispatcher.dispatch_tasks(dirty_tasks)
        self.assertEqual(len(results), 5)

        # Check None fallback
        self.assertEqual(results[0]["input"]["text"], "default_story_content")

        # Check String fallback
        self.assertEqual(results[1]["input"]["text"], "String as task")

        # Check List fallback
        self.assertEqual(results[2]["input"]["text"], "List as task")

        # Check dict missing text fallback
        self.assertEqual(results[3]["input"]["text"], "Content instead of text")

        # Check unrecog dict fallback
        self.assertEqual(results[4]["input"]["text"], "default_story_content")

        # Make sure they all got an auto type
        for res in results:
            self.assertEqual(res["input"]["type"], "auto")

    def test_03_missing_parameter_fallback(self):
        """Test zero-parameter execution one_click_run()"""
        summary = self.dispatcher.one_click_run()
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["results_count"], 3)
        self.assertTrue(os.path.exists(summary["exports"]["json"]))
        self.assertTrue(os.path.exists(summary["exports"]["csv"]))

    def test_04_excel_export_adapter(self):
        """Test Excel/CSV dump correctness"""
        tasks = [{"text": "Export test 1"}, {"text": "Export test 2"}]
        results = self.dispatcher.dispatch_tasks(tasks)

        # Even if format is excel, it should fallback to csv logic for simplicity
        csv_path = self.dispatcher.export_results(results, format_type="excel", filename="export_test")
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(csv_path.endswith(".csv"))

        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 3) # 1 header + 2 data rows
            self.assertEqual(rows[0], ["Task ID", "Input Text", "Google Image URL", "GPT Image URL"])
            self.assertEqual(rows[1][1], "Export test 1")
            self.assertEqual(rows[2][1], "Export test 2")

    def test_05_extreme_boundary_cases(self):
        """Test edge cases: negative workers, single non-list task input"""
        # Test bad worker count falls back to 10
        dispatcher = EgoDualCloudDispatcher(max_workers=-5, output_dir=self.output_dir)
        self.assertEqual(dispatcher.max_workers, 10)

        # Test single non-list task (string)
        results = dispatcher.dispatch_tasks("Just a string task")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["input"]["text"], "Just a string task")

        # Test unrecognized format type defaults to json
        out_path = dispatcher.export_results(results, format_type="unknown_format", filename="unknown")
        self.assertTrue(out_path.endswith(".json"))

        # Test error handling during task dispatching
        # Force a worker to raise an Exception by passing something that breaks _heal_task_data or _process_single_task
        # Since _heal_task_data is very robust, we can mock _mock_dispatch_to_cloud to raise an exception
        original_mock_dispatch = dispatcher._mock_dispatch_to_cloud
        def broken_dispatch(task_id, task, provider):
            raise Exception("Mocked Cloud Error")

        dispatcher._mock_dispatch_to_cloud = broken_dispatch
        results_error = dispatcher.dispatch_tasks(["Task to trigger error"])
        self.assertEqual(len(results_error), 1)
        self.assertEqual(results_error[0]["status"], "error")
        self.assertIn("Mocked Cloud Error", results_error[0]["error_message"])

        # Test exporting when there's an error in results
        csv_path_err = dispatcher.export_results(results_error, format_type="csv", filename="error_export")
        self.assertTrue(os.path.exists(csv_path_err))

        # Restore mock
        dispatcher._mock_dispatch_to_cloud = original_mock_dispatch


        # Test fallback for completely weird type like object
        class WeirdObject:
            def __str__(self):
                return "WeirdObjectString"
        weird_results = dispatcher.dispatch_tasks(WeirdObject())
        self.assertEqual(len(weird_results), 1)
        self.assertEqual(weird_results[0]["input"]["text"], "WeirdObjectString")

    def test_06_main_block(self):
        """Test the main block of the module"""
        import ultra_modules.ego_dual_cloud_dispatcher_cli_one_click as module
        module.run_main()

if __name__ == "__main__":
    unittest.main()
