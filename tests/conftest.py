"""Shared pytest configuration.

Registers Hypothesis profiles so property-based tests can be tuned per context:

    HYPOTHESIS_PROFILE=dev   pytest -q   # fast feedback (50 examples)
    HYPOTHESIS_PROFILE=ci    pytest -q   # thorough (500 examples)
    HYPOTHESIS_PROFILE=nightly pytest -q # exhaustive (2000 examples)

Default (no env var) uses the ci profile.
"""
from hypothesis import HealthCheck, settings

settings.register_profile(
    "dev",
    max_examples=50,
    deadline=2000,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    "ci",
    max_examples=500,
    deadline=5000,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    "nightly",
    max_examples=2000,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example],
)

settings.load_profile(
    __import__("os").environ.get("HYPOTHESIS_PROFILE", "ci")
)


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    config.addinivalue_line("markers", "stateful: model-based stateful test")
