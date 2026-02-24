"""Pacing behavior - restless back-and-forth when the pet is unsettled."""

import random
from entities.behaviors.base import BaseBehavior


class PacingBehavior(BaseBehavior):
    """Pet burns off restless anxiety by pacing.

    Triggered when at least one core emotional need is low (comfort,
    fulfillment, or affection) and the pet lacks the patience and serenity
    to sit with it. Provides mild comfort relief and channels unspent energy
    into mischievousness.

    After pacing, whether the pet vocalizes or just resigns itself to idle
    depends on personality. An immature and social cat is far more likely
    to demand attention out loud; a mature, independent cat just sulks off.

    Transition probability to vocalizing:
        p = (1 - maturity/100) * (sociability/100)

    Phases:
    1. starting  - Pet gets up, restless energy building
    2. pacing    - Back and forth movement
    3. stopping  - Settles, for now
    """

    NAME = "pacing"

    TRIGGER_STAT = None  # Multi-stat trigger — see can_trigger()
    PRIORITY = 55  # Below stretching (50), above lounging (90)

    STAT_EFFECTS = {
        "comfort": 0.2,
        "mischievousness": 0.3,
    }
    COMPLETION_BONUS = {
        "comfort": 5,
        "mischievousness": 5,
    }

    @classmethod
    def can_trigger(cls, context):
        has_need = (
            getattr(context, 'comfort', 50) < 40 or
            getattr(context, 'fulfillment', 50) < 40 or
            getattr(context, 'affection', 50) < 40
        )
        return (
            has_need and
            getattr(context, 'patience', 50) < 50 and
            getattr(context, 'serenity', 50) < 50
        )

    def __init__(self, character):
        super().__init__(character)
        self.start_duration = 1.0
        self.pace_duration = 10.0
        self.stop_duration = 1.5

    def next(self, context):
        maturity = getattr(context, 'maturity', 50) / 100.0
        sociability = getattr(context, 'sociability', 50) / 100.0
        p_vocalize = (1.0 - maturity) * sociability
        if random.random() < p_vocalize:
            from entities.behaviors.vocalizing import VocalizingBehavior
            return VocalizingBehavior
        return None  # -> idle

    def start(self, on_complete=None):
        if self._active:
            return
        super().start(on_complete)
        self._phase = "starting"
        self._character.set_pose("sitting.side.neutral")

    def update(self, dt):
        if not self._active:
            return

        self._phase_timer += dt

        if self._phase == "starting":
            if self._phase_timer >= self.start_duration:
                self._phase = "pacing"
                self._phase_timer = 0.0
                self._character.set_pose("standing.side.neutral")

        elif self._phase == "pacing":
            self._progress = min(1.0, self._phase_timer / self.pace_duration)
            if self._phase_timer >= self.pace_duration:
                self._phase = "stopping"
                self._phase_timer = 0.0
                self._character.set_pose("sitting.side.aloof")

        elif self._phase == "stopping":
            if self._phase_timer >= self.stop_duration:
                self.stop(completed=True)
