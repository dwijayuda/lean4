import Std.WP

/-!
PSCVL v0 effect relations, inside Lean's single logic.

These definitions give precise propositions about *actual* result, input
reader/state and typed exception paths. They introduce no axioms and do not
silently certify world effects (IO/FFI) or backend code generation.

Lean's pinned Std.WP supplies the primary WPMonad semantics and checked
monotonicity/pure/bind laws for Id, ReaderM, StateM and Except. These explicit
relational views are useful for checking PSCV effect obligations in .ps proofs,
without inventing any second logic or confusing tests with verified evidence.
-/

namespace PSCVL.Effect

open scoped Std.WP Lean.Order

universe u v

/-- A pure computation's weakest precondition is its requested postcondition. -/
def pureWP {α : Type u} (value : α) (post : α → Prop) : Prop :=
  post value

@[simp] theorem pureWP_apply {α : Type u} (x : α) (post : α → Prop) :
    pureWP x post ↔ post x := Iff.rfl

/-- A read-only computation is specified at an explicit, unchanged environment. -/
def readerWP {ρ α : Type u} (prog : ReaderM ρ α)
    (post : α → ρ → Prop) (env : ρ) : Prop :=
  post (prog env) env

@[simp] theorem readerWP_pure {ρ α : Type u} (x : α)
    (post : α → ρ → Prop) (env : ρ) :
    readerWP (pure x : ReaderM ρ α) post env ↔ post x env := Iff.rfl

theorem readerWP_bind {ρ α β : Type u} (prog : ReaderM ρ α)
    (k : α → ReaderM ρ β) (post : β → ρ → Prop) (env : ρ) :
    readerWP (prog >>= k) post env ↔
      readerWP prog (fun value original => readerWP (k value) post original) env := Iff.rfl

/-- Typed error contracts distinguish the successful and exceptional branches. -/
def errorWP {ε α : Type u} (prog : Except ε α)
    (ok : α → Prop) (failed : ε → Prop) : Prop :=
  match prog with
  | .ok value => ok value
  | .error err => failed err

@[simp] theorem errorWP_ok {ε α : Type u} (x : α)
    (post : α → Prop) (errPost : ε → Prop) :
    errorWP (.ok x) post errPost ↔ post x := Iff.rfl

@[simp] theorem errorWP_error {ε α : Type u} (e : ε)
    (post : α → Prop) (errPost : ε → Prop) :
    errorWP (.error e) post errPost ↔ errPost e := Iff.rfl

theorem errorWP_bind {ε α β : Type u} (prog : Except ε α)
    (next : α → Except ε β) (post : β → Prop) (errPost : ε → Prop) :
    errorWP (prog >>= next) post errPost ↔
      errorWP prog (fun x => errorWP (next x) post errPost) errPost := by
  cases prog <;> rfl

/-- Stateful contracts preserve explicit logical pre-state rather than
conflating a mutation with an ambient host-memory side effect. -/
def stateWP {σ α : Type u} (prog : StateM σ α)
    (post : α → σ → Prop) (initial : σ) : Prop :=
  let (value, final) := prog.run initial
  post value final

@[simp] theorem stateWP_pure {σ α : Type u} (x : α)
    (post : α → σ → Prop) (initial : σ) :
    stateWP (pure x : StateM σ α) post initial ↔ post x initial := Iff.rfl

/-- The relational form of a state effect's postcondition. The first
state is 'old' / pre-state, the second the actual produced post-state. -/
def stateRel {σ α : Type u} (prog : StateM σ α)
    (pre : σ → Prop) (post : σ → α → σ → Prop) : Prop :=
  ∀ old, pre old →
    let (value, newState) := prog.run old
    post old value newState

/-- A frame obligation over an explicitly selected observation. Proof of this
relation does not establish a full modifies/reads capability registry. -/
def preserves {σ α β : Type u} (prog : StateM σ α) (view : σ → β) : Prop :=
  ∀ before, view (prog.run before).2 = view before

/-- A checked frame lemma is an ordinary theorem about observable state. -/
theorem preserves_pure {σ α β : Type u} (x : α) (view : σ → β) :
    preserves (pure x : StateM σ α) view := by
  intro before
  rfl

/-- The PSCVL pure relation is definitionally equivalent to the pinned
Lean `Std.WP.wp` interpretation; it is not a parallel semantic authority. -/
theorem pureWP_pinned {α : Type u} (value : Id α) (post : α → Prop) :
    pureWP value post ↔ Std.WP.wp value post () := Iff.rfl

/-- Kernel-checked correspondence to Lean 4.35 ReaderM weakest preconditions. -/
theorem readerWP_pinned {ρ α : Type u} (prog : ReaderM ρ α)
    (post : α → ρ → Prop) (env : ρ) :
    readerWP prog post env ↔ Std.WP.wp prog post () env := Iff.rfl

/-- Kernel-checked correspondence to Lean 4.35 StateM weakest preconditions. -/
theorem stateWP_pinned {σ α : Type u} (prog : StateM σ α)
    (post : α → σ → Prop) (initial : σ) :
    stateWP prog post initial ↔ Std.WP.wp prog post () initial := Iff.rfl

/-- Kernel-checked correspondence to Lean 4.35 Except weakest preconditions,
including distinct success and error postconditions. -/
theorem errorWP_pinned {ε α : Type u} (prog : Except ε α)
    (ok : α → Prop) (failed : ε → Prop) :
    errorWP prog ok failed ↔ Std.WP.wp prog ok failed := by
  cases prog <;> exact Iff.rfl

end PSCVL.Effect
