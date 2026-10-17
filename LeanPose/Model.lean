import Lean.Data.Json
import Lean.Elab.Deriving.FromToJson
import Lean.Elab.Deriving.Repr
import Lean.Elab.Deriving.DecEq
import Lean.Elab.Deriving.BEq

namespace LeanPose

open Lean

/-- Identity includes the immutable revision, even when two revisions have equal bytes. -/
structure Artifact where
  source : String
  inventoryYear : Nat
  repository : Option String
  revision : String
  rawSha256 : String
  deriving Repr, DecidableEq, BEq, FromJson, ToJson

/-- One candidate membership in an exact placement, with retained occurrence IDs. -/
structure Member where
  candidateId : String
  occurrenceIds : List String
  deriving Repr, DecidableEq, BEq, FromJson, ToJson

/-- One immutable artifact revision and exact source category path. -/
structure Placement where
  artifact : Artifact
  category : String
  members : List Member
  deriving Repr, DecidableEq, BEq, FromJson, ToJson

structure Snapshot where
  schemaVersion : String
  candidateIds : List String
  placements : List Placement
  deriving Repr, FromJson, ToJson

structure Facets where
  source : Option String := none
  year : Option Nat := none
  category : Option String := none
  artifactSha256 : Option String := none
  deriving Repr, ToJson

instance : FromJson Facets where
  fromJson? json := do
    let object ← json.getObj?
    unless object.toList.all (fun field => ["source", "year", "category", "artifactSha256"].contains field.1) do
      throw "unknown facet field"
    return {
      source := ← json.getObjValAs? (Option String) "source"
      year := ← json.getObjValAs? (Option Nat) "year"
      category := ← json.getObjValAs? (Option String) "category"
      artifactSha256 := ← json.getObjValAs? (Option String) "artifactSha256"
    }

def Facets.matches (q : Facets) (p : Placement) : Bool :=
  (q.source.all (· == p.artifact.source)) &&
  (q.year.all (· == p.artifact.inventoryYear)) &&
  (q.category.all (· == p.category)) &&
  (q.artifactSha256.all (· == p.artifact.rawSha256))

structure Query where
  candidateId : String
  facets : Facets := {}
  offset : Nat := 0
  limit : Nat := 60
  deriving Repr, ToJson

instance : FromJson Query where
  fromJson? json := do
    let object ← json.getObj?
    unless object.toList.all (fun field => ["candidateId", "facets", "offset", "limit"].contains field.1) do
      throw "unknown query field"
    let candidateId ← json.getObjValAs? String "candidateId"
    let facets ← json.getObjValAs? (Option Facets) "facets"
    let offset ← json.getObjValAs? (Option Nat) "offset"
    let limit ← json.getObjValAs? (Option Nat) "limit"
    return { candidateId, facets := facets.getD {}, offset := offset.getD 0, limit := limit.getD 60 }

structure Request where
  snapshot : Snapshot
  query : Query
  deriving FromJson

end LeanPose
