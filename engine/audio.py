import io
import math
import wave
import struct
import pygame
from typing import Dict, Any, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("audio")


def _generate_synthetic_wav(freq: float, duration: float, volume: float = 0.5, wave_type: str = "sine") -> bytes:
    """Generates an in-memory WAV byte stream so sound works without external asset files (UC 05.03)."""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()

    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)

        frames = []
        for i in range(n_samples):
            t = float(i) / sample_rate
            # Volume envelope (decay)
            env = max(0.0, 1.0 - (t / duration))

            if wave_type == "sine":
                val = math.sin(2.0 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
            else:
                val = math.sin(2.0 * math.pi * freq * t)

            sample = int(val * env * volume * 32767.0)
            sample = max(-32768, min(32767, sample))
            frames.append(struct.pack("<h", sample))

        wf.writeframes(b"".join(frames))

    return buf.getvalue()


class AudioManager:
    """
    Manages sound effects, volume constraints, and audio channel states
    driven by Event Bus events (Module 5).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        self.audio_available: bool = False
        self.sounds: Dict[str, Any] = {}
        self.is_paused: bool = False
        self.low_health_alert_active: bool = False
        
        self.priority_channel = None 
        self.loop_channel = None

        # Volume settings (UC 05.06)
        self.master_volume: float = 0.8
        self.volume_cap: float = 1.0
        self.is_muted: bool = False

        # Preload and configure
        self._init_mixer()
        self._load_sounds()
        self._subscribe_events()

    def _init_mixer(self) -> None:
        """Initializes Pygame mixer with fallback resilience if no audio device exists (UC 05.04)."""
        try:
            if not pygame.mixer.get_init():
                # 22050 Hz, 16-bit, 2 channels, 512 buffer (low latency - UC 05.01)
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_available = True
            # Allocate 8 mixer channels and reserve channel 0 for high-priority effects (UC 05.02)
            pygame.mixer.set_num_channels(8)
            self.priority_channel = pygame.mixer.Channel(0)
            self.loop_channel = pygame.mixer.Channel(1)
            log.info("Audio system initialized successfully. (UC 05.01, 05.04)")
        except Exception as err:
            self.audio_available = False
            log.warning("Audio device unavailable (%s). Running in silent mode. (UC 05.04)", err)

        self._refresh_volume_from_config()

    def _refresh_volume_from_config(self) -> None:
        """Enforces volume cap and mute status from config (UC 05.06)."""
        vol = self.config.get("audio.volume", 80) / 100.0
        cap = self.config.get("audio.max_volume_cap", 100) / 100.0
        self.is_muted = self.config.get("audio.mute", False)

        # Enforce volume cap
        self.volume_cap = max(0.0, min(1.0, cap))
        self.master_volume = min(vol, self.volume_cap)

        if self.audio_available:
            effective = 0.0 if self.is_muted else self.master_volume
            # Update volume across all sounds
            for sound in self.sounds.values():
                if hasattr(sound, "set_volume"):
                    sound.set_volume(effective)

    def _load_sounds(self) -> None:
        """Preloads sound effects into memory (UC 05.01, 05.03)."""
        if not self.audio_available:
            return

        # Procedural synth definitions for out-of-the-box sounds:
        synth_defs = {
            "jump": (440.0, 0.18, 0.6, "sine"),           # Pitch whoop
            "hit": (120.0, 0.25, 0.8, "square"),          # Low thud (high priority)
            "game_over": (150.0, 0.50, 0.9, "square"),    # Game over crash (high priority)
            "powerup": (880.0, 0.30, 0.6, "sine"),        # Bright chime
            "countdown": (600.0, 0.10, 0.5, "sine"),      # Short beep
            "low_health": (300.0, 0.20, 0.7, "square"),   # Warning buzzer
            "running_loop": (200.0, 0.40, 0.3, "sine"),   # Background ambient loop (UC 05.05)
        }

        for name, (freq, duration, vol, wtype) in synth_defs.items():
            try:
                wav_data = _generate_synthetic_wav(freq, duration, vol, wtype)
                sound = pygame.mixer.Sound(io.BytesIO(wav_data))
                sound.set_volume(0.0 if self.is_muted else self.master_volume)
                self.sounds[name] = sound
            except Exception as err:
                log.warning("Could not create sound '%s': %s (UC 05.03)", name, err)

    def _subscribe_events(self) -> None:
        """Map Event Bus signals to sounds (UC 05.01, 05.07, 05.08)."""
        self.bus.subscribe(EventType.JUMP, lambda e: self.play_sound("jump"))
        self.bus.subscribe(EventType.OBSTACLE_HIT, lambda e: self.play_sound("hit"))
        self.bus.subscribe(EventType.POWERUP_COLLECTED, lambda e: self.play_sound("powerup"))
        self.bus.subscribe(EventType.COUNTDOWN_TICK, lambda e: self.play_sound("countdown"))
        self.bus.subscribe(EventType.HEALTH_CHANGED, self._on_health_changed)
        self.bus.subscribe(EventType.GAME_PAUSE, self._on_pause)
        self.bus.subscribe(EventType.GAME_RESUME, self._on_resume)
        self.bus.subscribe(EventType.GAME_OVER, lambda e: self.play_sound("game_over", priority=True))
        self.bus.subscribe(EventType.STATE_CHANGED, self._on_state_changed)

    # -------------------------------------------------------------------------
    # Playback & Event Controls
    # -------------------------------------------------------------------------

    def play_sound(self, sound_name: str, priority: bool = False) -> bool:
        """
        Plays a sound. High-priority sounds (hit, game over) play on a reserved
        channel so they are never interrupted or cut off (UC 05.02).
        """
        if not self.audio_available or self.is_muted or self.is_paused:
            return False

        sound = self.sounds.get(sound_name)
        if sound is not None:
            try:
                if priority and self.priority_channel:
                    self.priority_channel.play(sound)
                else:
                    sound.play()
                return True
            except Exception as err:
                log.error("Failed to play sound '%s': %s", sound_name, err)
        return False

    def _on_state_changed(self, event: Event) -> None:
        """Controls looping background running sounds on state transitions (UC 05.05)."""
        new_state = event.payload.get("new_state", "MENU")
        if new_state == "PLAYING":
            self.start_loop("running_loop")
        else:
            self.stop_loop()

    def start_loop(self, sound_name: str) -> bool:
        """Starts a looping background sound on the dedicated loop channel (UC 05.05)."""
        if not self.audio_available or self.is_muted or self.is_paused:
            return False

        sound = self.sounds.get(sound_name)
        if sound is not None and self.loop_channel:
            try:
                self.loop_channel.play(sound, loops=-1)
                return True
            except Exception as err:
                log.error("Failed to start loop '%s': %s", sound_name, err)
        return False

    def stop_loop(self) -> None:
        """Stops the active looping sound cleanly (UC 05.05)."""
        if self.audio_available and self.loop_channel:
            self.loop_channel.stop()

    def _on_health_changed(self, event: Event) -> None:
        """Ties low-health alert state directly to health metric (UC 05.07)."""
        is_low = event.payload.get("is_low", False)
        if is_low and not self.low_health_alert_active:
            self.low_health_alert_active = True
            self.play_sound("low_health")
        elif not is_low and self.low_health_alert_active:
            self.low_health_alert_active = False

    def _on_pause(self, event: Event) -> None:
        """Pauses all sound channels (UC 05.08)."""
        self.is_paused = True
        if self.audio_available:
            pygame.mixer.pause()

    def _on_resume(self, event: Event) -> None:
        """Resumes active sound channels (UC 05.08)."""
        self.is_paused = False
        if self.audio_available:
            pygame.mixer.unpause()

    def close(self) -> None:
        """Stops and quits the mixer."""
        if self.audio_available and pygame.mixer.get_init():
            pygame.mixer.stop()
            pygame.mixer.quit()
            self.audio_available = False