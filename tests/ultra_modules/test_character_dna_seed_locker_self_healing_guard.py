import unittest
import time
from unittest.mock import patch
from ultra_modules.character_dna_seed_locker_self_healing_guard import CharacterDnaSeedLockerSelfHealingGuard

class TestCharacterDnaSeedLockerSelfHealingGuard(unittest.TestCase):

    def setUp(self):
        self.locker = CharacterDnaSeedLockerSelfHealingGuard()

    def test_normal_execution(self):
        """Test case 1: Normal standard execution"""
        dna_data = {
            'hair_color': 'blonde',
            'eye_color': 'blue',
            'clothing': 'armor',
            'style_suffix': '3d',
            'seed': 12345
        }

        locked = self.locker.lock_dna('Arthur', dna_data)
        self.assertEqual(locked['hair_color'], 'blonde')
        self.assertEqual(locked['seed'], 12345)

        retrieved = self.locker.get_dna('Arthur')
        self.assertEqual(retrieved, locked)

    def test_dirty_data_self_healing(self):
        """Test case 2: Dirty data self-healing"""
        dirty_dna_data = {
            'hair_color': '  red  ',
            'eye_color': '',  # Empty string should fallback
            'clothing': None, # None should fallback
            'style_suffix': 123, # Should be converted to string
            'seed': 'not_a_number' # Invalid seed should fallback
        }

        # Test with dirty character name
        locked = self.locker.lock_dna('   ', dirty_dna_data)

        self.assertEqual(locked['hair_color'], 'red') # Stripped
        self.assertEqual(locked['eye_color'], 'black') # Fallback to default
        self.assertEqual(locked['clothing'], 'casual') # Fallback to default
        self.assertEqual(locked['style_suffix'], '123') # String converted
        self.assertEqual(locked['seed'], 42) # Fallback to default

        # Character name '   ' should heal to 'UnknownCharacter'
        retrieved = self.locker.get_dna('UnknownCharacter')
        self.assertEqual(retrieved, locked)

    def test_missing_parameter_fallback(self):
        """Test case 3: Missing parameter fallback"""
        # Testing with missing parameters (None for name, missing keys in data)
        partial_dna_data = {
            'hair_color': 'silver'
            # Missing other keys
        }

        locked = self.locker.lock_dna(None, partial_dna_data)

        self.assertEqual(locked['hair_color'], 'silver')
        self.assertEqual(locked['eye_color'], 'black') # Fallback
        self.assertEqual(locked['clothing'], 'casual') # Fallback
        self.assertEqual(locked['style_suffix'], 'anime') # Fallback
        self.assertEqual(locked['seed'], 42) # Fallback

        retrieved = self.locker.get_dna(None)
        self.assertEqual(retrieved, locked)

    def test_extreme_boundary_conditions(self):
        """Test case 4: Extreme boundary conditions"""
        # Passing wrong type entirely for dna_data
        locked1 = self.locker.lock_dna('Hero', "this is not a dict")

        # Should populate with all defaults
        self.assertEqual(locked1['hair_color'], 'black')
        self.assertEqual(locked1['seed'], 42)

        # Calling get_dna on non-existent character
        retrieved_non_existent = self.locker.get_dna('Villain')
        self.assertEqual(retrieved_non_existent['hair_color'], 'black')
        self.assertEqual(retrieved_non_existent['seed'], 42)

        # Un-undoable condition
        self.assertFalse(self.locker.undo('Hero')) # Only 1 state, no snapshot
        self.assertFalse(self.locker.undo('Villain')) # Does not exist

    @patch('time.time')
    def test_snapshot_undo_feature(self, mock_time):
        """Test case 5: Snapshot undo feature"""
        # Set initial time
        mock_time.return_value = 100.0

        # State 1
        self.locker.lock_dna('Mage', {'hair_color': 'blue', 'seed': 100})

        # Advance time a little
        mock_time.return_value = 101.0

        # State 2
        self.locker.lock_dna('Mage', {'hair_color': 'red', 'seed': 200})

        # Check State 2 is active
        current_dna = self.locker.get_dna('Mage')
        self.assertEqual(current_dna['hair_color'], 'red')
        self.assertEqual(current_dna['seed'], 200)

        # Undo within 5 seconds (current time 102.0, state 1 saved at 101.0)
        mock_time.return_value = 102.0
        self.assertTrue(self.locker.undo('Mage'))

        # Check State 1 is restored
        restored_dna = self.locker.get_dna('Mage')
        self.assertEqual(restored_dna['hair_color'], 'blue')
        self.assertEqual(restored_dna['seed'], 100)

        # Lock new state (State 3)
        mock_time.return_value = 110.0
        self.locker.lock_dna('Mage', {'hair_color': 'green', 'seed': 300})

        # Try to undo after 5 seconds
        mock_time.return_value = 116.0 # 6 seconds later
        self.assertFalse(self.locker.undo('Mage')) # Undo fails because > 5 seconds

        # Check State 3 is still active
        final_dna = self.locker.get_dna('Mage')
        self.assertEqual(final_dna['hair_color'], 'green')

if __name__ == '__main__':
    unittest.main()
