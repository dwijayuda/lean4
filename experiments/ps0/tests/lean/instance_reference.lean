-- Full native Lean, no PSCV0 syntax restrictions.
class AnonymousBox where
  number : Nat

instance : AnonymousBox where
  number := 23

class NamedBox where
  number : Nat

instance chosen : NamedBox where
  number := 29

theorem anonymousBoxNumber :
    (inferInstance : AnonymousBox).number = 23 := by rfl
theorem namedBoxNumber : chosen.number = 29 := by rfl

-- Native value-form instances remain legal in unrestricted .lean.
class NativeValueForm where
  value : Nat
instance : NativeValueForm := { value := 31 }
theorem nativeValueInstance : (inferInstance : NativeValueForm).value = 31 := by rfl
