from usage.render.text import render


def test_text_groups_by_source_with_used_and_limit(sample_report):
    out = render([sample_report])
    assert "[demo]" in out
    assert "Actions minutes" in out
    assert "1240 / 3000 minutes (quota)" in out


def test_text_lists_errors(sample_report):
    out = render([sample_report], ["github: HTTP 503", "unknown source: nope"])
    assert "error: github: HTTP 503" in out
    assert "error: unknown source: nope" in out
