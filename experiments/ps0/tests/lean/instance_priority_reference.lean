-- Official Lean native 4.35.0 priority and typeclass elaboration.
class ChosenPriority where
  value : Nat
instance (priority := high) : ChosenPriority where
  value := 73

class NumberPriority where
  value : Nat
instance (priority := 750) chosenNumber : NumberPriority where
  value := 75

class GenericPriority (α : Type) where
  value : α
instance (priority := low) {α : Type} [Inhabited α] :
    GenericPriority α where
  value := default

theorem highSelected : (inferInstance : ChosenPriority).value = 73 := by rfl
theorem numericSelected : chosenNumber.value = 75 := by rfl
theorem genericSelected : (inferInstance : GenericPriority Nat).value = 0 := by rfl
