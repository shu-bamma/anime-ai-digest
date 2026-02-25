"""Basic tests to verify config loads and environment is set up."""


def test_config_loads():
    """Config module should import without errors."""
    from shared.config import SUPABASE_URL, SCORING_WEIGHTS
    assert isinstance(SCORING_WEIGHTS, dict)


def test_scoring_weights_sum():
    """Scoring weights should sum to ~1.0."""
    from shared.config import SCORING_WEIGHTS
    total = sum(SCORING_WEIGHTS.values())
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected ~1.0"
