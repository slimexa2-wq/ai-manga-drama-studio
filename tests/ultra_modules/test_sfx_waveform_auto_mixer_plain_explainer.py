import unittest
import json
from ultra_modules.sfx_waveform_auto_mixer_plain_explainer import SFXAutoMixerPlainExplainer

class TestSFXAutoMixerPlainExplainer(unittest.TestCase):
    def test_normal_operation(self):
        data = {
            'track_name': 'Sword Clash',
            'volume_db': -3.5,
            'frequency_hz': 800.0,
            'effect_type': 'Reverb'
        }

        # JSON
        json_card_str = SFXAutoMixerPlainExplainer.generate_json_card(data)
        json_card = json.loads(json_card_str)
        self.assertEqual(json_card['status'], 'success')
        self.assertEqual(json_card['data']['track_name'], 'Sword Clash')
        self.assertEqual(json_card['data']['volume_db'], -3.5)
        self.assertEqual(json_card['data']['frequency_hz'], 800.0)
        self.assertEqual(json_card['data']['effect_type'], 'Reverb')
        self.assertIn("The track 'Sword Clash' is mixed at -3.5 dB", json_card['summary'])

        # Markdown
        md_card = SFXAutoMixerPlainExplainer.generate_markdown_card(data)
        self.assertIn("**Track Name:** Sword Clash", md_card)
        self.assertIn("**Volume:** -3.5 dB", md_card)
        self.assertIn("**Frequency:** 800.0 Hz", md_card)
        self.assertIn("**Effect:** Reverb", md_card)

        # HTML
        html_card = SFXAutoMixerPlainExplainer.generate_html_card(data)
        self.assertIn("<li><strong>Track Name:</strong> Sword Clash</li>", html_card)
        self.assertIn("<li><strong>Volume:</strong> -3.5 dB</li>", html_card)
        self.assertIn("<li><strong>Frequency:</strong> 800.0 Hz</li>", html_card)
        self.assertIn("<li><strong>Effect:</strong> Reverb</li>", html_card)

    def test_missing_parameters_fallback(self):
        data = {}
        json_card_str = SFXAutoMixerPlainExplainer.generate_json_card(data)
        json_card = json.loads(json_card_str)

        self.assertEqual(json_card['data']['track_name'], 'Default SFX Track')
        self.assertEqual(json_card['data']['volume_db'], -12.0)
        self.assertEqual(json_card['data']['frequency_hz'], 440.0)
        self.assertEqual(json_card['data']['effect_type'], 'None')

        md_card = SFXAutoMixerPlainExplainer.generate_markdown_card(data)
        self.assertIn("**Track Name:** Default SFX Track", md_card)

        html_card = SFXAutoMixerPlainExplainer.generate_html_card(None)
        self.assertIn("<li><strong>Track Name:</strong> Default SFX Track</li>", html_card)

    def test_dirty_data_self_healing(self):
        # Invalid types for numerical, strange types for strings
        data = {
            'track_name': 12345,
            'volume_db': 'invalid_float',
            'frequency_hz': [1, 2, 3],
            'effect_type': {'invalid': 'type'}
        }

        json_card_str = SFXAutoMixerPlainExplainer.generate_json_card(data)
        json_card = json.loads(json_card_str)

        self.assertEqual(json_card['data']['track_name'], '12345')
        self.assertEqual(json_card['data']['volume_db'], -12.0) # default fallback for unparseable float
        self.assertEqual(json_card['data']['frequency_hz'], 440.0) # default fallback
        self.assertEqual(json_card['data']['effect_type'], "{'invalid': 'type'}")

    def test_dirty_data_completely_invalid_type(self):
        data = "this is not a dictionary"
        json_card_str = SFXAutoMixerPlainExplainer.generate_json_card(data)
        json_card = json.loads(json_card_str)
        self.assertEqual(json_card['data']['track_name'], 'Default SFX Track')
        self.assertEqual(json_card['data']['volume_db'], -12.0)
        self.assertEqual(json_card['data']['frequency_hz'], 440.0)
        self.assertEqual(json_card['data']['effect_type'], 'None')

    def test_extreme_boundary_conditions(self):
        data = {
            'track_name': '  Bass Drop  ',
            'volume_db': 100.0, # Too high, should cap at 20.0
            'frequency_hz': 50000.0, # Too high, should cap at 20000.0
            'effect_type': '  Distortion  '
        }

        json_card_str = SFXAutoMixerPlainExplainer.generate_json_card(data)
        json_card = json.loads(json_card_str)

        self.assertEqual(json_card['data']['track_name'], 'Bass Drop')
        self.assertEqual(json_card['data']['volume_db'], 20.0)
        self.assertEqual(json_card['data']['frequency_hz'], 20000.0)
        self.assertEqual(json_card['data']['effect_type'], 'Distortion')

        data_low = {
            'volume_db': -200.0, # Too low, should floor at -100.0
            'frequency_hz': 5.0, # Too low, should floor at 20.0
        }
        json_card_str_low = SFXAutoMixerPlainExplainer.generate_json_card(data_low)
        json_card_low = json.loads(json_card_str_low)

        self.assertEqual(json_card_low['data']['volume_db'], -100.0)
        self.assertEqual(json_card_low['data']['frequency_hz'], 20.0)

if __name__ == '__main__':
    unittest.main()
