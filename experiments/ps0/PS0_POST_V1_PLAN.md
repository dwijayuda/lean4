# PS0 post-V1 milestone: release consumption and application qualification

## Qualified baseline

V1-100 is PASS at compiler source `156524fc660dbd6db8fbc4a5845d5a2d486860c3`, pinned Lean `eb6cafb7290e8bd5f2937522d8d804f58f02bafc` (4.35.0). [Qualification run 43750175058](https://github.com/dwijayuda/pskernel/actions/runs/43750175058) passed all 12 Linux jobs over 2,569 canonical .ps modules. [Qualification records](CONFORMANCE.md) and [structured coverage](v1-coverage.json) retain the exact evidence.

The source and CI changes were merged in [Lean PR #21](https://github.com/dwijayuda/lean4/pull/21) and [PSKernel PR #263](https://github.com/dwijayuda/pskernel/pull/263).

The next milestone is **PENDING**. Completion of the 242 recorded V1 obligations is not language-wide conformance, byte-identical final ELF output, completed grammar migration, or verified execution.

## Published qualified release

[Versioned Linux release](https://github.com/dwijayuda/pskernel/releases/tag/ps0-v1-qualified-lean4.35.0-156524fc-linux-x86_64) is published. [Publication run 43835228088](https://github.com/dwijayuda/pskernel/actions/runs/43835228088), Linux job [133190063024](https://github.com/dwijayuda/pskernel/actions/runs/43835228088/job/133190063024), passed after checking all 12 qualification jobs, original artifact archive hashes, the independent receipt hash, and the retained stage-two prefix. [Publication receipt artifact 14209698710](https://github.com/dwijayuda/pskernel/actions/runs/43835228088/artifacts/14209698710): 3,163 bytes, `sha256:8a0903f8fa783b82e8504c751fc14d491341730ecd68aaffa80a5b5476fb3516`.

| Asset | Release asset ID | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Bootstrap ZIP | 754138534 | 285576940 | `cef1a778bf408e593e735ce51468967fb795f8a936fc434ccb39e7e8a3cdf283` |
| Independent audit ZIP | 754138532 | 655 | `7b3a22fbea17139916a72c24ffc5532bbc84c259d2af3ba0fe76658a1800bc5e` |
| audit.json | 754138530 | 1001 | `a60a100c22da0a96f29489e0082ed75f24d4560722423ccc2a196850179bb217` |
| release-manifest.json | 754138537 | 3684 | `e9d9b87dd5fae11f6508b2d94e51e0a99430ba4e6e0c4db1b49889b7040eb614` |
| SHA256SUMS | 754138536 | 370 | `fc2b6e74a31a055fa6ecc9fe0ebc478199b8c19517afcfcb4f1813299e493c1a` |

Download all five assets, verify SHA256SUMS against its recorded hash, then run `sha256sum -c SHA256SUMS` before extracting. The bootstrap is the unchanged qualified stage-two archive, including its compiler prefix and metadata. The prior bootstrap remains the default seed until the adoption criteria below pass.

## Goal

Make the qualified Linux bootstrap reproducibly consumable and establish a small, explicit application and operational test baseline. Keep compiler changes driven by demonstrated failures.

## Work and acceptance criteria

| Work item | Required evidence before PASS |
| --- | --- |
| Release consumption | A fresh Linux job downloads the versioned release, checks every asset against SHA256SUMS, verifies the manifest, source and Lean identities, rehashes the retained prefix, and exercises relocated compiler operation. Record exact release asset, job and receipt identities. |
| Bootstrap adoption | Qualify a clean canonical two-stage run using the new published bootstrap as the first-stage seed, followed by the independent audit. Preserve the prior seed and its receipts; change the default fetch pin only after this replacement succeeds. |
| Representative applications | Freeze a compact suite covering a multi-module library/consumer, a command-line IO program, a data/recursion program, and an imported user-syntax extension. Each case needs source hashes, an explicit semantic/runtime oracle, Linux CI results and retained outputs. |
| Diagnostic stability | Add malformed counterparts for those programs with exact expected diagnostic categories and source locations. Preserve native .lean handling and deliberate imported-syntax ownership boundaries. |
| Performance baseline | Record compiler wall time and peak RSS for the frozen suite and canonical build on a documented Linux runner/toolchain. Retain measurements as a baseline; make no speedup claim without comparable measurements. |
| Grammar ownership review | Inventory compatibility and native-adapter paths exercised by the suite. Distinguish intentional native-language boundaries from uncovered PS0 ownership obligations. Add focused tests before changing any mechanism. |

## Claim boundaries and reporting

Use a separate post-V1 evidence record; do not inflate the existing V1 total. Mark each new work item PENDING until its own exact CI evidence exists. A test suite establishes only its stated finite scope.

Continue comparing producer C/public-olean receipts separately from independent rehashes of retained files. Keep `grammar_migration_complete=false` and `verified_execution=false` until separate evidence justifies stronger claims. Backend semantic preservation and formal execution verification are later milestones.

## Execution order

1. Publish and verify the immutable qualified release.
2. Qualify release consumption and relocated operation in a fresh Linux job.
3. Run clean two-stage qualification from the new seed before changing default bootstrap pins.
4. Freeze the application/diagnostic suite and performance measurements.
5. Review demonstrated gaps and select the next implementation family.

This plan records future work; it does not claim that these acceptance criteria have passed.
