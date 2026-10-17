# Bootstrap verification receipt

Local verification on 2026-10-17 with `leanprover/lean4:v4.35.0`:

- `lake build`: all 12 targets built successfully, including the executable.
- `python3 scripts/check_proofs.py`: no proof placeholders or custom axioms.
- `lake env lean tests/ProofAudit.lean`: all six theorem declarations checked;
  dependencies only standard `propext`, `Classical.choice`, and `Quot.sound`.
- `python3 -m unittest discover -s tests -v`: 11 test groups passed, including
  80 deterministically generated relation cases plus transport, facets,
  pagination, invalid-input, and source-adapter regressions.
- Full parity against clean public Log Pose commit
  `734fddd33d88a5ac3c63cf3f7b8df1ab3f1bb76a`: passed.
  - 1,240 candidates
  - 348 exact placements
  - 5,964 memberships
  - 1,288 queries (all full neighborhoods plus filtered/paginated cases)
  - 47,288 exact unordered pairs
  - Exact support identities and both endpoint occurrence IDs matched.
  - Full batch elapsed approximately 101 seconds on the development cloud host.
    This is a correctness regression run, not a controlled performance benchmark.

The public-source corpus remains outside this repository. CI reproduces the
build, axiom audit, test suite, and pinned-source parity on every push and pull
request. Its status is available in the repository's Actions tab.

These checks establish the stated finite membership/query semantics and tested
wire behavior. They do not prove source authenticity, retained-row integrity,
knowledge-time replay, relationship validity, database migrations, or production
readiness. See README.md for the precise proof boundary and next slices.
