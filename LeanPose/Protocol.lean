import LeanPose.Kernel

namespace LeanPose
open Lean

/-- Wire data is checked before it can be queried. This validator is tested, not formally proved. -/
def validateSnapshot (s : Snapshot) : Except String Unit := do
  unless s.schemaVersion == "leanpose.membership.v1" do
    throw "unsupported snapshot schemaVersion"
  unless s.candidateIds.eraseDups.length == s.candidateIds.length do
    throw "duplicate candidate ID"
  unless s.candidateIds.all (! ·.isEmpty) do
    throw "empty candidate ID"
  let keys := s.placements.map fun p => (p.artifact, p.category)
  unless keys.eraseDups.length == keys.length do
    throw "duplicate artifact/category placement"
  for p in s.placements do
    if p.artifact.source.isEmpty || p.artifact.revision.isEmpty || p.category.isEmpty then
      throw "placement needs source, immutable revision, and category"
    unless p.artifact.rawSha256.length == 64 &&
        p.artifact.rawSha256.toList.all (fun c => c.isDigit || ('a' ≤ c && c ≤ 'f')) do
      throw "rawSha256 must be a lowercase 64-character SHA-256 digest"
    let ids := placementMembers p
    unless ids.eraseDups.length == ids.length do
      throw "duplicate candidate membership in a placement"
    for m in p.members do
      unless s.candidateIds.contains m.candidateId do
        throw "membership references an unknown candidate"
      if m.occurrenceIds.isEmpty || m.occurrenceIds.any String.isEmpty then
        throw "membership needs nonempty retained occurrence IDs"
      unless m.occurrenceIds.eraseDups.length == m.occurrenceIds.length do
        throw "duplicate occurrence ID in a membership"

structure Support where
  artifact : Artifact
  category : String
  centerOccurrenceIds : List String
  neighborOccurrenceIds : List String
  deriving ToJson

structure Neighbor where
  candidateId : String
  supports : List Support
  deriving ToJson

structure Response where
  schemaVersion : String := "leanpose.neighborhood.v1"
  candidateId : String
  total : Nat
  offset : Nat
  limit : Nat
  truncated : Bool
  neighbors : List Neighbor
  deriving ToJson

/-- The CLI calls the same definitions about which Kernel.lean proves its theorems. -/
def querySnapshot (s : Snapshot) (q : Query) : Except String Response := do
  validateSnapshot s
  unless s.candidateIds.contains q.candidateId do
    throw "unknown center candidate"
  let all := neighbors s.placements q.facets q.candidateId
  let selected := (all.drop q.offset).take q.limit
  let result := selected.map fun candidate => {
    candidateId := candidate
    supports := (supportingPlacements s.placements q.facets q.candidateId candidate).map fun p => {
      artifact := p.artifact
      category := p.category
      centerOccurrenceIds := occurrenceWitnesses p q.candidateId
      neighborOccurrenceIds := occurrenceWitnesses p candidate
    : Support }
  : Neighbor }
  return {
    candidateId := q.candidateId
    total := all.length
    offset := q.offset
    limit := q.limit
    truncated := q.offset + selected.length < all.length
    neighbors := result
  }

def handleRequest (input : String) : Except String Json := do
  let json ← Json.parse input
  let req : Request ← fromJson? json
  toJson <$> querySnapshot req.snapshot req.query

structure BatchRequest where
  snapshot : Snapshot
  queries : List Query
  deriving FromJson

/-- Reuse a parsed snapshot for parity/benchmark batches; each query still validates it. -/
def handleBatchRequest (input : String) : Except String Json := do
  let json ← Json.parse input
  let req : BatchRequest ← fromJson? json
  validateSnapshot req.snapshot
  let responses ← req.queries.mapM (querySnapshot req.snapshot)
  return toJson responses

end LeanPose
