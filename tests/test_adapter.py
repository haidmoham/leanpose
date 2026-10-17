"""Compatibility boundary tests using synthetic source-shaped records only."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from atlas_adapter import convert


class AtlasAdapter(unittest.TestCase):
    def index(self):
        artifact = {"source": "synthetic", "inventory_year": 2024,
                    "repository": None, "commit": "same-revision", "raw_sha256": "a" * 64}
        return {"candidates": [{"id": "alpha"}, {"id": "beta"}],
            "artifacts": [artifact, dict(artifact, repository="")],
            "placements": [{"artifact_index": i, "source_category": "Exact / Category"} for i in range(2)],
            "memberships": [{"candidate_index": c, "placement_index": p,
                              "occurrence_ids": [f"row-{p}-{c}"]} for p in range(2) for c in range(2)]}

    def test_null_and_empty_repository_remain_distinct(self):
        wire = convert(self.index())
        self.assertIsNone(wire["placements"][0]["artifact"]["repository"])
        self.assertEqual(wire["placements"][1]["artifact"]["repository"], "")
        result = subprocess.run([str(ROOT / ".lake/build/bin/leanpose")],
            input=json.dumps({"snapshot": wire, "query": {"candidateId": "alpha"}}),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(json.loads(result.stdout)["neighbors"][0]["supports"]), 2)

    def test_revision_locator_fallback_and_missing_identity(self):
        index = self.index()
        for artifact in index["artifacts"]:
            artifact["commit"] = None
            artifact["artifact_path"] = "pinned/source.yaml"
        wire = convert(index)
        self.assertEqual(wire["placements"][0]["artifact"]["revision"], "pinned/source.yaml")
        del index["artifacts"][0]["artifact_path"]
        with self.assertRaises(ValueError):
            convert(index)

    def test_adapter_does_not_mutate_input_or_copy_source_bodies(self):
        index = self.index()
        index["memberships"][0]["rows"] = [{"private": "synthetic source body"}]
        before = copy.deepcopy(index)
        wire = convert(index)
        self.assertEqual(index, before)
        self.assertNotIn("synthetic source body", json.dumps(wire))


if __name__ == "__main__":
    unittest.main()
