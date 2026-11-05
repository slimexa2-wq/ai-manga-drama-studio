import json

class SFXAutoMixerPlainExplainer:
    """
    SFX Waveform Auto Mixer Plain Explainer.
    Synthesizes complex multi-track auto-mixing calculation data into simple UI cards.
    Handles dirty data, extreme boundaries, and missing arguments automatically to ensure zero-configuration fault tolerance.
    """

    @staticmethod
    def _heal_data(data: dict) -> dict:
        if data is None:
            data = {}
        if not isinstance(data, dict):
            try:
                data = dict(data)
            except Exception:
                data = {}

        healed = {}
        # Track Name: Fallback to sensible default
        track_name = data.get('track_name')
        if track_name is None:
            healed['track_name'] = 'Default SFX Track'
        else:
            track_name_str = str(track_name).strip()
            if not track_name_str:
                healed['track_name'] = 'Default SFX Track'
            else:
                healed['track_name'] = track_name_str

        # Volume (dB): Handle string floats, invalid types, extreme values
        try:
            vol = float(data.get('volume_db', -12.0))
            if vol > 20.0: vol = 20.0
            if vol < -100.0: vol = -100.0
            healed['volume_db'] = vol
        except (ValueError, TypeError):
            healed['volume_db'] = -12.0

        # Frequency (Hz): Valid audio frequency ranges
        try:
            freq = float(data.get('frequency_hz', 440.0))
            if freq < 20.0: freq = 20.0
            if freq > 20000.0: freq = 20000.0
            healed['frequency_hz'] = freq
        except (ValueError, TypeError):
            healed['frequency_hz'] = 440.0

        # Effect Type: String parsing
        effect = data.get('effect_type')
        if effect is None:
            healed['effect_type'] = 'None'
        else:
            effect_str = str(effect).strip()
            if not effect_str:
                healed['effect_type'] = 'None'
            else:
                healed['effect_type'] = effect_str

        return healed

    @classmethod
    def generate_json_card(cls, calculation_data: dict) -> str:
        """Generates a JSON string representing the simplified explainer card."""
        healed = cls._heal_data(calculation_data)
        summary = (
            f"The track '{healed['track_name']}' is mixed at {healed['volume_db']:.1f} dB "
            f"with a base frequency of {healed['frequency_hz']:.1f} Hz. "
            f"Applied effect: {healed['effect_type']}."
        )
        return json.dumps({"status": "success", "data": healed, "summary": summary})

    @classmethod
    def generate_markdown_card(cls, calculation_data: dict) -> str:
        """Generates a Markdown string representing the simplified explainer card."""
        healed = cls._heal_data(calculation_data)
        summary = (
            f"The track '{healed['track_name']}' is mixed at {healed['volume_db']:.1f} dB "
            f"with a base frequency of {healed['frequency_hz']:.1f} Hz. "
            f"Applied effect: {healed['effect_type']}."
        )
        return f"""# SFX Auto Mixer Summary

**Track Name:** {healed['track_name']}
**Volume:** {healed['volume_db']:.1f} dB
**Frequency:** {healed['frequency_hz']:.1f} Hz
**Effect:** {healed['effect_type']}

> {summary}"""

    @classmethod
    def generate_html_card(cls, calculation_data: dict) -> str:
        """Generates an HTML string representing the simplified explainer card."""
        healed = cls._heal_data(calculation_data)
        summary = (
            f"The track '{healed['track_name']}' is mixed at {healed['volume_db']:.1f} dB "
            f"with a base frequency of {healed['frequency_hz']:.1f} Hz. "
            f"Applied effect: {healed['effect_type']}."
        )
        return f"""<div class="sfx-card">
    <h2>SFX Auto Mixer Summary</h2>
    <ul>
        <li><strong>Track Name:</strong> {healed['track_name']}</li>
        <li><strong>Volume:</strong> {healed['volume_db']:.1f} dB</li>
        <li><strong>Frequency:</strong> {healed['frequency_hz']:.1f} Hz</li>
        <li><strong>Effect:</strong> {healed['effect_type']}</li>
    </ul>
    <p>{summary}</p>
</div>"""
