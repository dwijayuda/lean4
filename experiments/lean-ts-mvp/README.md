# Lean 4.35.0-rc4 → TypeScript 7.0.2 MVP

A deliberately tiny, out-of-tree Lean-to-TypeScript experiment. It uses the original Lean parser, elaborator, tactic engine, and kernel to check the source. A Lean command translates a restricted set of elaborated Nat definitions into TypeScript. The official TypeScript 7.0.2 compiler produces portable Node.js ESM.

This is not an LCNF backend and does not prove generated JavaScript correct.

## Try the complete pipeline

Install elan, Node.js 22+ and npm. From this folder (not the Lean4 root), run:

    lake build LeanTs
    lake env lean Example.lean > lean-emit.log
    node publish.mjs lean-emit.log
    npm install --ignore-scripts --no-audit --no-fund --no-package-lock
    npm run build
    npm test

The source-level Lean theorems are checked before invoking the export commands. The compiler emits generated/increment.ts, generated/square.ts, generated/saturatingSub.ts; TypeScript emits dist/*.js and dist/*.d.ts. Node tests cover large integers, saturation, and JS boundary validation.

## Negative tests

The following commands must both fail. No corresponding output file may appear:

    ! lake env lean Reject.lean
    ! test -e generated/unsupported.ts
    ! lake env lean BadProof.lean
    ! test -e generated/afterBadProof.ts

The GitHub Actions workflow automates these checks.

## Explicitly supported subset

Only safe, unqualified, top-level Lean definitions with Nat arguments and a Nat result. Expressions may use Nat.add, Nat.mul, Nat.sub, Nat.succ, natural-number literals, and bound parameters. Generated functions use JavaScript bigint, saturating subtraction, and runtime checks that reject negative and non-bigint Nat inputs.

All other executable Lean constructs must fail explicitly. The Lean host still supports its ordinary syntax, definitions, and tactics for proving theorems, because these do not need translation into TypeScript.

## Trust and limitations

This uses Lean's original kernel to check Lean declarations and proofs. It does not formally verify translation semantics, the official TypeScript compiler, the Node runtime, or JavaScript callers. Lean sorry and nonstandard axioms are not automatically audited by this tiny emitter.

The command writes framed TypeScript to stdout, not to files. The publish.mjs step runs only after Lean returns a successful exit code, validates all output blocks, and atomically renames each staged file. A failed Lean proof therefore blocks publishing. Do not invoke publish.mjs on output from a failed Lean command. This checks build-process success but does not formally verify generated JavaScript or audit all axioms. Other limitations include lack of recursion, higher-order functions, polymorphism, effect handling, arrays, and external Lean functions.

The logical next backend milestone is extracting actual base/mono-LCNF and implementing explicit TS runtime lowering without changing the Lean frontend or kernel.
