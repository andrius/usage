"""Claude Code subscription usage source (parses `claude -p /usage`)."""
from __future__ import annotations

import asyncio
import re
from decimal import Decimal

from ..models import FetchContext, Metric, SourceReport

# "Current session: 24% used ... resets Jul 15, 9:59am (UTC)"
_SESSION = re.compile(r"Current session:\s*(\d+)%\s*used.*?resets\s+(.+?)\s*\(", re.S)
# "Current week (all models): 71% used ... resets Jul 16, 1:59pm (UTC)"
_WEEK = re.compile(r"Current week \(([^)]+)\):\s*(\d+)%\s*used.*?resets\s+(.+?)\s*\(", re.S)


def parse_usage(text: str) -> list[Metric]:
    metrics: list[Metric] = []
    for m in _SESSION.finditer(text):
        metrics.append(Metric(source="claude_code", scope="plan:claude-code",
                              label="Session usage", dimension="quota",
                              used=Decimal(m.group(1)), limit=Decimal("100"), unit="%"))
    for m in _WEEK.finditer(text):
        model = m.group(1)
        metrics.append(Metric(source="claude_code", scope="plan:claude-code",
                              label=f"Weekly usage ({model})", dimension="quota",
                              used=Decimal(m.group(2)), limit=Decimal("100"), unit="%"))
    return metrics


def _no_metric_warnings(stdout: str, stderr: str) -> list[str]:
    """Explain why `claude -p /usage` yielded no subscription metrics."""
    combined = stdout + "\n" + stderr
    if "takes precedence" in combined or "Total cost:" in stdout:
        return [
            "subscription usage unavailable: claude ran in API-key/gateway mode "
            "(an auth override such as ANTHROPIC_API_KEY takes precedence over "
            "your claude.ai login). Run under your claude.ai subscription to see "
            "session/weekly usage."
        ]
    return ["could not parse /usage; raw output follows:\n" + stdout]


class ClaudeCodeSource:
    name = "claude_code"
    env_prefix = None

    async def fetch(self, ctx: FetchContext) -> SourceReport:
        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", "/usage",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode(errors="replace")
        metrics = parse_usage(out)
        if metrics:
            return SourceReport(source=self.name, metrics=metrics)
        return SourceReport(
            source=self.name,
            warnings=_no_metric_warnings(out, stderr.decode(errors="replace")),
        )


source = ClaudeCodeSource()
