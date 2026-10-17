# Architecture and trust boundary

`Model.lean` defines the JSON record grains. `Kernel.lean` defines executable
finite-relation queries and their theorems. `Protocol.lean` validates incoming
records, applies pagination, and assembles provenance-preserving responses.
`Main.lean` provides transport only. The Python adapter bridges the existing
public atlas export and never participates in production query evaluation.

## Data contract

A snapshot contains a schema version, unique candidate IDs (including candidates
with no membership), and unique exact placements. Each placement holds immutable
artifact identity metadata, a category path, and unique candidate memberships.
Each membership holds nonempty, unique occurrence identifiers.

The validator rejects duplicate placement keys even if their membership lists
differ, unknown membership references, repeated candidate memberships, empty
identity strings, and malformed lowercase SHA-256 strings. Hash shape validation
does not verify the content digest or prove an upstream revision is immutable.

The repository field is optional: JSON null means absent, while an empty string
remains distinct. The adapter preserves this distinction because upstream
artifact identity hashes it. This wire model does not implement upstream
cryptographic artifact-ID hashing.

Queries filter placements before finding neighbors. Supports are whole exact
placements, never source/year/category summaries that could collapse revisions.
Occurrence IDs on each support trace each endpoint back to membership inputs.
No candidate is promoted to a company and no co-listing becomes a reviewed claim.

## What is checked where

- Lean kernel checks theorem proof terms about the actual executable definitions.
- Runtime validation checks well-formedness needed at the external boundary.
- Black-box tests check parsing, validation, sorting, paging, error behavior, and
  source adaptation. These are tests, not formal proofs of all those layers.
- Full parity compares against a separately pinned public Log Pose checkout.
- CI builds proofs and the executable, audits theorem axioms, runs the synthetic
  test suite, and compares every public-snapshot neighborhood with the pinned oracle.

The trusted computing base includes Lean's logical kernel and runtime/compiler,
its standard axioms, the operating system, and the JSON/input boundary. Standard
Lean logical axioms such as propositional extensionality are not novel domain
assumptions. No `sorryAx`, `native_decide` trust shortcut, or custom axiom is used.

## Temporal semantics are an explicit migration boundary

The present query filters inventory year only. In Log Pose, evidence capture
selection uses captured_at <= cutoff, then newest capture and deterministic
provider/record-ID/row-ID ties. Ingestion time is separate: backfilling an old
capture can change a capture-time view. Reviewed relationship visibility also
needs source/publication/retrieval, original arrival, premises, and review clocks.
These semantics must be ported with dedicated types and parity/proof obligations;
none is claimed by the membership kernel.

## Source reference

Inspected public Log Pose revision:
[`734fddd33d88a5ac3c63cf3f7b8df1ab3f1bb76a`](https://github.com/haidmoham/log-pose/tree/734fddd33d88a5ac3c63cf3f7b8df1ab3f1bb76a).

Contracts reviewed: `src/log_pose/atlas_membership.py`,
`tests/test_atlas_membership.py`, `docs/atlas-membership.md`, `storage.py`, and
`topology_store.py`. This rewrite changes none of those files.
