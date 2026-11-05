import unittest
import time
import copy
from ultra_modules.climax_pacing_analyzer_self_healing_guard import ClimaxPacingAnalyzerSelfHealingGuard

class TestClimaxPacingAnalyzerSelfHealingGuard(unittest.TestCase):

    def setUp(self):
        self.guard = ClimaxPacingAnalyzerSelfHealingGuard()

    def test_normal_flow(self):
        """Test normal pacing data without needing healing."""
        input_data = [
            {"phase": "suppression", "intensity": 20, "duration_sec": 30},
            {"phase": "accumulation", "intensity": 50, "duration_sec": 45},
            {"phase": "payoff", "intensity": 95, "duration_sec": 10},
            {"phase": "suspense", "intensity": 40, "duration_sec": 15}
        ]

        result = self.guard.analyze(input_data)

        self.assertEqual(len(result["healed_pacing"]), 4)
        self.assertEqual(result["healed_pacing"][2]["phase"], "payoff")
        self.assertEqual(result["healed_pacing"][2]["intensity"], 95.0)
        self.assertEqual(result["diagnosis"], "Good climax detected")
        self.assertTrue("signature" in result)

    def test_dirty_data_repair(self):
        """Test self-healing on dirty, malformed data."""
        dirty_data = [
            "this is not a dict",
            {"phase": None, "intensity": "invalid_string", "duration_sec": None},
            {"phase": "accumulation", "intensity": 150.0, "duration_sec": -5} # Out of bounds
        ]

        result = self.guard.analyze(dirty_data)
        healed = result["healed_pacing"]

        self.assertEqual(len(healed), 2)

        # Second item in dirty data
        self.assertEqual(healed[0]["phase"], "suppression")
        self.assertEqual(healed[0]["intensity"], 50.0)
        self.assertEqual(healed[0]["duration_sec"], 10.0)

        # Third item in dirty data
        self.assertEqual(healed[1]["phase"], "accumulation")
        self.assertEqual(healed[1]["intensity"], 100.0) # Capped at 100
        self.assertEqual(healed[1]["duration_sec"], 1.0) # Capped at min 1s

    def test_missing_parameter_defaults(self):
        """Test fallback defaults when parameters are completely missing or input is empty."""
        # Empty input
        result1 = self.guard.analyze(None)
        self.assertEqual(len(result1["healed_pacing"]), 1)
        self.assertEqual(result1["healed_pacing"][0]["phase"], "suppression")

        # Dict missing keys
        result2 = self.guard.analyze([{}])
        self.assertEqual(len(result2["healed_pacing"]), 1)
        self.assertEqual(result2["healed_pacing"][0]["phase"], "suppression")
        self.assertEqual(result2["healed_pacing"][0]["intensity"], 50.0)
        self.assertEqual(result2["healed_pacing"][0]["duration_sec"], 10.0)

    def test_undo_snapshot_success(self):
        """Test restoring the previous snapshot within the 5-second limit."""
        # State 1
        res1 = self.guard.analyze([{"phase": "suppression", "intensity": 20}])
        self.assertEqual(res1["healed_pacing"][0]["intensity"], 20.0)

        # State 2
        res2 = self.guard.analyze([{"phase": "payoff", "intensity": 90}])
        self.assertEqual(res2["healed_pacing"][0]["intensity"], 90.0)

        # Undo back to State 1
        undone = self.guard.undo()
        self.assertEqual(undone["healed_pacing"][0]["intensity"], 20.0)

    def test_undo_snapshot_expiry(self):
        """Test that undo fails silently and does not revert if 5 seconds have passed."""
        # State 1
        self.guard.analyze([{"phase": "suppression", "intensity": 20}])

        # Modify the timestamp of the internal snapshot to simulate time passing
        # Since analyze just happened, it was saved when we do the next analyze
        self.guard.analyze([{"phase": "payoff", "intensity": 90}])

        # Force the timestamp of the snapshot to be old
        self.guard._snapshots[0]["timestamp"] = time.time() - 10

        # Try to undo
        undone = self.guard.undo()

        # Should remain at State 2 (intensity 90)
        self.assertEqual(undone["healed_pacing"][0]["intensity"], 90.0)

if __name__ == '__main__':
    unittest.main()
