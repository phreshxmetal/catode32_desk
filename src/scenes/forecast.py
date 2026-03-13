from scene import Scene
from weather_system import WeatherSystem

_WEATHER_SYSTEM = WeatherSystem()

_HEADER = "Weather Forecast"
_ROW_HEIGHT = 8
_HEADER_Y = 0
_LIST_Y = 10       # First entry row (one gap below header)
_VISIBLE_ROWS = 6  # Rows available below header


def _fmt_duration(minutes):
    """Format duration in minutes to a short display string."""
    if minutes < 60:
        return "~%dm" % minutes
    hours = minutes // 60
    rem = minutes % 60
    if rem >= 30:
        hours += 1
    return "~%dh" % hours


class ForecastScene(Scene):
    """Displays a scrollable 72-hour weather forecast."""

    MODULES_TO_KEEP = ['weather_system']

    def __init__(self, context, renderer, input_handler):
        super().__init__(context, renderer, input_handler)
        self._entries = []   # list of (weather_str, duration_minutes)
        self._scroll = 0     # index of topmost visible entry

    def enter(self):
        self._entries = _WEATHER_SYSTEM.get_forecast(self.context.environment, hours=72)
        self._scroll = 0

    def handle_input(self):
        if self.input.was_just_pressed('up'):
            if self._scroll > 0:
                self._scroll -= 1
        elif self.input.was_just_pressed('down'):
            max_scroll = max(0, len(self._entries) - _VISIBLE_ROWS)
            if self._scroll < max_scroll:
                self._scroll += 1
        elif self.input.was_just_pressed('a') or self.input.was_just_pressed('b'):
            return ('change_scene', 'normal')
        return None

    def draw(self):
        self.renderer.clear()

        # Header
        header_x = (128 - len(_HEADER) * 8) // 2
        self.renderer.draw_text(_HEADER, header_x, _HEADER_Y)

        # Divider
        self.renderer.draw_line(0, _LIST_Y - 1, 127, _LIST_Y - 1)

        # Entries
        visible = self._entries[self._scroll: self._scroll + _VISIBLE_ROWS]
        for i, (weather, duration) in enumerate(visible):
            y = _LIST_Y + i * _ROW_HEIGHT
            is_current = (self._scroll == 0 and i == 0)

            if is_current:
                self.renderer.draw_text(">", 0, y)

            # Weather name (max 8 chars, padded)
            name = weather[:8]
            self.renderer.draw_text(name, 9, y)

            # Duration right-aligned at column 128
            dur_str = _fmt_duration(duration)
            dur_x = 128 - len(dur_str) * 8
            self.renderer.draw_text(dur_str, dur_x, y)

        # Scroll indicators
        if self._scroll > 0:
            self.renderer.draw_text("^", 120, _LIST_Y)
        if self._scroll < len(self._entries) - _VISIBLE_ROWS:
            self.renderer.draw_text("v", 120, _LIST_Y + (_VISIBLE_ROWS - 1) * _ROW_HEIGHT)
