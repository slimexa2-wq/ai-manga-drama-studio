import unittest
from ultra_modules.gpt_image_turnaround_sheet_audit_trace import GPTImageTurnaroundSheetGenerator, AuditTraceManager

class TestGPTImageTurnaroundSheetGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = GPTImageTurnaroundSheetGenerator()

    def test_01_normal_execution(self):
        """Test with valid normal inputs."""
        res = self.generator.generate(
            character_name="Alice",
            style_description="cyberpunk, neon lighting",
            angles=["front view", "side view"],
            expressions=["happy", "sad"]
        )
        prompt = res["result"]["prompt"]
        self.assertIn("Alice", prompt)
        self.assertIn("cyberpunk", prompt)
        self.assertIn("front view, side view", prompt)
        self.assertIn("happy, sad", prompt)
        # Check no audit traces since all data was clean and normal
        self.assertEqual(len(res["audit_traces"]), 0)

    def test_02_missing_parameters_default_fallback(self):
        """Test with completely missing (None) parameters to ensure defaults work."""
        res = self.generator.generate(
            character_name=None,
            style_description=None,
            angles=None,
            expressions=None
        )
        prompt = res["result"]["prompt"]
        self.assertIn(GPTImageTurnaroundSheetGenerator.DEFAULT_CHARACTER_NAME, prompt)
        self.assertIn(GPTImageTurnaroundSheetGenerator.DEFAULT_STYLE, prompt)

        # Verify default traces
        traces = res["audit_traces"]
        self.assertTrue(any(t["step"] == "character_name_none_check" for t in traces))
        self.assertTrue(any(t["step"] == "style_description_none_check" for t in traces))

    def test_03_dirty_data_healing(self):
        """Test with dirty data like duplicated lists, empty strings, spaces."""
        res = self.generator.generate(
            character_name="  Bob   ",
            style_description="",
            angles=["front view", " front view ", "side view", ""],
            expressions=["happy", None, "happy"]
        )
        result = res["result"]

        # Check character name healed
        self.assertEqual(result["clean_parameters"]["character_name"], "Bob")

        # Check style healed to default (empty string -> default)
        self.assertEqual(result["clean_parameters"]["style_description"], GPTImageTurnaroundSheetGenerator.DEFAULT_STYLE)

        # Check deduplication and cleaning of lists
        # "" becomes falsey, None becomes string "none" which is kept in expressions if not empty
        self.assertListEqual(result["clean_parameters"]["angles"], ["front view", "side view"])
        self.assertListEqual(result["clean_parameters"]["expressions"], ["happy"])

    def test_04_extreme_edge_cases(self):
        """Test with extreme edge cases like wrong types (int for string, dict for list)."""
        class EmptyStrClass:
            def __str__(self):
                return "   "

        res = self.generator.generate(
            character_name=12345,
            style_description=EmptyStrClass(),
            angles={"front": True}, # Dict instead of list
            expressions=[999, EmptyStrClass(), 999] # list with ints and empty string object
        )
        result = res["result"]

        # Int -> String auto-healing
        self.assertEqual(result["clean_parameters"]["character_name"], "12345")

        # Boolean -> String auto-healing
        self.assertEqual(result["clean_parameters"]["style_description"], GPTImageTurnaroundSheetGenerator.DEFAULT_STYLE)

        # Dict -> Default list (type check fallback)
        self.assertListEqual(result["clean_parameters"]["angles"], GPTImageTurnaroundSheetGenerator.DEFAULT_ANGLES)

        # Check deduplication and cleaning of list with extreme cases
        self.assertListEqual(result["clean_parameters"]["expressions"], ["999"])

        # Ensure audit traces are recorded for all these corrections
        traces = res["audit_traces"]
        self.assertTrue(any(t["step"] == "character_name_type_cast" for t in traces))
        self.assertTrue(any(t["step"] == "angles_type_check" for t in traces))

    def test_05_audit_trace_manager(self):
        """Test the AuditTraceManager independently to ensure clearing and logging."""
        manager = AuditTraceManager()
        manager.log_change("test_step", "orig", "upd", "reason")
        traces = manager.get_traces()
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["step"], "test_step")

        manager.clear()
        self.assertEqual(len(manager.get_traces()), 0)

    def test_06_dirty_data_empty_list_fallback(self):
        """Test empty list and list becoming empty after sanitization."""
        res = self.generator.generate(
            angles=[],
            expressions=["   ", ""]
        )
        result = res["result"]

        self.assertListEqual(result["clean_parameters"]["angles"], GPTImageTurnaroundSheetGenerator.DEFAULT_ANGLES)
        self.assertListEqual(result["clean_parameters"]["expressions"], GPTImageTurnaroundSheetGenerator.DEFAULT_EXPRESSIONS)

if __name__ == '__main__':
    unittest.main()
