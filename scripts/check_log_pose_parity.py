#!/usr/bin/env python3
"""Compare the compiled Lean query with the actual public Log Pose Python oracle.

The separate checkout is read-only. Corpus data and generated responses stay in
memory and are not copied into this repository.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from atlas_adapter import convert

ROOT = Path(__file__).resolve().parents[1]
PIN = "734fddd33d88a5ac3c63cf3f7b8df1ab3f1bb76a"


def main():
    if not __debug__:
        raise SystemExit("parity checks require Python without -O/PYTHONOPTIMIZE")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-pose", required=True, type=Path)
    parser.add_argument("--allow-other-revision", action="store_true")
    args = parser.parse_args()
    checkout = args.log_pose.resolve()
    revision = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if revision != PIN and not args.allow_other_revision:
        raise SystemExit(f"expected Log Pose {PIN}, got {revision}; explicitly allow another revision if intended")
    if subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain", "--untracked-files=no"], text=True).strip():
        raise SystemExit("Log Pose tracked files must be clean for a reproducible parity receipt")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(checkout / "src"))
    from log_pose.atlas_membership import build_atlas_membership, select_candidate_neighborhood

    projection = json.loads((checkout / "web/data/topology-discovery.json").read_text())
    index = build_atlas_membership(projection)
    snapshot = convert(index)
    candidates = snapshot["candidateIds"]
    queries = [{"candidateId": candidate, "limit": len(candidates)} for candidate in candidates]
    # Exercise the actual source's facets and bounded pagination as well as every full neighborhood.
    for placement in snapshot["placements"][:12]:
        if not placement["members"]:
            continue
        center = placement["members"][0]["candidateId"]
        for facets in [{"source": placement["artifact"]["source"]},
                       {"year": placement["artifact"]["inventoryYear"]},
                       {"category": placement["category"]},
                       {"artifactSha256": placement["artifact"]["rawSha256"]}]:
            queries.append({"candidateId": center, "facets": facets, "offset": 1, "limit": 7})
    started = time.monotonic()
    result = subprocess.run([str(ROOT / ".lake/build/bin/leanpose"), "--batch"],
                            input=json.dumps({"snapshot": snapshot, "queries": queries}),
                            capture_output=True, text=True, check=False)
    if result.returncode:
        raise SystemExit(f"Lean failed ({result.returncode}): {result.stderr}\n{result.stdout[:2000]}")
    responses = json.loads(result.stdout)
    if len(responses) != len(queries):
        raise AssertionError("response count differs from query count")
    occurrence_by_pair = {(row["candidate_index"], row["placement_index"]): row["occurrence_ids"]
                          for row in index["memberships"]}
    indices = {candidate: i for i, candidate in enumerate(candidates)}
    directed_count = 0
    for number, (query, actual) in enumerate(zip(queries, responses)):
        facets = query.get("facets", {})
        expected = select_candidate_neighborhood(index, query["candidateId"],
            source=facets.get("source"), year=facets.get("year"), category=facets.get("category"),
            artifact_sha256=facets.get("artifactSha256"), offset=query.get("offset", 0),
            limit=query.get("limit", 60))
        for lean_key, python_key in [("candidateId", "candidate_id"), ("total", "total"),
                                      ("offset", "offset"), ("limit", "limit"), ("truncated", "truncated")]:
            assert actual[lean_key] == expected[python_key], (number, lean_key)
        assert [n["candidateId"] for n in actual["neighbors"]] == [n["candidate_id"] for n in expected["neighbors"]], number
        for observed, original in zip(actual["neighbors"], expected["neighbors"]):
            supports = []
            for placement_index in original["supporting_placement_indices"]:
                placement = snapshot["placements"][placement_index]
                supports.append({"artifact": placement["artifact"], "category": placement["category"],
                    "centerOccurrenceIds": occurrence_by_pair[indices[query["candidateId"]], placement_index],
                    "neighborOccurrenceIds": occurrence_by_pair[original["candidate_index"], placement_index]})
            assert observed["supports"] == supports, (number, observed["candidateId"], "supports")
        if number < len(candidates):
            directed_count += actual["total"]
    assert directed_count % 2 == 0
    if revision == PIN:
        assert directed_count // 2 == 47288, "pinned pair-count regression"
    print(json.dumps({"status": "passed", "logPoseRevision": revision,
        "candidates": len(candidates), "placements": len(snapshot["placements"]),
        "memberships": index["counts"]["memberships"], "queries": len(queries),
        "exactUnorderedPairs": directed_count // 2,
        "seconds": round(time.monotonic() - started, 3)}, indent=2))


if __name__ == "__main__":
    main()
