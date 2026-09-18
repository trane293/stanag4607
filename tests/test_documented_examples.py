"""Smoke tests for the scripts linked from the public example gallery."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/mission_dwell_hi_res_targets.gmti"


def _run_example(name: str) -> str:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / name), str(FIXTURE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return result.stdout


def test_inspect_targets_example() -> None:
    output = _run_example("inspect_targets.py")
    assert "2026-04-29T08:30:00+00:00" in output
    assert "3 targets" in output
    assert "target 0:" in output


def test_round_trip_example() -> None:
    output = _run_example("round_trip.py")
    assert "packets: 1" in output
    assert "byte-identical: yes" in output


@pytest.mark.parametrize(
    "page",
    ["README.md", "docs/PACKETS.md", "docs/STREAMS.md", "docs/GEOJSON.md"],
)
def test_python_documentation_snippets_compile(page: str) -> None:
    contents = (ROOT / page).read_text(encoding="utf-8")
    snippets = re.findall(r"```python\n(.*?)\n```", contents, re.DOTALL)
    assert snippets, f"{page} has no runnable Python examples"
    for snippet in snippets:
        ast.parse(snippet, filename=page)
