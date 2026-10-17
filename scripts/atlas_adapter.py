#!/usr/bin/env python3
"""Convert a public Log Pose atlas-membership index to the Lean wire boundary.

This reads identifiers and membership metadata only, never retained source bodies.
The caller owns the original index's validation and provenance authenticity.
"""
import argparse
import json
from pathlib import Path


def convert(index):
    candidates = [row["id"] for row in index["candidates"]]
    members = [[] for _ in index["placements"]]
    for membership in index["memberships"]:
        members[membership["placement_index"]].append({
            "candidateId": candidates[membership["candidate_index"]],
            "occurrenceIds": membership["occurrence_ids"],
        })
    placements = []
    for number, placement in enumerate(index["placements"]):
        source = index["artifacts"][placement["artifact_index"]]
        revision = source.get("commit") or source.get("artifact_path") or source.get("url")
        if not revision:
            raise ValueError("artifact lacks an immutable revision locator")
        placements.append({
            "artifact": {
                "source": source["source"],
                "inventoryYear": source["inventory_year"],
                "repository": source.get("repository"),
                "revision": revision,
                "rawSha256": source["raw_sha256"],
            },
            "category": placement["source_category"],
            "members": members[number],
        })
    return {"schemaVersion": "leanpose.membership.v1", "candidateIds": candidates,
            "placements": placements}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("candidate")
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()
    request = {"snapshot": convert(json.loads(args.index.read_text())),
               "query": {"candidateId": args.candidate, "limit": args.limit}}
    print(json.dumps(request, separators=(",", ":")))


if __name__ == "__main__":
    main()
