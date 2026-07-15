"""Test source auto-discovery behavior.

This file characterizes how pkgutil-based discovery works in
src/usage/sources/ and verifies expected invariants.
"""
from usage.sources import discover


def test_discover_finds_demo():
    registry = discover()
    assert "demo" in registry


def test_discover_skips_underscore_modules():
    registry = discover()
    assert "template" not in registry  # _template.py is skipped


def test_registered_sources_match_protocol():
    for name, src in discover().items():
        assert src.name == name
        assert callable(getattr(src, "fetch", None))
