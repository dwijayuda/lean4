module
import all Admitted
import Lean

public section
namespace InventoryProof

-- This theorem refers to the actual PS0-elaborated definition, not a model
-- retyped by hand. The reference specification is independently fixed by
-- the host's ChallengeSource module and checked by lake comparator.
theorem remaining_spec (stock requested : Nat) :
    Inventory.remaining stock requested = stock - requested := by
  rfl

theorem remaining_le (stock requested : Nat) :
    Inventory.remaining stock requested ≤ stock := by
  rw [remaining_spec]
  exact Nat.sub_le _ _

theorem conservation (stock requested : Nat) (h : requested ≤ stock) :
    Inventory.remaining stock requested + requested = stock := by
  rw [remaining_spec]
  exact Nat.sub_add_cancel h

end InventoryProof
