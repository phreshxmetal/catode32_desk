"""Vocalizing behavior - pet meows, yowls, or chirps with energy."""

import random
from entities.behaviors.base import BaseBehavior
from ui import draw_bubble


class VocalizingBehavior(BaseBehavior):
    """Pet breaks into an excited vocal outburst.

    Requires high energy and playfulness to trigger, same as zoomies.
    Expresses itself through a speech bubble during the vocalizing phase.
    Can chain back into zoomies or dissolve to idle.

    Phases:
    1. winding_up  - Pet gears up, shifts pose
    2. vocalizing  - Active vocal display with speech bubble
    3. settling    - Calms down after the outburst
    """

    NAME = "vocalizing"

    TRIGGER_STAT = None  # Multi-stat trigger — see can_trigger()
    PRIORITY = 25  # Same as zoomies — idle picks randomly between them

    STAT_EFFECTS = {"energy": -1.0, "playfulness": -1.5}
    COMPLETION_BONUS = {"energy": -5, "playfulness": -8}

    @classmethod
    def can_trigger(cls, context):
        return (getattr(context, 'energy', 0) > 70 and
                getattr(context, 'playfulness', 0) > 70)

    def __init__(self, character):
        super().__init__(character)
        self.windup_duration = 1.0
        self.vocalize_duration = 6.0
        self.settle_duration = 1.5

    def next(self, context):
        if random.random() < 0.2:
            from entities.behaviors.zoomies import ZoomiesBehavior
            return ZoomiesBehavior
        return None  # -> idle

    def start(self, on_complete=None):
        if self._active:
            return
        super().start(on_complete)
        self._phase = "winding_up"
        self._character.set_pose("sitting.forward.neutral")

    def update(self, dt):
        if not self._active:
            return

        self._phase_timer += dt

        if self._phase == "winding_up":
            if self._phase_timer >= self.windup_duration:
                self._phase = "vocalizing"
                self._phase_timer = 0.0
                self._character.set_pose("sitting.forward.happy")

        elif self._phase == "vocalizing":
            self._progress = min(1.0, self._phase_timer / self.vocalize_duration)
            if self._phase_timer >= self.vocalize_duration:
                self._phase = "settling"
                self._phase_timer = 0.0
                self._character.set_pose("sitting.side.neutral")

        elif self._phase == "settling":
            if self._phase_timer >= self.settle_duration:
                self.stop(completed=True)

    def draw(self, renderer, char_x, char_y, mirror=False):
        if self._active and self._phase == "vocalizing":
            draw_bubble(renderer, "exclaim", char_x, char_y, self._progress, mirror)
