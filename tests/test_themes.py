from src.themes import DEFAULT_GRADIENT, NIGHT_GRADIENT, background_gradient


def test_clear_night_uses_night_palette():
    assert background_gradient("Clear", is_night=True) == NIGHT_GRADIENT


def test_known_conditions_get_their_own_palette():
    assert background_gradient("Rain") != DEFAULT_GRADIENT


def test_unknown_or_missing_condition_falls_back_to_default():
    assert background_gradient(None) == DEFAULT_GRADIENT
    assert background_gradient("Unicorns") == DEFAULT_GRADIENT
