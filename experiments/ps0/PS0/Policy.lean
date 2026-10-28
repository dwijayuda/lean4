import Lean
import PS0.Syntax

/-!
PS0 v1 distinguishes language acceptance from explicit assurance claims.

Native Lean 4.35.0 may elaborate safe, unsafe, partial, axiomatic,
noncomputable, metaprogramming and effectful source. A source construct
is not banned merely because a stronger, separately requested proof
claim would fail. This module is an *informational* evidence command,
NOT a verification certificate or trusted source extension sandbox.
-/

open Lean Elab Command

namespace PS0

syntax (name := ps0Evidence) "#ps0_evidence" : command

/-- Report local declaration classifications, without silently accepting
    axioms as an approved trust foundation or declaring runtime correctness.
    Explicit theorem/assumption/effect claims must use a supplied policy
    and their true transitive dependency closure per PS0 v1 §12. -/
@[command_elab ps0Evidence]
def elabPs0Evidence : CommandElab := fun _ => do
  let locals ← (← getEnv).getLocalConstantInfos
  let mut axioms : Nat := 0
  let mut unsafeDecls : Nat := 0
  let mut partialDecls : Nat := 0
  for c in locals do
    let info := c.toConstantInfo
    if let .axiomInfo _ := info then
      axioms := axioms + 1
    if info.isUnsafe then
      unsafeDecls := unsafeDecls + 1
    if info.isPartial then
      partialDecls := partialDecls + 1
  logInfo m!"PS0 v1: {locals.size} local declarations; {axioms} declared axioms; {unsafeDecls} unsafe; {partialDecls} partial"
  logInfo "PS0 v1: assumption policy NOT assessed; source specification NOT assessed; execution correspondence NOT established; no verified certificate issued"

end PS0
