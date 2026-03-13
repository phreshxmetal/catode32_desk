# weather_system.py - Deterministic weather progression via seeded Markov chain


def _xorshift32(x):
    """Simple xorshift PRNG for deterministic pseudo-random values"""
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= (x >> 17)
    x ^= (x << 5) & 0xFFFFFFFF
    return x & 0xFFFFFFFF


def _seeded_rand(step):
    """Mix step into a well-distributed seed, then xorshift."""
    x = (step * 2654435761 + 1) & 0xFFFFFFFF
    return _xorshift32(x)


# Markov chain: each state lists its possible successors (including itself).
# Order matters for the weighted pick — all options are equally likely.
_TRANSITIONS = {
    "Clear":    ("Clear", "Cloudy", "Windy"),
    "Cloudy":   ("Cloudy", "Clear", "Overcast", "Windy"),
    "Overcast": ("Overcast", "Cloudy", "Rain", "Windy"),  # Snow appended in Fall/Winter
    "Windy":    ("Windy", "Clear", "Cloudy", "Overcast"),
    "Rain":     ("Rain", "Overcast", "Storm"),
    "Storm":    ("Storm", "Rain", "Overcast"),
    "Snow":     ("Snow", "Cloudy", "Overcast"),
}

# How long each weather state lasts, in in-game minutes (min, max inclusive).
_DURATION_RANGES = {
    "Clear":    (120, 300),
    "Cloudy":   ( 90, 240),
    "Overcast": ( 60, 180),
    "Windy":    ( 60, 150),
    "Rain":     ( 60, 180),
    "Storm":    ( 30,  90),
    "Snow":     ( 90, 240),
}

_COLD_SEASONS = ("Fall", "Winter")


def _compute_transition(step, current_weather, season):
    """
    Given a transition step index, current weather, and season, return
    (next_weather, duration_minutes) using the seeded PRNG.

    The result is fully deterministic for a given (step, current_weather, season).
    """
    x = _seeded_rand(step)

    options = _TRANSITIONS.get(current_weather, ("Clear",))
    if current_weather == "Overcast" and season in _COLD_SEASONS:
        # Extend with a mutable copy so Snow becomes possible
        options = options + ("Snow",)

    next_weather = options[x % len(options)]

    x = _xorshift32(x)
    min_d, max_d = _DURATION_RANGES.get(next_weather, (60, 180))
    duration = min_d + (x % (max_d - min_d + 1))

    return next_weather, duration


class WeatherSystem:
    """
    Manages automatic weather transitions over in-game time.

    State is stored entirely in context.environment so it persists across saves:
      - 'weather'       : current weather string
      - 'weather_step'  : int, global transition counter (seed for PRNG)
      - 'weather_timer' : float, in-game minutes remaining in current state

    Usage:
        ws = WeatherSystem()
        ws.update(game_minutes_elapsed, context.environment)
        forecast = ws.get_forecast(context.environment, hours=72)
    """

    def update(self, game_minutes, environment):
        """
        Advance the weather simulation by game_minutes in-game minutes.

        If the current state's timer expires, transitions to the next state
        (possibly multiple times if game_minutes is large, e.g. after a save load).
        """
        if game_minutes <= 0:
            return

        timer = environment.get('weather_timer', 0.0)
        timer -= game_minutes

        while timer <= 0:
            step = environment.get('weather_step', 0)
            current = environment.get('weather', 'Clear')
            season = environment.get('season', 'Summer')
            next_weather, duration = _compute_transition(step, current, season)
            environment['weather'] = next_weather
            environment['weather_step'] = step + 1
            timer += duration

        environment['weather_timer'] = timer

    def get_forecast(self, environment, hours=72):
        """
        Return a deterministic weather forecast for the next `hours` in-game hours.

        Returns a list of (weather, duration_minutes) tuples. The first entry is
        the current weather with its remaining time; subsequent entries are future
        states. The list covers at least `hours * 60` minutes of future time.
        """
        current = environment.get('weather', 'Clear')
        step = environment.get('weather_step', 0)
        remaining = environment.get('weather_timer', 60.0)
        season = environment.get('season', 'Summer')

        forecast = [(current, int(remaining))]
        total_minutes = remaining
        target_minutes = hours * 60

        while total_minutes < target_minutes:
            next_weather, duration = _compute_transition(step, current, season)
            forecast.append((next_weather, duration))
            total_minutes += duration
            current = next_weather
            step += 1

        return forecast
