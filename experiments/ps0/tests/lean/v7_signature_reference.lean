/-!
Manual official Lean 4.35.0 reference for PS0's selected declaration telescope
and optional return-type spelling. These are native Lean declarations and
are *not* subject to the PSCV0 v7 .ps source grammar.
-/

def twice (n : Nat) := n + n
def zero (_unit : Unit) : Nat := 42
private def privateNext (n : Nat) := n + 1
def triple (n : Nat) := n + n + n
def keep {α : Type} [Inhabited α] (x : α) := x

def choose (n : Nat) [Decidable (n = 0)] (x : Fin (n + 1)) : Nat := x.val
def select {α : Type} (x : α) [Inhabited α] (y : α) : α := x
def retain ⦃α : Type⦄ (x : α) : α := x

theorem nativeChooseCorrect (n : Nat) [Decidable (n = 0)]
    (x : Fin (n + 1)) : choose n x = x.val := by rfl
theorem nativeKeepCorrect {α : Type} [Inhabited α]
    (x : α) : keep x = x := by rfl
theorem nativeNullaryUnit : zero () = 42 := by rfl
