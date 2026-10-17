"""Black-box tests of the compiled Lean executable, not a Python rewrite."""
import copy
import json
import random
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / ".lake/build/bin/leanpose"
FIXTURE = ROOT / "fixtures/revisions.json"


def run(request):
    result = subprocess.run([str(BINARY)], input=json.dumps(request), text=True,
                            capture_output=True, check=False)
    return result.returncode, json.loads(result.stdout)


def oracle(request):
    """Deliberately independent set-based finite relation oracle."""
    query, snapshot = request["query"], request["snapshot"]
    center, facets = query["candidateId"], query.get("facets", {})
    support = {}
    for placement in snapshot["placements"]:
        artifact = placement["artifact"]
        values = {"source": artifact["source"], "year": artifact["inventoryYear"],
                  "category": placement["category"], "artifactSha256": artifact["rawSha256"]}
        if any(value is not None and values[key] != value for key, value in facets.items()):
            continue
        members = {m["candidateId"]: set(m["occurrenceIds"]) for m in placement["members"]}
        if center not in members:
            continue
        for candidate in members.keys() - {center}:
            support.setdefault(candidate, []).append({
                "artifact": artifact, "category": placement["category"],
                "centerOccurrenceIds": sorted(members[center]),
                "neighborOccurrenceIds": sorted(members[candidate]),
            })
    ordered = sorted(support)
    offset, limit = query.get("offset", 0), query.get("limit", 60)
    selected = ordered[offset:offset + limit]
    return {"schemaVersion": "leanpose.neighborhood.v1", "candidateId": center,
            "total": len(ordered), "offset": offset, "limit": limit,
            "truncated": offset + len(selected) < len(ordered),
            "neighbors": [{"candidateId": c, "supports": support[c]} for c in selected]}


def normalized(response):
    for neighbor in response.get("neighbors", []):
        for support in neighbor["supports"]:
            support["centerOccurrenceIds"].sort()
            support["neighborOccurrenceIds"].sort()
    return response


