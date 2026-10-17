import LeanPose.Model
import Lean.Elab.Tactic.Simp

namespace LeanPose

/-- Membership identity is separate from the number of retained source occurrences. -/
def placementMembers (p : Placement) : List String :=
  p.members.map Member.candidateId

/-- Derived from the same membership relation as `placementMembers`; no trusted inverse index. -/
def candidatePlacements (ps : List Placement) (candidate : String) : List Placement :=
  ps.filter fun p => candidate ∈ placementMembers p

/-- Query only the center's eligible placements; do not expand unrelated cliques. -/
def eligiblePlacements (ps : List Placement) (q : Facets) (center : String) : List Placement :=
  (candidatePlacements ps center).filter q.matches

/-- Exact supports, with revision-qualified identities, in input placement order. -/
def supportingPlacements (ps : List Placement) (q : Facets)
    (center neighbor : String) : List Placement :=
  (eligiblePlacements ps q center).filter fun p => neighbor ∈ placementMembers p

/-- Unique neighbors, sorted by candidate ID; pagination is a separate operation. -/
def neighbors (ps : List Placement) (q : Facets) (center : String) : List String :=
  (((eligiblePlacements ps q center).flatMap placementMembers).filter
    fun candidate => candidate != center).eraseDups.mergeSort

/-- Retain all distinct occurrences for one candidate in one placement. -/
def occurrenceWitnesses (p : Placement) (candidate : String) : List String :=
  ((p.members.filter fun m => m.candidateId == candidate).flatMap Member.occurrenceIds).eraseDups

/-- The executable index directions are inverses of the same relation. -/
theorem candidate_placement_iff (ps : List Placement) (candidate : String) (p : Placement) :
    p ∈ candidatePlacements ps candidate ↔ p ∈ ps ∧ candidate ∈ placementMembers p := by
  simp [candidatePlacements]

/-- Both soundness and completeness of exact support selection, including every facet. -/
theorem supporting_placement_iff (ps : List Placement) (q : Facets)
    (center neighbor : String) (p : Placement) :
    p ∈ supportingPlacements ps q center neighbor ↔
      p ∈ ps ∧ center ∈ placementMembers p ∧ q.matches p = true ∧
        neighbor ∈ placementMembers p := by
  simp [supportingPlacements, eligiblePlacements, candidatePlacements, and_comm, and_left_comm]

/-- Before pagination, a neighbor exists exactly when an eligible shared placement does. -/
theorem neighbor_iff (ps : List Placement) (q : Facets) (center neighbor : String) :
    neighbor ∈ neighbors ps q center ↔
      neighbor ≠ center ∧ ∃ p ∈ ps, center ∈ placementMembers p ∧
        q.matches p = true ∧ neighbor ∈ placementMembers p := by
  simp [neighbors, eligiblePlacements, candidatePlacements, List.mem_flatMap,
    and_left_comm, and_comm]

/-- Querying a candidate can never report it as its own neighbor. -/
theorem no_self_neighbor (ps : List Placement) (q : Facets) (center : String) :
    center ∉ neighbors ps q center := by
  simp [neighbor_iff]

/-- Co-listing is symmetric, even though the returned neighborhood is center-specific. -/
theorem neighbor_symmetric (ps : List Placement) (q : Facets) (a b : String) :
    b ∈ neighbors ps q a ↔ a ∈ neighbors ps q b := by
  simp [neighbor_iff, ne_comm, and_left_comm, and_comm]

/-- Occurrence IDs are neither invented nor dropped by the provenance projection. -/
theorem occurrence_witness_iff (p : Placement) (candidate occurrence : String) :
    occurrence ∈ occurrenceWitnesses p candidate ↔
      ∃ m ∈ p.members, m.candidateId = candidate ∧ occurrence ∈ m.occurrenceIds := by
  simp [occurrenceWitnesses, List.mem_flatMap, and_assoc]

end LeanPose
