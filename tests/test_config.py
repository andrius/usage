from datetime import date, timedelta
from usage.config import load_config, slice_creds, window_from_config


def test_slice_creds_filters_by_prefix():
    env = {"GITHUB_TOKEN": "t", "HETZNER_API_TOKEN": "h", "OTHER": "x"}
    assert slice_creds(env, "GITHUB") == {"GITHUB_TOKEN": "t"}


def test_slice_creds_none_prefix_returns_empty():
    assert slice_creds({"A": "b"}, None) == {}


def test_window_from_config_uses_default_days(tmp_path):
    cfg = {"window": {"default_days": 7}}
    w = window_from_config(cfg)
    assert (w.until - w.since) == timedelta(days=7)


def test_window_falls_back_when_no_config():
    w = window_from_config({})
    assert (w.until - w.since) == timedelta(days=30)


def test_load_config_reads_yaml(tmp_path):
    f = tmp_path / "config.yml"
    f.write_text("window:\n  default_days: 14\n")
    assert load_config(f) == {"window": {"default_days": 14}}


def test_load_config_missing_file_returns_empty(tmp_path):
    assert load_config(tmp_path / "nope.yml") == {}