class KernelCLI(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(FIXTURE.read_text())

    def check_oracle(self, request):
        code, actual = run(request)
        self.assertEqual(code, 0, actual)
        self.assertEqual(normalized(actual), oracle(request))

    def test_exact_revision_support_and_occurrences(self):
        self.check_oracle(self.request)
        _, actual = run(self.request)
        self.assertEqual(actual["total"], 2)
        self.assertEqual([n["candidateId"] for n in actual["neighbors"]], ["beta", "gamma"])
        self.assertEqual(len(actual["neighbors"][0]["supports"]), 2)

    def test_no_cross_revision_edge(self):
        request = copy.deepcopy(self.request)
        request["snapshot"]["placements"] = request["snapshot"]["placements"][:2]
        request["snapshot"]["placements"][0]["members"] = [{"candidateId": "alpha", "occurrenceIds": ["a"]}]
        request["snapshot"]["placements"][1]["members"] = [{"candidateId": "beta", "occurrenceIds": ["b"]}]
        self.check_oracle(request)
        self.assertEqual(run(request)[1]["neighbors"], [])

    def test_facets(self):
        for facets in [{"source": "cncf"}, {"year": 2024}, {"category": "Data / Store"},
                       {"artifactSha256": "a" * 64}, {"source": "absent"},
                       {"year": 2025, "category": "Data / Store"}]:
            with self.subTest(facets=facets):
                self.request["query"]["facets"] = facets
                self.check_oracle(self.request)

    def test_pagination_and_isolated_candidate(self):
        for offset, limit in [(0, 0), (0, 1), (1, 1), (2, 60), (100, 60)]:
            self.request["query"].update(offset=offset, limit=limit)
            self.check_oracle(self.request)
        self.request["query"] = {"candidateId": "isolated"}
        self.check_oracle(self.request)

    def test_rejects_invalid_input(self):
        mutations = [
            lambda r: r["query"].update(candidateId="unknown"),
            lambda r: r["query"].update(limit=-1),
            lambda r: r["query"].update(offset=-1),
            lambda r: r["query"].update(facets=3),
            lambda r: r["query"].update(facets={"soruce": "typo"}),
            lambda r: r["query"].update(limt=3),
            lambda r: r["snapshot"].update(schemaVersion="invalid"),
            lambda r: r["snapshot"]["candidateIds"].append("alpha"),
            lambda r: r["snapshot"]["placements"].append(copy.deepcopy(r["snapshot"]["placements"][0])),
            lambda r: r["snapshot"]["placements"][0]["artifact"].update(revision=""),
            lambda r: r["snapshot"]["placements"][0]["artifact"].update(rawSha256="bad"),
            lambda r: r["snapshot"]["placements"][0]["members"].append({"candidateId": "alpha", "occurrenceIds": ["x"]}),
            lambda r: r["snapshot"]["placements"][0]["members"][0].update(candidateId="unknown"),
            lambda r: r["snapshot"]["placements"][0]["members"][0].update(occurrenceIds=[]),
            lambda r: r["snapshot"]["placements"][0]["members"][0].update(occurrenceIds=["same", "same"]),
        ]
        for mutation in mutations:
            request = copy.deepcopy(self.request)
            mutation(request)
            with self.subTest(mutation=mutation):
                code, response = run(request)
                self.assertEqual(code, 1)
                self.assertIn("error", response)

    def test_malformed_json_and_jsonl(self):
        invalid = subprocess.run([str(BINARY)], input="{", text=True, capture_output=True)
        self.assertEqual(invalid.returncode, 1)
        valid = json.dumps(self.request)
        result = subprocess.run([str(BINARY), "--jsonl"], input=valid + "\n{\n" + valid + "\n",
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        outputs = list(map(json.loads, result.stdout.splitlines()))
        self.assertEqual(len(outputs), 3)
        self.assertEqual(outputs[0], outputs[2])
        self.assertIn("error", outputs[1])

    def test_batch_and_file_transport(self):
        queries = [{"candidateId": "alpha"}, {"candidateId": "isolated"},
                   {"candidateId": "beta", "offset": 1, "limit": 1}]
        batch = {"snapshot": copy.deepcopy(self.request["snapshot"]), "queries": queries}
        result = subprocess.run([str(BINARY), "--batch"], input=json.dumps(batch),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        expected = [oracle({"snapshot": batch["snapshot"], "query": q}) for q in queries]
        self.assertEqual([normalized(r) for r in json.loads(result.stdout)], expected)
        batch["queries"].append({"candidateId": "unknown"})
        invalid = subprocess.run([str(BINARY), "--batch"], input=json.dumps(batch),
                                 text=True, capture_output=True)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("error", json.loads(invalid.stdout))
        batch["queries"] = []
        batch["snapshot"]["schemaVersion"] = "invalid"
        empty_invalid = subprocess.run([str(BINARY), "--batch"], input=json.dumps(batch),
                                       text=True, capture_output=True)
        self.assertEqual(empty_invalid.returncode, 1)
        file_result = subprocess.run([str(BINARY), str(FIXTURE)], text=True, capture_output=True)
        self.assertEqual(file_result.returncode, 0, file_result.stderr)
        self.assertEqual(normalized(json.loads(file_result.stdout)), oracle(self.request))
        missing = subprocess.run([str(BINARY), str(ROOT / "fixtures/does-not-exist.json")],
                                 text=True, capture_output=True)
        self.assertEqual(missing.returncode, 2)

    def test_generated_relations(self):
        rng = random.Random(20261017)
        for case in range(80):
            candidates = [f"c{i}" for i in range(rng.randint(1, 12))]
            placements = []
            for p in range(rng.randint(0, 10)):
                placements.append({"artifact": {"source": "synthetic", "inventoryYear": 2020 + p % 3,
                    "repository": "fixture", "revision": f"revision-{p}", "rawSha256": "a" * 64},
                    "category": f"category-{p % 2}", "members": [{"candidateId": c,
                    "occurrenceIds": [f"occ-{p}-{c}"]} for c in candidates if rng.random() < 0.45]})
            request = {"snapshot": {"schemaVersion": "leanpose.membership.v1",
                "candidateIds": candidates, "placements": placements}, "query": {
                "candidateId": rng.choice(candidates), "offset": rng.randint(0, 3),
                "limit": rng.randint(0, 15), "facets": {} if case % 2 else {"year": 2021}}}
            with self.subTest(case=case):
                self.check_oracle(request)


if __name__ == "__main__":
    unittest.main()
