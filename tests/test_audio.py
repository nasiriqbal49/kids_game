import unittest
from core.events import Event, EventType
from core.event_bus import EventBus
from engine.audio import AudioManager, _generate_synthetic_wav


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestAudioModule(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.cfg = FakeConfig({
            "audio.volume": 70,
            "audio.mute": False,
            "audio.max_volume_cap": 80,
        })
        self.audio = AudioManager(bus=self.bus, cfg=self.cfg)

    def tearDown(self):
        self.audio.close()

    def test_05_01_synthetic_wav_generation(self):
        """UC 05.01 / 05.03: Procedural sound generator creates valid WAV bytes without external files."""
        wav_bytes = _generate_synthetic_wav(freq=440.0, duration=0.1)
        self.assertGreater(len(wav_bytes), 100)
        # Check RIFF header
        self.assertTrue(wav_bytes.startswith(b"RIFF"))

    def test_05_03_missing_sound_handled_gracefully(self):
        """UC 05.03: Requesting a non-existent sound returns False without crashing."""
        played = self.audio.play_sound("non_existent_sound_key")
        self.assertFalse(played)

    def test_05_06_volume_cap_enforced(self):
        """UC 05.06: Master volume is clamped to max_volume_cap."""
        # Volume set to 95%, but cap is 80%
        capped_cfg = FakeConfig({
            "audio.volume": 95,
            "audio.mute": False,
            "audio.max_volume_cap": 80,
        })
        manager = AudioManager(bus=self.bus, cfg=capped_cfg)
        self.assertAlmostEqual(manager.master_volume, 0.80)
        manager.close()

    def test_05_07_low_health_alert_triggers_and_resets(self):
        """UC 05.07: Low health alert state is tied directly to health state."""
        self.assertFalse(self.audio.low_health_alert_active)

        # Health drops low
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 20, "is_low": True}))
        self.assertTrue(self.audio.low_health_alert_active)

        # Health restored
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 80, "is_low": False}))
        self.assertFalse(self.audio.low_health_alert_active)

    def test_05_08_pause_and_resume_channel_state(self):
        """UC 05.08: GAME_PAUSE and GAME_RESUME control audio pause flag."""
        self.assertFalse(self.audio.is_paused)

        self.bus.publish(Event(EventType.GAME_PAUSE, {"reason": "parent_key"}))
        self.assertTrue(self.audio.is_paused)

        self.bus.publish(Event(EventType.GAME_RESUME, {"reason": "parent_key"}))
        self.assertFalse(self.audio.is_paused)


if __name__ == "__main__":
    unittest.main()