"""Background gradients chosen from the current weather condition."""

DEFAULT_GRADIENT = ("#0f2027", "#203a43", "#2c5364")

# Keyed by OpenWeather's main condition ("Clear", "Rain", ...).
CONDITION_GRADIENTS = {
    "Clear": ("#1e3c72", "#2a5298", "#4a7bc8"),
    "Clouds": ("#3a4a5c", "#4f6276", "#5f7285"),
    "Rain": ("#232526", "#2f3b4a", "#414345"),
    "Drizzle": ("#2c3e50", "#3b5063", "#4b6578"),
    "Thunderstorm": ("#1a1a2e", "#2b1055", "#4a0e4e"),
    "Snow": ("#4a6785", "#6b8fb5", "#8fb3d9"),
    "Mist": ("#4b5563", "#5b6472", "#6b7280"),
    "Fog": ("#4b5563", "#5b6472", "#6b7280"),
    "Haze": ("#4b5563", "#5b6472", "#6b7280"),
    "Smoke": ("#4b5563", "#5b6472", "#6b7280"),
    "Dust": ("#6b4f2a", "#7d5f35", "#8f6f42"),
    "Sand": ("#6b4f2a", "#7d5f35", "#8f6f42"),
    "Ash": ("#3a3a3a", "#4a4a4a", "#5a5a5a"),
    "Squall": ("#2b2d42", "#3d405b", "#4a4e69"),
    "Tornado": ("#3a1c71", "#6a3a8f", "#d76d77"),
}

NIGHT_GRADIENT = ("#0f0c29", "#302b63", "#24243e")


def background_gradient(condition: str | None, is_night: bool = False) -> tuple[str, str, str]:
    """Return three colours for the page gradient.

    Clear skies at night use a dark navy palette. Unknown or missing
    conditions fall back to the default teal.
    """
    if condition == "Clear" and is_night:
        return NIGHT_GRADIENT
    if condition in CONDITION_GRADIENTS:
        return CONDITION_GRADIENTS[condition]
    return DEFAULT_GRADIENT
