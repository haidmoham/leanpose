# leanpose development

- Read README.md and docs/architecture.md before changing semantics.
- Discover existing Lean/Std and ecosystem libraries before inventing infrastructure.
  Record relevant alternatives and compatible pins in docs/libraries.md.
- Keep exact artifact revision + category identity, occurrence IDs, and separate
  clock meanings. Co-listing never becomes a reviewed relationship or probability.
- The executable must use the definitions whose behavior is proved. Do not add
  a parallel, disconnected specification and describe it as implementation proof.
- No sorry, admit, custom axioms, or unchecked proof shortcuts for claimed results.
  State clearly which boundary checks are tested rather than formally proved.
- Work on a feature branch. Preserve unrelated changes and never modify the
  separate Log Pose oracle checkout as part of a parity run.
- Before publishing, run lake build, scripts/check_proofs.py, the theorem axiom
  audit in tests/ProofAudit.lean, the Python unittest suite, and full pinned-source
  parity. Check the exact remote commit's CI before calling the change verified.
- Do not copy the retained source corpus, private data, credentials, or local
  research material into this public repository. Synthetic fixtures are preferred.
