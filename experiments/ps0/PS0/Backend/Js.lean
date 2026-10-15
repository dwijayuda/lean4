import PS0.Backend.Js.Lower
import PS0.Backend.Js.Emit

/-!
PS0 JS backend public imports. The pipeline is:
  checked .ps frontend → selected typed runtime IR → deterministic emitter
  → ESM JS / .d.ts / source-map v3.

Additional backends can share or extend the typed portable IR without
depending on a JavaScript runtime or introducing an independent kernel.
-/
