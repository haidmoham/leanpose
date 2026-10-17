# leanpose

An executable Lean 4 rewrite of the **exact membership query kernel** from
[Log Pose](https://github.com/haidmoham/log-pose). This is the first vertical
slice, not a replacement for the existing product or evidence store.

The original repository and its deployment are unchanged. The initial boundary
is JSON in / JSON out: immutable source-artifact metadata, exact category
placements, candidate memberships, and retained occurrence identifiers.

## Run

Install [Lean through elan](https://lean-lang.org/install/), then:

```sh
lake build
lake exe leanpose fixtures/revisions.json
python3 -m unittest discover -s tests -v
```

The compiler is pinned to **Lean 4.35.0**. There are no external Lean or Python
package dependencies. The implementation reuses Lean's list operations and
theorems, JSON parser/derived codecs, sorting, and proof tactics. See
[the library investigation](docs/libraries.md) for researched alternatives and
version-compatible next steps.

```sh
# One request from stdin, or one independent request per line.
cat fixtures/revisions.json | .lake/build/bin/leanpose
.lake/build/bin/leanpose --jsonl < requests.jsonl
# A single {"snapshot": ..., "queries": [...]} batch, parsed once:
.lake/build/bin/leanpose --batch < batch.json
```

Successful requests emit JSON to stdout and exit 0. Invalid requests emit a JSON
`error` and exit 1; usage/filesystem failures exit 2. JSONL keeps processing after
an invalid request, emits one response per line, and exits 1 if any request failed.

## What works

- Exact source, inventory-year, category, and artifact-content-hash facets.
- Distinct, lexically ordered neighbors with total count and offset/limit paging.
- Every exact supporting placement, including **separate revisions with identical
  source bytes**.
- Retained occurrence IDs for both endpoints of every support.
- Explicit rejection of unknown candidates and malformed/ambiguous memberships.
- Known candidates with no memberships return a legitimate empty neighborhood.

A placement's identity is `(source, inventoryYear, repository, immutable revision,
rawSha256, exact category)`. Inventory year alone is not a revision. The SHA facet
filters content: multiple revisions with the same hash all match it.

This wire schema is intentionally smaller than Log Pose's complete export.
It retains occurrence identifiers, **not the original source row bodies**, source
hash verification, identity reviews, research claims, or build manifests. An
inventory co-listing is an observation, not a company identity, business
relationship, strength score, or probability.

## What Lean proves

The CLI directly invokes the definitions proved in
[`LeanPose/Kernel.lean`](LeanPose/Kernel.lean):

- `candidate_placement_iff`: both membership directions express the same relation.
- `supporting_placement_iff`: supports contain exactly the shared placements
  passing every requested facet, with no invented or omitted placement.
- `neighbor_iff`: before pagination, a candidate is returned if and only if it is
  distinct from the center and shares an eligible exact placement.
- `no_self_neighbor` and `neighbor_symmetric`.
- `occurrence_witness_iff`: reported distinct occurrence IDs come exactly from
  the selected candidate's retained membership records.

These theorems quantify over all finite inputs. Structural validation is a
separate executable boundary, covered by tests. The current proof scope does
**not** include parser/serializer correctness, validator completeness, output
pagination, canonical hashing, source authenticity, SQL, or a claim's truth.
There are no `sorry`, `admit`, custom axioms, or unchecked proof shortcuts.

## Compatibility checks

The committed fixture is fully synthetic. Tests exercise equal-byte revisions,
multiple supporting occurrences, exact facets, empty/unknown candidates, paging,
malformed input, and deterministic generated finite relations against an
independent set-based oracle.

The [public-source parity test](scripts/check_log_pose_parity.py) reads a
separate checkout of Log Pose, builds its existing membership index, converts it
in memory, and compares the compiled Lean responses with the actual Python
selector. It neither rewrites Log Pose nor commits its corpus here. CI runs it after the
synthetic suite; it can also be run locally:

```sh
python3 scripts/check_log_pose_parity.py --log-pose /path/to/log-pose
```

The [bootstrap verification receipt](docs/verification.md) records the checked
commands and full-snapshot parity result.

## Scope and next slices

This implementation prioritizes a small, checked semantic boundary. It avoids
materializing all candidate pairs, but currently scans placements to find the
center and uses list deduplication. It does not yet match the indexed performance
of Log Pose's production membership index. Large-input limits and a long-running
service are not provided; use the CLI for trusted, bounded local inputs.

1. Preserve the proven relation while introducing `Std.HashMap`/`Std.HashSet`
   indexes; prove refinement and benchmark the full public snapshot.
2. Import read-only snapshots with pinned `leanprover/leansqlite v4.35.0`, retaining
   identifiers and hashes; keep Python ingestion authoritative during migration.
3. Formalize capture-time selection and deterministic tie breaking. Add separate
   publication, arrival, event/validity, and review-time types using `Std.Time`.
   Inventory-year filtering here is **not** historical knowledge-time replay.
4. Add a native `Std.Http` read service and replace the existing query boundary
   behind parity tests. Keep the current browser UI until that boundary is ready.
5. Only then consider the review workflow, ingestion, and UI migration.

See [architecture and trust boundary](docs/architecture.md). No production
cutover, private data, paid infrastructure, or new credentials are part of this
bootstrap.

## Licensing and source provenance

Original code in this repository was written for this rewrite. No third-party
source bodies or corpus files have been copied into it. Log Pose had no root
license file at the inspected public revision; no license for that repository's
code or retained third-party evidence is inferred or changed here. This initial
repository deliberately does not select a new distribution license on the
owner's behalf. Lean and any future dependencies retain their own licenses.
