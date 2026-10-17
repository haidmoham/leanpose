# Library discovery before implementation

Investigated on 2026-10-17. Pins were checked against actual upstream files, not
only search results or package-index summaries. Prefer reuse; dependencies must
solve a concrete problem in the current slice.

## Used now

- [Lean v4.35.0](https://github.com/leanprover/lean4/tree/v4.35.0): the toolchain
  provides the runtime, Lake, `List.filter`, `flatMap`, `eraseDups`, `mergeSort`,
  membership theorems, `simp`. Reusing these avoids a handwritten
  collections or proof infrastructure layer.
- [Lean JSON](https://lean-lang.org/doc/api/Lean/Data/Json/FromToJson/Basic.html):
  built-in `Lean.Json`, `FromJson`, and `ToJson`, including generated structure
  codecs. No custom JSON parser, external JSON package, or native FFI bridge.
- Python standard-library `unittest`, `json`, and `subprocess`: black-box testing
  and adaptation only; the query logic executed by users is compiled Lean.

The `lean-toolchain` pins the exact release and `lake-manifest.json` records the
empty external dependency graph. The initial one-file/stdin/JSONL surface needs
no option parser: query options are typed JSON fields.

## Investigated and deferred

- [mathlib v4.35.0](https://github.com/leanprover-community/mathlib4/tree/v4.35.0)
  (Apache-2.0): `Finset` and its algebra are valuable once richer set/theory
  obligations justify them. Lean core already proves the list membership facts
  used here; adding mathlib and its cache solely for those would be unnecessary.
- [Batteries v4.35.0](https://github.com/leanprover-community/batteries/tree/v4.35.0)
  (Apache-2.0), commit `66e469188fe07963e5cf666c7d4433f45b8131c5`:
  useful extra data structures and lemmas, no missing primitive in this slice.
- [Aesop](https://github.com/leanprover-community/aesop) (Apache-2.0), compatible
  mathlib pin `4a174c490d8707121c4a9290800489f105d85e07`: stronger proof search,
  unnecessary for these short `simp` proofs.
- [lean4-cli v4.35.0](https://github.com/leanprover/lean4-cli/tree/v4.35.0)
  (MIT), commit `c24fe6078c630e89b489bffe59b3e20ac30d12c8`: add for a multi-command
  CLI rather than growing a handwritten flag parser.
- [Plausible](https://github.com/leanprover-community/plausible), compatible pin
  `dfa4f38190d07c37e315953e08b90fe2d95b3c24`: promising Lean-side generated tests.
  Existing deterministic external oracle tests cover the current wire boundary.
- [Std.Time](https://github.com/leanprover/lean4/blob/v4.35.0/src/Std/Time.lean):
  timestamp/calendar parsing for upcoming temporal selection. Do not implement
  calendar arithmetic ourselves, or conflate capture and arrival clocks.
- [Std.Http](https://github.com/leanprover/lean4/blob/v4.35.0/src/Std/Http.lean):
  native HTTP/1.1 and async support already included in the pinned toolchain.
  A later service does not need an invented HTTP server framework.
- [leanprover/leansqlite v4.35.0](https://github.com/leanprover/leansqlite/tree/v4.35.0)
  (Apache-2.0): exact compatible toolchain verified. Prepared statements and a
  read-only low-level connection are suitable for the next storage slice. The
  upstream high-level API remains experimental; do not track floating `main`,
  which had already advanced to 4.36.0-rc1 during this investigation.

Compatibility cross-check:
[mathlib v4.35.0 lockfile](https://github.com/leanprover-community/mathlib4/blob/v4.35.0/lake-manifest.json).
If mathlib becomes necessary, use its coherent pinned dependency set instead of
independently choosing the latest Batteries/Aesop versions.
