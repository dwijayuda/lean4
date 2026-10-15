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

// Semantically equivalent to braced PSCV0 parametric instance source.
class DefaultBox (α : Type) where
  fallback : α
instance {α : Type} [Inhabited α] : DefaultBox α where
  fallback := default

class IdentityBox (α : Type) where
  identity : α → α
instance selected {α : Type} : IdentityBox α where
  identity := fun x => x

theorem defaultBoxNat : (inferInstance : DefaultBox Nat).fallback = 0 := by rfl
theorem identityBoxNat : selected.identity 4 = 4 := by rfl
