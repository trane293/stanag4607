"""Ensure every vendored interoperability fixture matches its provenance record."""

import hashlib
import json
from pathlib import Path


def test_vendored_fixture_hashes_match_manifest() -> None:
    root = Path(__file__).parent.parent
    manifest = json.loads((root / "references/data/manifest.json").read_text())
    dataset = manifest["datasets"][0]
    records = {Path(item["filename"]).name: item for item in dataset["files"]}

    for relative in dataset["vendored_fixtures"]:
        fixture = root / relative
        record = records[fixture.name]
        content = fixture.read_bytes()
        assert len(content) == record["bytes"]
        assert hashlib.sha256(content).hexdigest() == record["sha256"]
