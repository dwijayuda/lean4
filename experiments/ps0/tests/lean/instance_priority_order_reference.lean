-- Native Lean selection oracle. No PSCV0 restrictions on this .lean file.
class PreferredNative where
  value : Nat
instance (priority := low) : PreferredNative where
  value := 11
instance (priority := high) : PreferredNative where
  value := 99
theorem selectedPriority : (inferInstance : PreferredNative).value = 99 := by rfl
