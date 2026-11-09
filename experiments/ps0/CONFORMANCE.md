# PS0 v1 — Implementation and Conformance Ledger

## Owned lambda operands and exact compiler output — Linux PASS

Qualified source **7f885fcc1caa9277e3633c849d086bb2614e143e**, runner **be50016de092e47d1df9306aac8a941ef6b49bf4**, [run 42537205963](https://github.com/dwijayuda/pskernel/actions/runs/42537205963): **all four jobs PASS** — project **128904045087**, native **128904044934**, proof-linked **128904044798**, host **128904044594**.

**PS0_LAMBDAS:3:3:3:3:3:3:2:3:3:3:3** and **PS0_LAMBDA_OPERANDS: PASS** cover typed/grouped/untyped, implicit/strict/instance binders, native tuple/Unit patterns, overall type annotation, Unicode lambda spelling and owned lambda type/body calls. Native binder/pattern/lambda elaboration remains Lean's; declaration default/comma rules are not substituted for lambda grammar. Body/type call-gap and argument-order diagnostics pass; native quotations remain native. **psFunBinder** host registration is cloned with the other finite categories for prelude compilation without hidden target PS0 logical imports.

The native source census additionally records **only direct single-body lambda argument roots** of actual source value applications. The planner edits such body calls **only when the containing root call is itself adapted**, preserving unrelated/quoted/DSL data. In pinned **Lean.Compiler.LCNF.DeclHash** (**5f818560cb8fcba0df6f64acb6bdc01c48425189**), **hashAlts** now adapts the actual lambda-body **mixHash** call as well as its containing **foldl** call. The original lambda/pattern elaborator and parenthesized argument nodes are retained.

- **18 byte edits**; original source SHA-256 **b91bd09cd5fbf9f0def82b12c7ef5d2c5c5465f55edfeec8ad59a640f0b5d1d0**; PS SHA-256 **b74e88c4932b629b61d788d5cdab675b6629ef4819360e34a8d3e83a3226c0d6**.
- Original lambda body application range **742..763**, function **742..749**, arguments **750..751** and **752..763**; ranges come from Lean's actual original frontend syntax.
- Native/PS C SHA-256 **9611a2b34cb41baebe563bfc8ceee525819636d71ec7228d7f0c552184055d4c**; public olean SHA-256 **103a0395c4808e7a0b2cbe5fa9e9bbd27392d18312c2a25235d1a9470a9308fb**. Strict byte comparisons remain unchanged.
- All **15 converted heads / four actual compiler modules**, registered owned-term macros and relocated SDK-backed host regressions retain PASS.

[Project artifact 13639793140](https://github.com/dwijayuda/pskernel/actions/runs/42537205963/artifacts/13639793140), ZIP SHA-256 **291e677ea6ebf2443116cceb8297eada2598b869a3dc00311c37af4807e3dc5d**. Native artifact **13640081217**, SHA-256 **e16c9661c1cb6673494ced57debca47c67945075941face796b4b3ccd339ff01**; proof artifact **13639599095**, SHA-256 **7a24d76eacd2d9027808f915ac3b025a3f00650a366be34ab4c40ec1604438a0**. [Independent inspection 42537641040](https://github.com/dwijayuda/pskernel/actions/runs/42537641040), runner **7dfe7c6b0fd7e2d8d54dfd8c884585a8fa33cfea**, job **128905384499 PASS**, verifies all four module comparisons, the exact 18-edit plan and original lambda body role.

Test-first run **42536259326 / 128901122247** fails before the adapter; first implementation **42536727424 / 128902548521** retains all compiler parity but its fixture also used unrelated unsupported call-left arrow syntax, legacy reserved **unicode(** spelling and a nonadjacent **MacroM** type application. The revised fixture isolates lambda operands; these broader parser/lexer roles are not promoted to completion. Both failed source/runner/artifact identities remain in the ledgers.

## Fresh .ps-built compiler host — stage one PASS, stage two IN PROGRESS

Separate exact source **2cba0bc26df49c52d653598fd9c791f23209199c**, runner **b83ebb191c21c0985c9dc6df3a4cca11ae31e121**, [run 42532849633](https://github.com/dwijayuda/pskernel/actions/runs/42532849633): prerequisite jobs all PASS, compiler stage one **128891725901 PASS**. **2,567 modules / 5,138 native Lake jobs** build and link the .ps source forest. The resulting executable and **200 host metadata files freshly compiled from that forest** pass the relocated missing-host negative, PS prelude compile/link/runtime, stage-option and no-hidden-import probes.

Driver SHA-256 **4ecf775dbb7b4d275bccd679463cbd805f5d618d9bb350b57c1baa94dcc4a2e9**; raw native-host evidence SHA-256 **1afb8cf6db63bcfb98618e214641bcdf1f75efe66dd82cf4216eba79c3e590f1**; sorted JSON host metadata manifest SHA-256 **6fada1ca81b868b0c5aec19c299a4416e241afb8785e35a573e5f9980d3b4fb6**. [Stage-one artifact 13639457688](https://github.com/dwijayuda/pskernel/actions/runs/42532849633/artifacts/13639457688), ZIP SHA-256 **13f7e3b9c10878b503a7458a158af6e661ece4e4e7c8edb8fd1bab155117ed3b**. [Inspection 42537298767](https://github.com/dwijayuda/pskernel/actions/runs/42537298767), runner **4fc9653592b931653be89036cd614719516e260a**, job **128904326108 PASS**, verifies those identities, 200 metadata pairs and the native-compatible source census.

This earlier forest has **72,797 native-compatible selected rows / zero mapped PS rows**. Stage two **128901327549 IN PROGRESS** will require the same fresh host checks and strict all-module C/public-olean fixed point. It neither completes canonical grammar conversion nor qualifies this newer lambda/macro head. The earlier fixed point at source **28904e5a7ccb19a15e311ecc654541dc0ee639ec** remains separate.

Goal **ACTIVE / NOT COMPLETE**. Remaining owned operator/layout/field/constructor/local-declaration contexts, complete checked source conversion, full current-head bootstrap and diagnostic/IDE fidelity remain open. All 242 broad obligations remain PENDING; no trust/reference pin or exact-output gate is relaxed and no verified-execution certificate is issued. Earlier pending lambda and stage-one notes below are superseded by these exact finite results.


## Registered owned term macros — native Lean dispatch PASS

Qualified source **b6e9671252219e63a4bda7b8df70017b90145ff1**, runner **167f9607a5507f86dc69197db10598739066e6bb**, [Linux run 42534811062](https://github.com/dwijayuda/pskernel/actions/runs/42534811062): **all four jobs PASS** — project **128896644458**, native **128896644569**, proof-linked **128896644297**, host **128896644480**.

The owned **psTerm** boundary now calls pinned **Lean.Macro.expandMacro?** for registered unknown nodes, then recursively lowers the resulting owned syntax. **Lean.Macro.withIncRecDepth** supplies native recursion bounds. The native dispatcher retains fresh scopes and normal macro attributes; no separate macro evaluator, typechecker or kernel is introduced.

**PS0_OWNED_MACROS:8:6** and **PS0_OWNED_TERM_MACRO_EXPANSION: PASS** cover nested registered macros, hygiene against a local binder named **add**, native checking/C/object/link/runtime, original macro-argument **PS0V1-CALL-GAP**, expanded argument-list **PS0V1-CALL-ORDER**, native **maximum recursion depth** and **PS0V1-HOST-LOWER** for an unowned expanded node. The suite uses native explicit antiquotation category annotations and escaped syntax-kind identifiers. It does not qualify every macro category or arbitrary generated syntax/text correspondence.

[Project artifact 13638129268](https://github.com/dwijayuda/pskernel/actions/runs/42534811062/artifacts/13638129268), ZIP SHA-256 **f317a1cdadf2f87441285e6a95520c910dc354acaa900a644c59205d71bae75c**. Native artifact **13638484712**, SHA-256 **ea94ecc8fe9bdb8cb6c97c84ba0fad80cb28988ba11fa361ef798896a1e4b03b**; proof-linked artifact **13638163978**, SHA-256 **d39aeafcf1c105e256d93fe89a5d03028b3c70eb3caae2139fd89cc1c96b4d16**. Exact failed source/runner/job/artifact evidence is retained in both JSON ledgers: test-first **42533778399 / 128893486047**, then dispatch-positive but cycle-fixture failing **42534400476 / 128895393134**.

The same passing run retains **all 15 converted compiler heads / four modules** with strict C/public-olean parity, mixed/default/nested-command/quoted-source tests and the SDK-backed relocated native grammar host. The separate full compiler integration **42532849633**, source **2cba0bc26df49c52d653598fd9c791f23209199c**, runner **b83ebb191c21c0985c9dc6df3a4cca11ae31e121**, has **all four prerequisite jobs PASS** and compiler stage one **128891725901 IN PROGRESS** as last checked. Its fresh .ps-built grammar host and stage-two fixed point are **not qualified yet**; this older pin does not qualify the newer macro implementation.

Goal **ACTIVE / NOT COMPLETE**. Complete source conversion and remaining owned operand roles, including richer lambda/operator/layout/field/constructor contexts, plus full diagnostic/IDE fidelity, remain open. All 242 broad obligations remain PENDING; no verified-execution certificate is issued.


## Fresh .ps-built compiler grammar-host integration — IN PROGRESS

Candidate source **2cba0bc26df49c52d653598fd9c791f23209199c**, runner **b83ebb191c21c0985c9dc6df3a4cca11ae31e121**, [run 42532849633](https://github.com/dwijayuda/pskernel/actions/runs/42532849633), [runner PR234](https://github.com/dwijayuda/pskernel/pull/234). Each full native-compatible compiler stage now additionally tests a relocated executable with **PS0 host metadata freshly compiled from its .ps source forest**, retaining the missing-host negative, native Lake PS prelude compile/link/runtime, no-hidden-import checks, compiler-stage options and host manifest. SDK metadata dependencies remain explicit. Stage two retains the all-module strict C/public-olean fixed-point gate. **This integration has not passed yet**; the source forest remains native-compatible, and the entire-corpus PS grammar goal remains ACTIVE / NOT COMPLETE.

The previously qualified 15-head/mixed/default/source-fidelity and SDK-backed native-host checkpoints below remain exact source **7fea6986042ba76fd1f1a028474209dc5f3bc519**. The earlier full native-compatible fixed point remains source **28904e5a7ccb19a15e311ecc654541dc0ee639ec**. Neither result is promoted to this newer candidate.


## Mixed/default compiler heads and native grammar host — Linux PASS

Qualified source **7fea6986042ba76fd1f1a028474209dc5f3bc519**. The mixed/default runner **af8cba4c485081ae3feaaf78607783d3586561d9**, [run 42531956835](https://github.com/dwijayuda/pskernel/actions/runs/42531956835), passes **all four jobs**: project **128887883496**, native **128887883501**, proof-linked **128887883492**, host **128887883581**. Expanded native-host runner **ed686af4624a721be79dc67be6f0c2e3e53389ce**, [run 42532092264](https://github.com/dwijayuda/pskernel/actions/runs/42532092264), also passes **all four jobs**: project **128888301265**, native **128888301253**, proof-linked **128888301071**, host **128888301397**.

**15 converted heads across four actual pinned compiler modules** now pass fresh native Lake compilation, native-only rejection and **byte-identical C/public olean** comparisons. The new **ScopeM** blob **5bc78059af7e9f16d980688c88c3eaeecae3ab1a** converts seven heads, including two instance telescopes and two source-parameterless **const** aliases. Its unchanged native **abbrev ScopeM** also reaches the PS adapter and is accounted for separately. The new **OtherDecl** blob **a09e23d6f39bb7e87e7a5b10c2f0fc7556575cd4** converts **getOtherDeclType**, retaining the typed **us : List Level := []** default and ordered parameters. Existing three ClosedTermCache and four recursive DeclHash heads retain strict parity.

| Actual module | Identical C SHA-256 | Identical public olean SHA-256 |
|---|---|---|
| Lean.Compiler.ClosedTermCache | `7d54fb41d97e4be6bd11497a5919f5ee35f87643befc481a135d2cf6365494d2` | `f772b02fde1d5ebc4117d53d6bd7aeeb15e5131c53329adf0b3b7ea623f4467e` |
| Lean.Compiler.LCNF.DeclHash | `9611a2b34cb41baebe563bfc8ceee525819636d71ec7228d7f0c552184055d4c` | `103a0395c4808e7a0b2cbe5fa9e9bbd27392d18312c2a25235d1a9470a9308fb` |
| Lean.Compiler.LCNF.OtherDecl | `a7374e6b1908187a18e4343b31c0d53a2dc4dec852b99b63e7770fe7074cdc3b` | `5ef05c49d8b84529d1e37e70b4d5c3f52f26ddbe27a97a71c402ff341a408f5b` |
| Lean.Compiler.LCNF.ScopeM | `0a149b683a22ff893a4631811a531bb483b19ef7845b036be8e7dbdd5be0de39` | `5e79495ce517159a2850bf5b9cb0ea1f530fca39f568672584a881dcb7ad36b7` |

ScopeM uses **10 explicit edits**; OtherDecl uses **3**, preserving instance/default/body bytes. ScopeM original/PS SHA-256: **555ea12e6be42a5e9be8eb3a22dc1d0dbc2ae748fcc7a971da7f63e23b64642a** / **a65dcf24c7f952ce4967e3cac79e371ee856eb48c392e3df598a08159af67577**. OtherDecl original/PS SHA-256: **cb137113a603520d0553a2d5553f60f1c66425a5a79613edade23b45c7a5fd95** / **5ffbf652349ac67a63e8e10aeb132db5c1511ab140186ac88b4b3428ced00649**. The original native declaration and quoted/DSL interiors are observed through Lean, not a second source parser. Unsupported shared/inferred/implicit/default shapes remain fail-closed in this finite planner.

**PS0_BINDER_LEXICAL_FIDELITY: PASS** also directly checks legacy native strict-binder lowering and identifier/type SourceInfo equality for ASCII/Unicode forms, alongside nested records and native quotations. Its modern test fixture publicly imports the category provider and uses native **import all** for the private helper; no compiler visibility rule is changed.

**PS0_RELOCATED_GRAMMAR_HOST: PASS**: a copied executable first fails without its host metadata, then succeeds with byte-preserved native metadata in **bin/../lib/lean**. Relocated prelude compilation, static linking, runtime **PS0_PRELUDE_GRAMMAR:42:3**, stage options and original-source/import checks pass. No hidden target PS0 logical import is added. This package uses explicit pinned SDK dependencies and **98 host metadata files / 32 IR files**. Driver SHA-256 **d3e0f57841d389836bf8400bf24386d57e88e3a86b1b20c9fd9339003953f068**; canonical sorted metadata manifest SHA-256 **89ee3505ae77f92ac11d7d93d33f7b3bdb65bc86f96eef781fcce166c752d6b0**. This is the SDK-backed host package; the fully .ps-built compiler host remains the next integration check.

[Independent inspection 42532451421](https://github.com/dwijayuda/pskernel/actions/runs/42532451421), runner **0da9b2bc17077b3c237bd4ab377fad06edaeaa45**, job **128889408555 PASS**, verifies exact module/source hashes, native comparisons, retained edit plans and host manifest. [Mixed/default artifact 13637936782](https://github.com/dwijayuda/pskernel/actions/runs/42531956835/artifacts/13637936782), ZIP SHA-256 **12cc0c080d2e5b5e07559278a0b91d7533643ecfe0ba3131fa698bbcd62bbdc5**. [Expanded native-host artifact 13637607576](https://github.com/dwijayuda/pskernel/actions/runs/42532092264/artifacts/13637607576), ZIP SHA-256 **9ada1694e4ac3d252fa7bd904319e6630d534190d5e56227dd901654cb9321bc**. All native/proof artifact IDs and digests, test-first planner failures and resolved harness failures remain in both JSON ledgers.

The earlier full native-compatible **2,567-module / 5,138-job** per-stage fixed point at source **28904e5a7ccb19a15e311ecc654541dc0ee639ec** remains qualified separately in **run 42522976977** with all six jobs PASS and zero C/public-olean differences. It has **72,792 native-compatible selected rows / zero mapped PS rows** and does not qualify this later head. Goal **ACTIVE / NOT COMPLETE**: remaining owned grammar roles, complete checked source conversion, fully migrated grammar-host bootstrap and source diagnostic/IDE fidelity remain open; all 242 broad obligations remain PENDING, and no verified-execution certificate is issued. Earlier ScopeM/default/host pending notes below are superseded by this finite result.


## Native strict-binder lexical fidelity — Linux PASS

Exact source **dce75d401549cad585c5a4481f52435d34a7e373**, runner **88e102880840f20c1f4f56b274ab5e0aa49ad443**, [run 42529792319](https://github.com/dwijayuda/pskernel/actions/runs/42529792319): **all four jobs PASS** — project **128881238870**, native **128881239010**, proof-linked **128881238753**, host **128881238995**. Native host imports now retain adjacent nested-record closing braces, ASCII/Unicode strict binders and native quotations. Legacy strict binder parsing reuses pinned **strictImplicitLeftBracket / strictImplicitRightBracket**, so no global double-brace tokens are added. **PS0_BINDER_LEXICAL_FIDELITY: PASS**; the two actual compiler module probes retain strict C/public-olean parity.

The test-first source **cce3ee56a28d4eeb178880f280d1d10f15b2e64a**, runner **9a29e03ff72dcf480987b24c36bb5b81cd72e543**, [run 42529389473](https://github.com/dwijayuda/pskernel/actions/runs/42529389473), project **128879992043**, reports native record/quotation errors at global tokens **`}}`** and **`{{`**. The test also corrects its native Type syntax-kind assertion to the pinned **Lean.Parser.Term.type**.

[Project artifact 13637016958](https://github.com/dwijayuda/pskernel/actions/runs/42529792319/artifacts/13637016958), ZIP SHA-256 **a98bc40efc7225f40cf0fa83040703aeaa8daab42ca40b2ad572551b04481907**. Native artifact **13636129219** SHA-256 **e116c4293e0a4d8829877402a49eeb00bac6c73560990ec5051783072b593801**; proof-linked artifact **13636991243** SHA-256 **525f3026398741dcd61e3436ef3095a30e5e8e1ff62ba3963b91b72b36b92988**.

The full earlier native-compatible compiler fixed point is independently inspected in [run 42529625243](https://github.com/dwijayuda/pskernel/actions/runs/42529625243), runner **e0dfe5129dcb0fd1c591cca8f687a7dc05ba5f42**, job **128880736870 PASS**. Stage-two migrated executable SHA-256 **f859aba1628208d75527c51d5012b7135cb3d01a321716633d1905f5ee450e7a**; changed C/public-olean arrays are both empty. This remains a native-compatible source forest, not full canonical grammar migration.

Next finite mixed-instance/value source probe: [source PR15](https://github.com/dwijayuda/lean4/pull/15), [runner PR232](https://github.com/dwijayuda/pskernel/pull/232), exact pinned **Lean.Compiler.LCNF.ScopeM** blob **5bc78059af7e9f16d980688c88c3eaeecae3ab1a**. Its seven source heads include instance telescopes and two named values. Qualification is **PENDING**; no ScopeM parity claim yet. The direct legacy-lowering test is also being extended. Goal **ACTIVE / NOT COMPLETE**.


## Full native-compatible compiler fixed point — Linux PASS

Exact source **28904e5a7ccb19a15e311ecc654541dc0ee639ec**, runner **484868307c6611fedf1a464e2e102c02b8ad5855**, [run 42522976977](https://github.com/dwijayuda/pskernel/actions/runs/42522976977): **all six jobs PASS**, including compiler stage one **128861032581** and stage two **128870983007**. Each stage builds **2,567 modules / 5,138 native Lake jobs** through native C/object/static-library/executable compilation and linking. The stage-one migrated executable rebuilds the same .ps source forest; **zero generated C differences and zero public olean differences** across all modules. Migrated executable environment/source-check smoke and all-module source-census/origin joins pass in both stages.

The corpus is **2,546 exact pinned upstream source blobs plus 21 repository PS0 modules**. Its census contains **72,792 selected native-compatible rows / zero mapped PS rows** at this earlier source pin. This establishes the native-compatible rebuild foundation only; it does **not** establish entire-corpus ProofScript grammar conversion or qualify later commits automatically.

- Stage one artifact **13635566244**, ZIP SHA-256 **c4443462ef060abcbe8a4033f5f01325f7c9f91cc6ece84b5c8b3c14c4ad5be0**.
- [Stage two artifact 13636098822](https://github.com/dwijayuda/pskernel/actions/runs/42522976977/artifacts/13636098822), ZIP SHA-256 **6043382a9516a22672ff076c66d75f9ae6587cf4d0eb84d64fbc2f1a8ca0198d**.
- Native Lean option **interpreter.prefer_native=false** matches the pinned upstream stage build policy. No compiler/interpreter fork, trust relaxation or changed reference pin is used.

Goal **ACTIVE / NOT COMPLETE**. The separately qualified seven canonical PS heads in two actual compiler modules remain finite; remaining grammar roles, complete source conversion, relocated host metadata and source diagnostics/IDE fidelity remain open. Earlier “stage two IN PROGRESS” notes below are historical and superseded by this exact terminal result.


## Real recursive compiler PS conversion — strict native parity PASS

Qualified source **`3c47198c4ed8f43a4967deef199ea61fa5e8d592`**, runner **`d27b55627f50bbc4184839766994e286ae18af80`**, Linux [run 42528176757](https://github.com/dwijayuda/pskernel/actions/runs/42528176757): **all four jobs PASS** — project **128876309105**, native **128876308880**, proof-linked **128876309176**, host **128876309075**.

Pinned original logical module **Lean.Compiler.LCNF.DeclHash**, Git blob **5f818560cb8fcba0df6f64acb6bdc01c48425189**, now converts four typed heads (**hashParams**, **hashAlt**, **hashAlts**, **hashCode**) including recursive partial mutual members. Native frontend ranges also adapt two explicit binder type calls and the owned root `foldl` value call. Original argument nodes/bodies are retained. Native-only mode rejects the converted source; PS mode passes actual native Lake module compilation with **PS0_PINNED_COMPILER_HEADS_NATIVE_PARITY: PASS**.

- Native and PS C SHA-256: `9611a2b34cb41baebe563bfc8ceee525819636d71ec7228d7f0c552184055d4c`.
- Native and PS public olean SHA-256: `103a0395c4808e7a0b2cbe5fa9e9bbd27392d18312c2a25235d1a9470a9308fb`.
- Original file SHA-256: `b91bd09cd5fbf9f0def82b12c7ef5d2c5c5465f55edfeec8ad59a640f0b5d1d0`; converted PS SHA-256: `7c86fd067a0cee635c1f8e4309bb194a37e627ec9b835846b7d47f04142b7717`.
- The **15 explicit byte edits** are retained in the artifact plan. Native match/lambda interiors, quoted data and other commands remain byte-preserved.

The public-olean mismatch diagnosed below is **resolved** by preserving original parenthesized type-argument syntax within the new PS call delimiters. This retains the native macro-hygiene behavior. **No counter padding, output normalization, alpha-only replacement gate or weakened comparison was used.** Independent [evidence inspection 42528596494](https://github.com/dwijayuda/pskernel/actions/runs/42528596494), runner **`8740fd27279b5e6e81f41de0c08fe22e28b7e0cd`**, job **128877559131**, verifies exact source, C/public-olean hashes and plans.

The earlier **three ClosedTermCache heads also retain exact parity** in this same run. This is **seven real heads across two compiler modules**, including finite owned type/value roles. Native bodies are not generally canonicalized, SDK dependencies remain explicit, and entire-corpus ProofScript grammar migration is **not complete**.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| native | [13636555251](https://github.com/dwijayuda/pskernel/actions/runs/42528176757/artifacts/13636555251) | `8770926b1b8bc6a8d2d20ba2c86971ce9466e6871fe5e04d8b6eb9552f7defde` |
| external | [13636505902](https://github.com/dwijayuda/pskernel/actions/runs/42528176757/artifacts/13636505902) | `227421fe6234c1e9ae73ee502ee5aa2a85dd9046a6d3770c9a1ec4f8606c8011` |
| project | [13635874486](https://github.com/dwijayuda/pskernel/actions/runs/42528176757/artifacts/13635874486) | `faca612cbf2750609d67718d085459c1850d213dcab2ba78f10167851bee52c3` |

The independent full compiler/census [run 42522976977](https://github.com/dwijayuda/pskernel/actions/runs/42522976977) remains pinned to earlier source **28904e5a7ccb19a15e311ecc654541dc0ee639ec** / runner **484868307c6611fedf1a464e2e102c02b8ad5855**. Stage one **128861032581 PASS**, **2,567 modules / 5,138 native Lake jobs**, source/census join PASS; stage two **128870983007** remains **IN PROGRESS** as last checked. Its source forest remains native-compatible, not canonical PS. Goal **ACTIVE / NOT COMPLETE**; remaining grammar roles, full checked source conversion, relocated host metadata packaging and source diagnostic/IDE fidelity remain open.


## Earlier real mutual compiler-module parity diagnosis — resolved by the strict passing checkpoint above

Source **`02c26c545f444a339698af0ae4b069ffd6f731b3`**, runner **`372e37f4822cc962467d2acae4daa3df552d0322`**, [run 42527694180](https://github.com/dwijayuda/pskernel/actions/runs/42527694180), project job **128874919801**: converted **Lean.Compiler.LCNF.DeclHash** now **compiles through PS grammar and produces byte-identical native C**. Native-only compilation rejects the converted source. The strict public-olean gate **FAILS**: native `103a0395c4808e7a0b2cbe5fa9e9bbd27392d18312c2a25235d1a9470a9308fb`, PS `7eb63649b6979438e70cf4d00fcb5a8077d082fad8a5ad05dbff366405cae7d6`.

A Linux diagnostic uses pinned Lean's native `readModuleData`, ConstantInfo/Expr comparison and expression representation. Ordered public constant names (**15**), types, levels, mutual groups and alpha-equivalent values match. Two values (`hashCode._unsafe_rec` and `hashAlt._unsafe_rec`) have different printed generated hygienic binder counters. Extension names/counts match; extension payload equality is **not** established. **This is diagnosis, not a public-olean parity PASS or whole-module source certificate.** The previous ClosedTermCache exact parity remains separately qualified.

[Diagnostic artifact 13636076642](https://github.com/dwijayuda/pskernel/actions/runs/42527694180/artifacts/13636076642), ZIP SHA-256 `d71ebe7d6e11eb694b434a375feacd1642f73955ae95c66cdbff9efa6b71fb56`.

Candidate source **`3c47198c4ed8f43a4967deef199ea61fa5e8d592`**, runner **`d27b55627f50bbc4184839766994e286ae18af80`**, [run 42528176757](https://github.com/dwijayuda/pskernel/actions/runs/42528176757) is **IN PROGRESS**. It preserves original parenthesized type-argument syntax within the added call delimiters. No hygiene-counter padding, output normalization or weakened byte gate is used. Goal remains **ACTIVE / NOT COMPLETE**.


## Earlier recursive compiler-head and root-value migration candidate — superseded

[Source PR #14](https://github.com/dwijayuda/lean4/pull/14), source **`a0e24b19e6dc7fc87dba1d06f8cf17938e4f4f31`**; [runner PR #231](https://github.com/dwijayuda/pskernel/pull/231), runner **`4ba47bcd4451874addc1b4df9c49b32d274e7cd1`**; [run 42527051005](https://github.com/dwijayuda/pskernel/actions/runs/42527051005): **IN PROGRESS**.

The actual pinned **Lean.Compiler.LCNF.DeclHash** blob **5f818560cb8fcba0df6f64acb6bdc01c48425189** is the next real-module probe. Native census ranges plan four typed heads (`hashParams`, `hashAlt`, `hashAlts`, `hashCode`), including recursive mutual members. Owned binder-type single-call adjacency is normalized; root-value application metadata retains only function/argument ranges, so call delimiters can be converted without walking lambda, match, quotation or DSL bodies. Native-only rejection and identical C/public-olean output remain required.

Test candidate **9afb5879612d5d6bf35e56f20eb0899512669727**, runner **885d87e714905047feaccd852cefe1856de1c2d6**, [run 42526462886](https://github.com/dwijayuda/pskernel/actions/runs/42526462886), project **128871135830**, planned four heads and passed the native baseline, then failed PS compilation at the original spaced-parenthesized `foldl` value operand. The newer candidate addresses that explicit owned root role. Exact failure artifact digests remain in both JSON ledgers. The older ClosedTermCache parity stays qualified separately. **No DeclHash parity or whole-body grammar closure is claimed yet.**

The independent full compiler/census [run 42522976977](https://github.com/dwijayuda/pskernel/actions/runs/42522976977) at source **28904e5a7ccb19a15e311ecc654541dc0ee639ec**, runner **484868307c6611fedf1a464e2e102c02b8ad5855** now has **stage one 128861032581 PASS**: **2,567 modules** (2,546 pinned + 21 PS0), **5,138 native Lake jobs**, source smoke and all-module census/origin join PASS; **72,792 selected native-compatible rows / zero mapped PS rows**. [Artifact 13635566244](https://github.com/dwijayuda/pskernel/actions/runs/42522976977/artifacts/13635566244) ZIP SHA-256 `c4443462ef060abcbe8a4033f5f01325f7c9f91cc6ece84b5c8b3c14c4ad5be0`. **Stage two 128870983007 is IN PROGRESS**, using that exact migrated executable. This native-compatible baseline is separate from canonical ProofScript source migration. Goal ACTIVE / NOT COMPLETE.


## Scoped/mutual PS source-command operands — finite Linux checkpoint

Qualified source **`27e58f278b2ceb74bab4535245b15dd4668ad331`**, runner **`7ebf8265bb5ec8296c8ace5031b039b043452a28`**, [run 42525540427](https://github.com/dwijayuda/pskernel/actions/runs/42525540427): **all four jobs PASS** — project **128868235000**, native **128868234727**, proof-linked **128868234968**, host **128868234969**.

**PS0_COMMAND_OPERANDS:3:3:3:3** and **PS0_SCOPED_MUTUAL_COMMAND_OPERANDS: PASS**: PS function signatures work under native `set_option ... in`, `open ... in`, nested `in` wrappers and native mutual blocks. Native option/namespace handling and command/mutual elaboration remain Lean's. Borrowed native fallback declines these explicit owned prefix words so it cannot consume a whole wrapper before PS child parsing; selected PS declarations use native `withPosition` to bound contextual alias words by declaration indentation. Native quotations retain native `Command.in` / `declaration` / `mutual` AST identity.

The new actual-source census traverses only the explicitly owned native `in` RHS and mutual command arrays. It records original nested declaration names and keyword ranges, preserves raw bytes/direct imports and retains nested counters separately from the original top-level counters. It does not descend into quoted/DSL/generated data. Nested invalid defaults reach **PS0V1-CALL-GAP** and **PS0V1-CALL-ORDER**.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| native | [13635446365](https://github.com/dwijayuda/pskernel/actions/runs/42525540427/artifacts/13635446365) | `a969cb29fc355700f891d6a4729ae4344be2ff5e7cc172fbc723a9aa6a400f8b` |
| project | [13635222711](https://github.com/dwijayuda/pskernel/actions/runs/42525540427/artifacts/13635222711) | `fe417f0c46ca8b9bb3de4dca131fd1bf21ddb55b0568f93184234c9f3ea63ccf` |
| external | [13634728251](https://github.com/dwijayuda/pskernel/actions/runs/42525540427/artifacts/13634728251) | `85284d25cd7ae70c388334912df7fcfad8b03d41ee5a0984e05ab8a25a378723` |

Failed parser-field/layout, fallback/indentation and host-lexer candidates are retained with source/runner/run/job/artifact digests in both JSON ledgers. Temporary traces are removed. The legacy `pscvNonExplicitBinder` still reserves double-brace tokens in host imports; cleaning up that lexical fidelity gap remains open. Native `attribute`/`variable`/`omit` prefix parsers are reused, but their other PS operand roles are not separately qualified by this checkpoint.

The independent full compiler/census [run 42522976977](https://github.com/dwijayuda/pskernel/actions/runs/42522976977) remains pinned to earlier runtime-qualified source **28904e5a7ccb19a15e311ecc654541dc0ee639ec**, runner **484868307c6611fedf1a464e2e102c02b8ad5855**; stage-one job **128861032581** subsequently PASSED; see the updated complete-forest evidence above. It does not qualify this newer grammar increment. Goal remains **ACTIVE / NOT COMPLETE**; broad obligations and execution-certificate claims are not promoted.


## Current modern metacompiler startup checkpoint — 9 November 2026

Qualified source **`28904e5a7ccb19a15e311ecc654541dc0ee639ec`**, runner **`4b3c4a60d9c6da28f581bba657f1e041c559b7c6`**, Linux [run 42522802697](https://github.com/dwijayuda/pskernel/actions/runs/42522802697): **all four jobs PASS** — project **128859792609**, native **128859792529**, proof-linked **128859792415**, host **128859792642**. Prelude/source/binder/recursive/native regressions, the three real compiler-head C/public-olean parity checks and the new modern-root startup regression all pass together.

**PS0_MODERN_FRONTEND_HOOKS: PASS** builds a native executable from an ordinary modern module root importing the census compiler module, then verifies runtime option registration and an actual native module-linter callback on source with only `Init` imported. Census observation code and builtin initializers now live in the ordinary runtime section, matching [pinned Lean runtime/comptime initialization](https://github.com/dwijayuda/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Compiler/LCNF/EmitC.lean). This corrects the startup boundary exposed by the previous full stage-two run; it is not a core compiler or trust-policy modification.

Focused [run 42522806754](https://github.com/dwijayuda/pskernel/actions/runs/42522806754), runner **`8fa31701d19947918cba8d2bcdc280409546a24d`**, job **128859806058**, PASS; [artifact 13633657923](https://github.com/dwijayuda/pskernel/actions/runs/42522806754/artifacts/13633657923) ZIP SHA-256 `0551c5d81aca60f167e8f177dbf540428d53e2eb7b2650d2f9bdcc060a76f52f`. The source `9a5c59fb60407272cf2e5d5fc53ca18bf503c0c9` probe failed earlier because its String option was inferred as a FilePath (run **42522565402**, job **128859048140**); the passing probe uses explicit native argument/option/path types.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| external | [13634018132](https://github.com/dwijayuda/pskernel/actions/runs/42522802697/artifacts/13634018132) | `41a85f5e2b444222a0ec554bff1c8317d03e920b1576268a753b75f6fa87f275` |
| project | [13633953401](https://github.com/dwijayuda/pskernel/actions/runs/42522802697/artifacts/13633953401) | `bd540f7aeeef3e9575f9c11f7825ebef89154da477fe00b3bf0887ed6f05d26f` |
| native | [13633683974](https://github.com/dwijayuda/pskernel/actions/runs/42522802697/artifacts/13633683974) | `ab969baff1bf5f637166f5816a866eac52e5e995c6b2853de9a5ff39ae051b10` |

The fresh complete compiler/census [run 42522976977](https://github.com/dwijayuda/pskernel/actions/runs/42522976977), runner **`484868307c6611fedf1a464e2e102c02b8ad5855`**, [PR #226](https://github.com/dwijayuda/pskernel/pull/226), is **IN PROGRESS**, pinned to this source. It first gates on the finite project/startup checks, then requires two complete native Lake stages and all C/public-olean fixed-point comparisons. No fresh full-compiler PASS is claimed.

**Goal remains ACTIVE / NOT COMPLETE:** finite prelude grammar and three real compiler heads are qualified, while entire-corpus ProofScript grammar/source conversion, scoped/mutual command operands and remaining term/signature contexts remain open. Native-compatible full-source compilation is a distinct gate. All broad obligations remain PENDING and all execution-certificate claims remain false.


## Qualified prelude grammar and real compiler heads; full bootstrap still open

Source **`704c5614e15981145260f5aac1ea8a891875cf12`**, runner **`b5a45855bbee9413efa7720d6c7cad673a31c347`**, Linux [run 42521766675](https://github.com/dwijayuda/pskernel/actions/runs/42521766675): **all four jobs PASS** — project **128856670616**, native **128856670515**, proof-linked **128856670295**, host **128856670557**. The existing grammar, binder/default/mixed-signature, origin recovery and recursive native Lake regressions pass together.

The finite prelude grammar checks now pass, including **PS0_PRELUDE_GRAMMAR:42:3**, no inserted logical PS0 imports or changed source bytes, native quotation AST ownership, contextual `function` identifiers, owned ASCII strict binders and native compiler-stage setup options. Compiler-host metadata lookup is isolated to the executable's sibling library and pinned SDK; it cannot select a target module currently being rebuilt.

**PS0_PINNED_COMPILER_HEADS_NATIVE_PARITY: PASS**: native syntax/ranges convert exactly `cacheClosedTermName`, `getClosedTermName?` and `isClosedTermName` in the original logical module **Lean.Compiler.ClosedTermCache**, pinned Git blob **20b7acf5d684789ab52b81dda7def4b19568213c**. Native-only mode rejects the converted PS heads. Both native Lake compilations produce identical C and public olean:
- C SHA-256: `7d54fb41d97e4be6bd11497a5919f5ee35f87643befc481a135d2cf6365494d2`.
- Public olean SHA-256: `f772b02fde1d5ebc4117d53d6bd7aeeb15e5131c53329adf0b3b7ea623f4467e`.
- Original file SHA-256: `e1184350de6ef6ade1dc0f34d7320a4fc7445c5f9a7132d9ed7fc1f5518c38b9`; converted PS SHA-256: `7289f2d309b04c5b9935d4bf0c4252c117ca3e46b7edb97b94606fc9b6842548`.

This is **three typed compiler declaration heads** with unchanged native bodies and pinned SDK dependency metadata; it is not whole-module grammar closure or the complete source migration. Focused [run 42521772271](https://github.com/dwijayuda/pskernel/actions/runs/42521772271), runner **`aedb625518e1550409ebbddbe281a2ecefc8fbd9`**, job **128856609143**, also PASS; [artifact 13633811615](https://github.com/dwijayuda/pskernel/actions/runs/42521772271/artifacts/13633811615) ZIP SHA-256 `2f62aba5be400a8e1b2c2d1a2fd26edb4d796d8cc4e0f67bf174aeb3eeed7d7f`. Independent hash inspection [run 42521989131](https://github.com/dwijayuda/pskernel/actions/runs/42521989131), job **128857280327**, confirms the retained exact comparisons and edit plan.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| external | [13633876770](https://github.com/dwijayuda/pskernel/actions/runs/42521766675/artifacts/13633876770) | `6e5897351d9214d9193e6c6ad2c3a586ca923e164d0ad1bbc7c9daffb3fb15ff` |
| native | [13633751880](https://github.com/dwijayuda/pskernel/actions/runs/42521766675/artifacts/13633751880) | `785a657ca64f790eddaa7770e8aff62698a96d5881d6f4a75bdcc30181582fe7` |
| project | [13633468541](https://github.com/dwijayuda/pskernel/actions/runs/42521766675/artifacts/13633468541) | `e24f2a84cd21fac865839f8a78b919737330f7b0fb55769f88863bc9ec0b2745` |

The earlier full compiler/census [run 42517718338](https://github.com/dwijayuda/pskernel/actions/runs/42517718338) has finished: stage one **128844671227 PASS**, **2,566 modules / 5,136 native Lake jobs**, all-module census/origin join and **72,790 native-compatible selected declaration rows / zero mapped PS**; stage two **128852603767 FAIL**, unknown **ps0.sourceCensusPath** at modern compiler startup. [Failure artifact 13632814291](https://github.com/dwijayuda/pskernel/actions/runs/42517718338/artifacts/13632814291) ZIP SHA-256 `c9fb98ee7a52d05bbfa93f137bd7fd8745459dddc9204b36233080e2bf7e6817`. No fresh full fixed point was reached.

The runtime-initialization candidate was subsequently qualified at source **28904e5a7ccb19a15e311ecc654541dc0ee639ec**; see the current checkpoint above.

The actual full census inspection [run 42521444844](https://github.com/dwijayuda/pskernel/actions/runs/42521444844), job **128855617016**, verifies source/binary identity and reports original top-level head counts, including **25,658 definitions**, **44,979 theorems**, **5,584 instances**, **2,445 structures**, **597 inductives**, **987 in wrappers** and **111 mutual blocks**. [Summary artifact 13632644276](https://github.com/dwijayuda/pskernel/actions/runs/42521444844/artifacts/13632644276) SHA-256 `f0c6a2043fc098f45affd1c5ab9dae0c4b64696d95295e09dbb2dcd120116c5d`. These are an adapter worklist, not completion percentages.

**Goal ACTIVE / NOT COMPLETE.** Next gates: modern metacompiler runtime initialization and full fresh compiler requalification; explicit scoped/mutual source-command operands, remaining PS term/signature contexts and safe canonical source conversion; then the entire pinned forest using ProofScript syntax through native build/link and migrated fixed-point checks. Relocated compiler-host metadata packaging and automatic diagnostic/IDE remapping remain open. All broad obligations remain PENDING; all `grammarMigrationComplete` / `verified_execution` claims remain false.


## Earlier complete native compiler census checkpoint — superseded by the final stage-two result above

Pinned source **`abf3585d99c921fe02697b679867a0a55e433168`**, runner **`e78cd4479ba5b1433e8879c14de79ba27427dfdc`**, [run 42517718338](https://github.com/dwijayuda/pskernel/actions/runs/42517718338): stage one **128844671227 PASS**. All **2,566 modules** (**2,546 pinned compiler + 20 PS0**) build/link through **5,136 native Lake jobs**. Source smoke passes. Every module passes the actual-frontend/original-byte census join. There are **72,790 selected source declaration rows, all native-compatible; zero mapped-PS rows** at this checkpoint. This establishes the native-compatible baseline and full census, **not** the required canonical PS source migration.

[Stage-one artifact 13632838932](https://github.com/dwijayuda/pskernel/actions/runs/42517718338/artifacts/13632838932), ZIP SHA-256 **`2395167f3782944cf4291efe55a10d1185f9eec6244493e0df985132e30e7308`**, retains the exact migrated executable, full source-command snapshots and joined hash summary. Stage two **128852603767** subsequently FAILED with unknown ps0.sourceCensusPath; see final evidence above. A fresh fixed-point result is not yet available.


## Finite prelude PS grammar step PASS; real compiler head parity pending

Source **`eb71f33b2fa0ff2e53bdd7dd9e73b96f63b593d1`**, runner **`dc03ae543bc2bc050a6c62034aee2cb4bc80a56b`**, [run 42520414613](https://github.com/dwijayuda/pskernel/actions/runs/42520414613), project job **128852573466**: **PS0_PRELUDE_GRAMMAR:42:3** and **PS0_PRELUDE_GRAMMAR_NO_HIDDEN_IMPORTS: PASS**. Native Lake builds/links/runs the actual PS prelude source, preserves exact raw bytes and direct imports, retains native quotation AST ownership and contextual identifiers, and accepts owned ASCII strict binders. It also compiles under native bootstrap/stage options. Exact project artifact digest is retained below and in the JSON ledgers.

**The overall project job FAILS later in a separate real-compiler-head probe.** The three-head edit plan is produced from captured native signature AST/ranges, but its native baseline could not find SDK sibling modules because its target `Lean` prefix shadowed the SDK root; its root-module setting also selected that module as an executable entry. No C/public-olean comparison was reached. Native/proof-linked/host jobs PASS; this is **not an all-four-jobs PASS checkpoint**.

[Project artifact 13633535255](https://github.com/dwijayuda/pskernel/actions/runs/42520414613/artifacts/13633535255), ZIP SHA-256 `8a10e7724b03e031fcb2063db4066814c34a0899e3f49cfedc48a323fffc3b7f`.

Candidate source **`263eb3f8693e0b2f9f57ea0418e1babdfce192f7`**, runner **`087035c38c30ad1a959d6279abdefe4bfe2536cc`**, corrects only that finite probe's native SDK metadata layout and entry-module selection; Linux qualification is pending. Dependency metadata stays pinned SDK data, while target artifacts are built fresh by native Lake. Compiler-head conversion remains limited to three typed heads; native bodies are retained. Goal remains ACTIVE / NOT COMPLETE.


## Earlier prelude source grammar candidate — superseded by the finite step evidence above

[Source PR #12](https://github.com/dwijayuda/lean4/pull/12), source **`eb71f33b2fa0ff2e53bdd7dd9e73b96f63b593d1`**; [runner PR #227](https://github.com/dwijayuda/pskernel/pull/227), runner **`dc03ae543bc2bc050a6c62034aee2cb4bc80a56b`**; Linux [run 42520414613](https://github.com/dwijayuda/pskernel/actions/runs/42520414613) is **IN PROGRESS**.

The candidate uses Lean's native parser categories, parser descriptors, builtin macro/term-elaborator registrations and root category dispatch. `-KsourceGrammar=true` reaches the frontend through native Lake setup options. A separate compiler-host environment loads syntax metadata beside the compiler executable and restores target module lookup before compilation. No target prelude source or logical import is inserted. Only the selected PS productions are registered; the root dispatch consumes its flag in a fresh native parser context/cache so native command/term/binder quotations retain their category ownership.

The finite test requires PS function/default/const declarations, a contextual `function` identifier, native strict binders, native quotation AST identity, exact source bytes/direct imports and **PS0_PRELUDE_GRAMMAR:42:3** from a Lake-linked executable. It first requires native-only prelude compilation to reject the PS command. The test-first run **42518050363** was superseded/cancelled and is **not red test evidence**. Actual failed candidates are retained in both JSON ledgers: namespace/token API errors, native persistent-map API mismatch, then missing compiler-host metadata under target-only module lookup.

The candidate also tests Lean's pinned `Lean.Compiler.ClosedTermCache` source (blob **20b7acf5d684789ab52b81dda7def4b19568213c**). A finite planner uses native signature AST/ranges to change three typed declaration heads to PS function/comma syntax, preserving native bodies and all unedited bytes. The test requires native-only rejection, actual PS grammar compilation, original direct imports and identical generated C/public olean. **This is pending; bodies are not canonicalized and no whole-module grammar closure is claimed.** Compiler-host stage options and lifetime, native strict-bracket parsers, fresh target initializer execution and native fallback AST/macro-scope preservation are included in the candidate. All failed-source/runner/job/artifact digests are retained in the JSON ledgers.

**Not yet qualified.** Full canonical source conversion, remaining nested PS operands/signatures, host metadata packaging for relocated migrated compilers and full fresh compiler closure remain open. Independent full compiler/census run **42517718338** continues at the earlier stage-option checkpoint. Goal remains **ACTIVE / NOT COMPLETE**.


## Native Lake compiler-stage evaluation recovery — 9 November 2026

Source **`abf3585d99c921fe02697b679867a0a55e433168`**, runner **`f5eea9af18a6c6a04ee92ef47ce36311f2d95e15`**, Linux [run 42517518674](https://github.com/dwijayuda/pskernel/actions/runs/42517518674): **all four jobs PASS** — project/binder/census **128843676094**, native **128843675964**, proof-linked **128843675694**, host **128843675945**.

Native Lake bootstrap builds now receive **`interpreter.prefer_native=false` through `leanOptions`**, matching [pinned Lean CMake stage builds](https://github.com/dwijayuda/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/CMakeLists.txt). This makes compile-time evaluation use the current IR while rebuilding declarations already linked in the running compiler. The original binder parsers are retained. Normal project options retain their existing defaults.

Focused [run 42517552265](https://github.com/dwijayuda/pskernel/actions/runs/42517552265), runner **`f5fb141be25251c6b8d55f21ac342df7d02218c5`**, job **128843778154**, verifies the actual native Lake setup option and successfully rebuilds `PS0.Binders` with the exact prior stage-one migrated executable. C and public olean hashes match the SDK-driver build. Oracles **PS0_BINDER_STAGE_OPTIONS_AND_OUTPUTS: PASS** and **PS0_BINDER_SELF_REBUILD: PASS**. Focused [artifact 13632032709](https://github.com/dwijayuda/pskernel/actions/runs/42517552265/artifacts/13632032709) SHA-256 `b7bcc738cddc05afe2c2345e6e15a7bbaf992289ce881f881d02def1b25ab84a`.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| external | [13631689156](https://github.com/dwijayuda/pskernel/actions/runs/42517518674/artifacts/13631689156) | `2ae2a4b513c506da1f014740e31724bd4123d487948e2635f810fc7659d987a8` |
| project | [13631639193](https://github.com/dwijayuda/pskernel/actions/runs/42517518674/artifacts/13631639193) | `1bdb60aa39e7acc3fee61e597493227acd43ac021553c583e153cc9b7b6de461` |
| native | [13631368600](https://github.com/dwijayuda/pskernel/actions/runs/42517518674/artifacts/13631368600) | `58341095eb56d6ec63ab964d73ad1125098b5040ee3a30e009564e5cbc11dc59` |

The inline-descriptor candidate `a21ecd55fa1b40d66ae5e8ccce64cc04ab5a0c30` was **reverted** after regular run **42517158082** / job **128842586950** rejected changed suffix AST shapes and focused run **42517187718** / job **128842672919** exposed old linked descriptors referencing removed `binderSuffix`. The final change reuses upstream infrastructure rather than changing binder syntax.

Independent [full compiler/census run 42517718338](https://github.com/dwijayuda/pskernel/actions/runs/42517718338), [runner PR #226](https://github.com/dwijayuda/pskernel/pull/226), runner **`e78cd4479ba5b1433e8879c14de79ba27427dfdc`**, is **IN PROGRESS** at this source. It requires both fresh complete compiler stages, all generated C/public olean comparisons, and actual-source census joins. This is still a native-compatible forest regression; canonical ProofScript source grammar migration remains **ACTIVE / NOT COMPLETE**.


## Current same-frontend census and compiler regression — 9 November 2026

Qualified source **`4d2b7204c0afab86e6f7dfc306b0d53fee6cd15a`**, runner **`189be356819cec9d2d56f3592207ffbe98f3ea6f`**, Linux [run 42515763246](https://github.com/dwijayuda/pskernel/actions/runs/42515763246): **all four jobs PASS**. Exact jobs: project/binder/census **128838311309**, native **128838311805**, proof-linked **128838303330**, host **128838316475**. Official Lean and normative R2 pins are unchanged.

The native `addModuleLinter` callback captures commands from the same frontend execution used for code generation. Census sidecars retain normalized source, original top-level command kinds/head kinds/ranges, imports and local environment names. Fixtures distinguish original declarations, macro-generated declarations and quoted declaration data. Actual recursive Lake module compilations retain matching census and origin sidecars. The corpus join verifies input equality and recovery of every original byte; its **one-module fixture subset** passes and mismatched provenance is rejected. **The full 2,546-module census has not run.** Prelude inputs remain native-compatible, without hidden logical imports or PS grammar support.

Scoped signature priority now exceeds the legacy alias priority. New `function` type/default and `const` type gap negatives reach the intended **PS0V1-CALL-GAP** adapter diagnostic. Executed oracles include **PS0_NATIVE_SOURCE_CENSUS: PASS**, **PS0_PROJECT_SAME_FRONTEND_CENSUS: PASS** and **PS0_NATIVE_SOURCE_CENSUS_JOIN: PASS**.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Proof-linked | [13631910233](https://github.com/dwijayuda/pskernel/actions/runs/42515763246/artifacts/13631910233) | `31686112db3cd8b940f201c63c9100867f0d16a0a5fc18c1a798954f6ddc7ba0` |
| Project/binder/census | [13631805505](https://github.com/dwijayuda/pskernel/actions/runs/42515763246/artifacts/13631805505) | `85f09423b3d2ea0deb845f3843bdbc5d3d6ff460cbfaaa8a94fa95838937a43a` |
| Native | [13631216761](https://github.com/dwijayuda/pskernel/actions/runs/42515763246/artifacts/13631216761) | `f8f20668e1ed032a1308189fc7dd97a1ea9fb35e0eb404d528a454bd8f836d16` |

The independent full compiler [run 42511359592](https://github.com/dwijayuda/pskernel/actions/runs/42511359592), source **`9826bdd9dc422fe021de953a570972d7b85df2f4`**, runner **`332ed8372583f2c1a2b08ed3aacd182aa3aa95d2`**, finished: stage one **128825446119 PASS**, building/linking **2,565 modules / 5,134 native Lake jobs** and passing source smoke; stage two **128831905726 FAIL**, native exit **139** while recompiling **PS0.Binders.ps**. Fixed-point comparison was not reached. Stage-one [artifact 13630277856](https://github.com/dwijayuda/pskernel/actions/runs/42511359592/artifacts/13630277856) SHA-256 `9cd6ca6db18c631390bcd4f6b762c38c8227f60a21a84d3eee52fac2a2f0ccf2`; failure [artifact 13631615771](https://github.com/dwijayuda/pskernel/actions/runs/42511359592/artifacts/13631615771) SHA-256 `6261b2be9f790dd8fdf07f17bc070fb934119281bf18a0e7ad78d3d5aa33cbb9`.

Focused diagnostic [run 42516632944](https://github.com/dwijayuda/pskernel/actions/runs/42516632944), runner **`e8b085b551a5de8c6c0a2e42b895627bd8be4832`**, job **128840967358**, reproduced the crash in Lean's native parser-constant evaluator. Setting the existing native option `interpreter.prefer_native=false` for that diagnostic alone succeeded, with identical generated C and public olean to the SDK build. Diagnostic [artifact 13631362254](https://github.com/dwijayuda/pskernel/actions/runs/42516632944/artifacts/13631362254) SHA-256 `7afffc436a768af054d2a32b3710307148a4a4d9a46b1db669ce7b4c7f5ca0ae`. This is diagnosis, not compiler qualification.

The inline-descriptor candidate was subsequently reverted; see the stage-evaluation recovery evidence above.

**Goal ACTIVE / NOT COMPLETE.** Required next: resolve/requalify the compiler self-rebuild, run the full actual-source census, provide bootstrap/prelude PS grammar without hidden logical imports/cycles, implement remaining owned operand/signature contexts and checked ProofScript source conversion, then build/link and compare the entire transformed corpus through a fresh migrated compiler. Diagnostic/IDE remapping and full provenance remain open. All broad obligations remain PENDING; `grammarMigrationComplete` and `verified_execution` remain false.


**Sole normative reference:** [PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md), edition R2, 2026-10-16. Uploaded Git blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
**Lean:** official 4.35.0, `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.

## Current origin-artifact recovery checkpoint — 9 November 2026

Source **`863da731fc5957000d4633d13a9711d8d14ae126`**, runner **`710e9d296ddd344e6f559717c4aee0b0568e3e6c`**, Linux [run 42512184970](https://github.com/dwijayuda/pskernel/actions/runs/42512184970): **completed SUCCESS; all four jobs PASS**. Exact jobs: project **128827500492**, native **128827500249**, proof-linked **128827500080**, host **128827500317**. This newer source retains the binder/signature probes below and adds **PS0_PROJECT_SOURCE_ORIGIN_CACHE_RECOVERY: PASS**.

The adapter composes a native `Job.mapM` continuation after successful `leanArts`, verifies/recreates the exact source-origin JSON and records its content in the native Lake trace. Deleting or corrupting an ilean origin sidecar is repaired to identical bytes on the next warm build, while the executable's SHA-256 and mtime remain unchanged. Native compilation/elaboration, artifact reuse, object code and linking remain Lean/Lake responsibilities.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Native regression | [13629788351](https://github.com/dwijayuda/pskernel/actions/runs/42512184970/artifacts/13629788351) | `403bca4db145582fa92f08f91f5ea8feb9f82efabe021d2983fc2454e409c107` |
| Project/binder/origin recovery | [13629683793](https://github.com/dwijayuda/pskernel/actions/runs/42512184970/artifacts/13629683793) | `1c60c6b9b98a6cceed3b99e2b3377a6fe36e4799e86f77c460e6c75e9637875d` |
| Proof-linked regression | [13629454560](https://github.com/dwijayuda/pskernel/actions/runs/42512184970/artifacts/13629454560) | `49c8bddc8739c988a0ab4ffa4fd407fcc50c280da9abd4a8daea8fb7fea877b5` |

Test-first source **89af6cc1d3aecf6cfa81f0a8adf59afb430a0e73**, run **42511729740**, job **128826050067**, failed because warm builds did not restore missing maps. Candidate **6d0c3f5c546e2ca15c2b52187d7ad353ad725781**, run **42511971440**, job **128826860303**, exposed a Bool return escaping the native artifact continuation; the passing source preserves the native artifact result.

The full compiler regression run **42511359592** has finished: stage one **128825446119 PASS**, stage two **128831905726 FAIL** with exit **139** in **PS0.Binders**. See the current evidence above; no fixed-point qualification was reached.

**The project goal remains ACTIVE.** Next: collect actual compiler command syntax through Lean's native module-linter API, distinguish original/quoted/DSL/generated forms, implement checked source migration and bootstrap/prelude grammar support without hidden logical imports or cycles, then qualify the entire transformed corpus through native Lake builds, migrated source checks and fixed-point evidence. Diagnostic/IDE remapping and full provenance also remain open. No broad v1 family is promoted; no verified-execution certificate is issued.

## Active goal and qualified binder/default checkpoint — 9 November 2026

**Goal remains ACTIVE:** compile the entire pinned Lean4 compiler corpus as `.ps` using ProofScript syntax and grammars. Renaming native sources, or building only native-compatible bodies, is insufficient. The earlier full native-compatible source-forest milestone is historical evidence, not completion of this stronger requirement.

Qualified source **`9826bdd9dc422fe021de953a570972d7b85df2f4`**, runner **`523c9e600ade3fdd6bba4a6bc203383477389837`**, [source PR #10](https://github.com/dwijayuda/lean4/pull/10), [runner PR #222](https://github.com/dwijayuda/pskernel/pull/222). Linux [run 42511067847](https://github.com/dwijayuda/pskernel/actions/runs/42511067847) is **completed SUCCESS; all four jobs PASS**: binder/project **128824034975**, native **128824034894**, proof-linked **128824034872**, host-contract **128824034957**. The official Lean **eb6cafb7290e8bd5f2937522d8d804f58f02bafc** and normative R2 **c50203f8e4cb79b3e6680088a07c1d1e145b8f0b** pins are unchanged.

`PS0/Binders.lean` lowers ordered mixed telescopes to genuine native binder nodes. It preserves native shared, anonymous and inferred binders, PS comma groups, dependency order, type/default operands, strict/implicit/instance/universe parameters and trailing commas. Equivalent native/single-comma parses coalesce by binder syntax structure; different structures fail before typing. The `function` alias retains its typed-group/adjacency/nullary restrictions. Native `binderTactic` is tried before ordinary PS defaults, preserving **autoParam versus optParam**, inspected in the actual Lean environment.

Mapped signatures now include simple def/abbrev/theorem/example, opaque, axiom and instance forms, native optional instance name/priority and omitted example result types. Function/const aliases retain native modifiers and source operands. Equation, contract, termination, constructor/field/local and remaining signature contexts are still required. The binder fixture checks exact identifier source information and type/default ranges; native `bracketedBinder` DSL operands retain native syntax.

Empty calls preserve the callable head before native optional completion, allow native CoeFun, and reject a remaining required telescope after Unit insertion, including returned functions and explicit `@id()`. The deriving adapter now forwards native identifiers to registered handlers instead of reserving class names globally. The executed oracles are **PS0_BINDERS:3:3:2:3:3:3**, **PS0_SIGNATURE_HEADS:3:3:3**, **PS0_BINDER_OPERANDS: PASS**, plus the existing recursive/category/origin/native/proof-linked regressions.

`mixed_signature_heads.ps` deliberately includes **one unused axiom** to exercise that declaration grammar; it is reported, not approved as a proof assumption. These are finite syntax/native-execution tests, not formal source or execution certificates. All broad v1 families remain PENDING and receipts retain `verified_execution: false`.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Proof-linked regression | [13629691688](https://github.com/dwijayuda/pskernel/actions/runs/42511067847/artifacts/13629691688) | `28f5a6346c3265732e378d6f2a0a4ebca210d8e4d63ad2e4cadfb398c3f08aad` |
| Native regression | [13629307964](https://github.com/dwijayuda/pskernel/actions/runs/42511067847/artifacts/13629307964) | `79a047113f70d353403457d308c70228b484c908d10bcae5cfc06f5cf756bf54` |
| Binder/project/source origins | [13629118835](https://github.com/dwijayuda/pskernel/actions/runs/42511067847/artifacts/13629118835) | `37843bed9b6446cf4243287990fced81b3997e7acf4d42fbb85ebb070571e191` |

The separate full native-compatible compiler regression run **42511359592** finished with stage one PASS and stage two FAIL in PS0.Binders. It does not establish canonical ProofScript source migration or a fixed point.

Next required work: source-origin sidecar cache recovery/diagnostic integration; a native-parser-driven syntax census and source migration; bootstrap/prelude PS adapters without hidden logical imports or dependency cycles; remaining PS operand/signature roles; then full transformed-corpus Lake build/link, migrated-compiler source checks and fixed-point evidence. No main merge, force push, package publication, pin change or trust relaxation occurred.

Resolved candidate failures and exact identities remain in `v1-coverage.json`. In particular, run **42509432717** job **128819138702** found parser-name ambiguity, run **42509906650** job **128820493639** found legacy deriving token pollution/default-head completion, and run **42510946874** job **128823659857** found the native optional-priority quotation shape. The passing checkpoint retains the intended native diagnostics.

## Previous grammar and source-origin increment — 9 November 2026

Qualified source **`1d76c795edbbaa79fe4d938f073114e5bd76a3ae`**, runner **`cd3d6862abc86d3d4371147cd516f2a1dfd1c9a5`**, draft [source PR #9](https://github.com/dwijayuda/lean4/pull/9) and [runner PR #221](https://github.com/dwijayuda/pskernel/pull/221). Linux [run 42507413045](https://github.com/dwijayuda/pskernel/actions/runs/42507413045) is **completed SUCCESS; all four jobs PASS**: project/grammar/origins **128812930802**, native **128812930996**, proof-linked **128812930942**, host-contract **128812930963**. The official Lean and normative R2 pins below are unchanged. Later documentation-only commits do not change the qualified implementation/test bytes.

Thin PS do adapters now lower a nonempty braced sequence to native `doSeqBracketed`/`doSeqItem` nodes. Identifier let/type/value, mutable let, reassignment, identifier monadic bind, expression statement and return slots lower through `psTerm`; Lean retains state, monad and type semantics. The fixture executes **`PS0_DO_OPERANDS:12:3`** and checks dedicated `apply`/`refine` proof operands. A native `doSeq` DSL preserves tuple application. Do-gap/order negatives reach **PS0V1-CALL-GAP/ORDER**, and a non-Unit intermediate action reaches Lean's actual **IO Nat versus IO Unit** error. The adapter reuses Lean's expression-token exclusion parser to keep `return` out of the generic do-expression alternative.

Header preparation now inserts generated policy/scope/evidence text around the original header and body, retaining every original UTF-8 byte in order. `source-map FILE.ps` exports **ps0-source-map/1**: half-open byte ranges distinguish original/generated spans, `source` retains original CRLF/trivia, and `nativeSource` is Lean's CRLF-normalized input. `source-origin FILE.ps NATIVE_BYTE_OFFSET` maps a native parser position back through Lean's own `FileMap` conversions and returns an original byte offset or JSON null for generated/no-origin positions. Use the same file bytes as the captured map. Native Lake compilation retains **`<module>.ilean.ps0-source-map.json`** sidecars.

Executed evidence: `tests/run-source-fidelity.py` passes implicit/explicit/prelude/empty/EOF-comment byte recovery, Unicode/nested/header/module comments, CRLF normalization lookup, exact CRLF/Unicode native-conversion body preservation, and an **actual native Syntax.getPos?** probe. The five source cases also pass official checking. `tests/run-project.py` validates and retains actual ilean sidecars while recursive build/invalidation/publication/module-boundary regressions pass. `tests/run-categories.py` passes both category fixtures and intended negatives. All build/proof/runtime tests ran on Linux Actions.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Project/grammar/origin maps | [13628415674](https://github.com/dwijayuda/pskernel/actions/runs/42507413045/artifacts/13628415674) | `990006cc3ad062fb57d930af70cb9bf703c815246c7a1b3c367c443b73e953ba` |
| Proof-linked regression | [13627967800](https://github.com/dwijayuda/pskernel/actions/runs/42507413045/artifacts/13627967800) | `6aea337c3e5c7f7b526be7fe7a431e7e2a854d72deb8f3ea10468ef40d94619b` |
| Native regression | [13627079788](https://github.com/dwijayuda/pskernel/actions/runs/42507413045/artifacts/13627079788) | `958adce04a4da8527811de3c7f91b55c9bbbc0d69798d4a44705e2184086abc9` |

This is finite grammar/origin-map qualification. Diagnostics and ilean references still use native prepared-source positions; automatic diagnostic/IDE presentation, sidecar cache recovery/facet tracking, arbitrary generated-syntax provenance and full source fidelity remain open. Binder/default/mixed signatures, remaining do control/pattern/configuration/native-layout slots, remaining tactic operands, match, collections/interpolation and configuration/attribute roles remain open. The 242 broad obligations are not promoted by these finite tests. Receipts retain `verified_execution: false`.

The complete compiler-source stage-one/stage-two test was **not rerun for this increment**. Its prior exact-source qualification remains recorded separately below. No main merge, force push, publication, pin change or trust relaxation occurred.

Resolved failed candidates remain in `v1-coverage.json`: source `74be717b036c8c01f971b5ba09a4553ba344a8a3`, run **42506026417**, job **128808825962**, exposed the native doElem splice requirement; source `1061a612067c1a9c88dee56eab30891ec68a0be2`, run **42506852635**, job **128811284072**, exposed return competition and normalized/raw CRLF offsets; source `133fcf9a0196597cd6ef62990bbef6483357cd61`, run **42507173849**, job **128812202395**, passed do cases but rejected CRLF headers when normalization was disabled. The passing implementation keeps native normalization and translates positions with native FileMaps.

## Historical complete compiler-source checkpoint

**Status at that checkpoint:** exact source `fb86cc425f0688bf3c6e98ff6c7adb8e899fe883`, runner
`0bca62aefdb00992d891f57c1a608dc0dacd60a3`, Linux
[run 42488162021](https://github.com/dwijayuda/pskernel/actions/runs/42488162021):
recursive/category `128754567397`, native `128754567736`, proof-linked
`128754567672`, host `128754567546` and compiler stage one `128754834515` PASS.
Stage two `128763580779` PASS: a fresh migrated-compiler build matches every C/public-olean hash across all 2,564 modules. All six workflow jobs passed.
Full v1 grammar closure remains open.

Both compiler stages compiled **all 2,546 pinned compiler-source Git blobs plus 18 PS0 modules**
from actual PS program inputs, completed **5,132 native Lake jobs**, audited every
generated C/olean and linked/ran a migrated compiler including an actual PS source check.
Its [artifact 13622010384](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13622010384)
has ZIP SHA-256 `de68e47310d1a58631c98072d4c786eede503f282c18830c3d0f13c2f422b23b`;
it retains the binary, all per-module input/output hashes and native link map.
Stage-two artifact `13621859608` has ZIP SHA-256
`dae31cf63a2098b2cfa67940936424fa16fd361c700d202b54c934ad24eb3827`.
Its result records zero C differences and zero public olean differences. Both stages
pass the migrated environment/source smoke checks. This tests a generated source
forest, not an upstream/main source cutover.

Independent Linux [link/ELF audit 42491501152](https://github.com/dwijayuda/pskernel/actions/runs/42491501152),
runner `54a3d0356609a24ec94090adedcc0a1645134f6b`, job `128764669538` PASS:
rebuilt frontend, LCNF emitter and PS0 objects/native symbols; zero SDK Lean/Init/Std
source-archive entries; zero SDK Lean shared-library dependencies. Migrated executable
SHA-256 `3c7371ca39e9689dd55c1b6fa1fbd3821f10c584a96c81f605e8350380bd339a`.
The pinned C++ runtime remains reused infrastructure.
Audit artifact `13621487247` has ZIP SHA-256
`8c9159eefd30f5204d277c888ea64eb40b5618beacca8a6825515f202637f6b6`.

Project artifact `13619929692` has ZIP SHA-256
`d1ea345719129239bf82acf92b543546e513e375d9e4211dfca815577edd759d`.
Executed fixtures cover recursive/meta imports, native dependencies/runtime, warm reuse,
source/native/driver invalidation, publication, prelude isolation, local entry,
source collisions, cycles and private visibility. Mapped category cases retain
native tuple DSL/quotation ownership and reject order/duplicate/gap errors.
These finite cases do not qualify all host operand roles. Older failures and
their exact evidence remain in AI_WORK_STATE.md and v1-coverage.json.

## Current exact-evidence policy

`v1-coverage.json` records the exact source, Lean/reference identity, fixture,
diagnostic/semantic oracle and CI run for each qualified finite case. A PASS
at an earlier source is historical evidence; changed implementations require
fresh exact-source qualification. Broad capability families remain PENDING
when only a subset has executable evidence.

The current category adapter registry is `standard-adapter-map.json`. The
recursive project fixtures are under `tests/project/`; `tests/run-project.py`
checks imported ps syntax, mixed native imports, source-kind ambiguity,
cycles, visibility and transitive invalidation. `tests/run-categories.py`
checks the selected mapped operands and native quotation/DSL ownership.

`tests/run-compiler-ps.py` is the compiler-source migration gate. It inventories
all 2,546 pinned `src/**/*.lean` Git blobs plus PS0 modules, compiles a program source tree with no
lean files, builds a migrated compiler executable and, in a second clean
job, requests full C/olean fixed-point comparison. Conversion, native source
admission, C/object compilation, executable behavior and a full compiler
fixed point are distinct outcomes. The two stages now PASS only at the recorded source/scope. Native-prelude coverage does not qualify all PS-owned bootstrap sugar.

## Implemented migration changes

| Layer | Current code | Remaining gap |
|---|---|---|
| Canonical document | Complete 4,163-line standalone v1 reference in PS0 | No normative predecessor fallback |
| Syntax adapters | Existing `function`/`const`, comma binders/calls, selected braced forms and Lean-native elaboration | All `psTerm`/`psCommand`/`psTactic`/`psDoSeq` ownership and `PS0.Syntax.lower` (`0B/`9) |
| Grammar | Removed frozen command/attribute/tactic/loop/source-token denial list; diagnostic-only syntax-kind inventory | Full interleaved host grammar and category-aware adaptation |
| Declaration policy | No mandatory v7 axioms/unsafe/partial/IO ban; `#ps0_evidence` is informational | Transitive claim-specific assumptions and evidence `12` |
| Imports/Standard | Native registered/imported extensions determine availability; no v7 finite Standard allowlist | Complete effective module/stage/extension identity and `prelude` isolation |
| Modules | Native Lake recursive PS/public/meta module graph, mixed native imports, invalidation, collision/cycle/private/local-entry negatives passed at the checkpoint | Broader package/options/plugin/bootstrap qualification and full grammar/source fidelity |
| `.lean` | Official Lean process unchanged and unrestricted | Routine exact-commit CI qualification |
| JS backend | Lean typed Nat-only IR, ESM/`.d.ts`/Source Map v3 | Validated build, more types, modules, runtime semantics proof |

**Important:** A v1 feature may be *admitted by the normative
language* but remain *not yet implemented by PS0*. Neither sentence
means it is guaranteed to compile in the current branch.

## New evidence baseline

[v1-coverage.json](v1-coverage.json) records **242** items:
100 capability families, 64 positive source cases, 47 negative
source/disallowed-claim cases, and 31 R2 boundary witnesses.
Every item initially has `PENDING` status. It is not a numeric
implementation-completion percentage.

`PASS` requires real evidence at the exact source, Lean,
compiler and imported environment identity. A static syntax-kind
count or availability via unchanged `.lean` does not qualify PS
source capability. The old PSCV0 v7 registry is not imported
and does not supply a fallback test outcome.

## Distinct validation outcomes

1. **Development:** native editor/elaboration may retain errors or
   `sorry`; not completed proof.
2. **Ordinary checked source:** complete relevant checking, with
   declared assumptions/runtime interfaces classified.
3. **Checked theorem:** precise elaborated proposition and actual
   kernel evidence, conditional on transitive assumptions.
4. **Source-verified:** named policy/spec, evidence for required
   coverage/effects/erasure/termination and assumption closure.
5. **Execution-correspondence-verified:** additional checked
   correspondence to a specified generated artifact/layer.

`#ps0_evidence` does not issue any verified label. A stronger
verified-output policy may refuse an otherwise valid ordinary
unsafe, partial, effectful or axiomatic program; that refusal
must not redefine the PS0 v1 source language.

## High-priority conformance probes

- Native `axiom`, unsafe/partial/`noncomputable`, bodyless
  `opaque` and development `sorry` (native classification).
- Macros, syntax categories, custom elaborators, dynamic
  attribute/deriving registrations, and quotations whose native
  category data must not be globally PS-rewritten.
- Explicit and implicit modern modules, `prelude`, public/meta/all
  import flags and hidden vs exposed public bodies.
- Native value-form instances, imported priority handlers,
  structural and nonstructural recursion, monadic `if let ←`,
  zipped loops, native tactics and semicolon control.
- ProofScript comma-call/tuple/nullary and binder-specific
  source ownership, matching and braced syntax (``0B–5).
- Source/claim boundary tests and the R2 witnesses, including
  per-phase diagnostic or AST semantics checks.

## Backend acceptance (separate from v1 language)

The Nat-only JS backend emits `.js`, `.d.ts` and `.js.map`
from a deliberately closed runtime IR. It is **not** a full
v1 language implementation and does not issue a verified JS
certificate. CI must demonstrate exact Nat arithmetic, type
signatures, source-map positions, deterministic emission,
refusal of unsupported constructs and runtime semantics.

See [PS0_V1_IMPLEMENTATION_PLAN.md](PS0_V1_IMPLEMENTATION_PLAN.md)
for remaining architecture gates and [AI_WORK_STATE.md](AI_WORK_STATE.md)
for the latest development handoff.


## Historical adapter milestones

The dated entries below preserve the earlier candidate scope. Their pending
wording is historical; current qualification, generalized mapped operands and
compiler-source fixed-point results are recorded above and in the exact JSON ledgers.

### PS0 v1 host psTerm postfix-call extension — 16 October 2026

Implemented a first PS-owned, **nonempty identifier-head** adjacent-call
source production in `PS0/HostCategories.lean`. It uses Lean's
`noWs` lexical/position-sensitive parser to distinguish a PS postfix
from a spaced native application. The separate `psCallArg` category
captures positional and named host operands.

The explicit `PS0.Syntax.lower` bridge lowers this source category
recursively to a native `Lean.Parser.Term.app` node, preserving the
argument tree. Named parameters use the genuine
`Lean.Parser.Term.namedArgument` category and reject duplicate names
or positional arguments after named parameters. No source-string
transpilation, name resolution or typechecker fork was added.
Native subtrees remain unmodified and other native, quotation and
DSL categories retain their own syntax ownership.

**Bounded scope:** identifier-head calls with nonempty argument lists
in **explicit host-category extension operands**. Full standard
declaration/tactic/do `psTerm` operand wiring, generalized callable
postfix heads, source-nullary completion, optional trailing commas,
parser ambiguity reconciliation and source-provenance verification
remain pending. Existing native term macros may support some source
forms but do not qualify the v1 host-category contract by themselves.

Candidate tests: `tests/v1/host_postfix_calls.ps` exercises
two-argument, nested, tuple-preserving and named calls, and an
extension verifying it receives the raw host-call syntax before
lowering. Separate negative fixtures assert the expected
`PS0V1-CALL-ORDER` and `PS0V1-CALL-NAMED` diagnostic categories.
Five relevant `v1-coverage.json` cases have new candidate links;
all remain `PENDING` until actually qualified by pinned Lean CI.

The canonical normative PS0 v1 R2 document remains unchanged.


### Standard declaration-body psTerm integration — 16 October 2026

PS0 now provides owned source-command forms for **typed** `function` and
`const` bodies whose RHS category is `psTerm` rather than silently taking a
native `term` operand. These forms have higher source-parser priority than
the older partial native-term-backed alias forms. They call the shared
`PS0.Syntax.lower` bridge, constructing real native Lean declarations with
the existing source binder/Unit sugar and ordinary Lean elaboration.

`tests/v1/standard_host_declarations.ps` exercises composed and nested
adjacent calls, reordered named arguments, trailing commas, a
partially applied function, and const initializers. Negative fixtures
`standard_host_order_negative.ps` and
`standard_host_duplicate_negative.ps` demand their specific
`PS0V1-CALL-ORDER`/`PS0V1-CALL-NAMED` rejections; a separate comma-only
fixture must not pass. These tests are **not** current CI PASS receipts.

The Lean-native Nat-only JS backend now recognizes the same new
`psTerm` body nodes, lowering only prior, exact-arity, monomorphic Nat
function calls and constant references into its closed typed IR.
`tests/js/nat_mvp.ps` includes calls with trailing commas in typed
`function` and `const` source forms, with a Node/TypeScript check in CI.
Broader JS semantics or proof-of-runtime-preservation are not claimed.

**Unfinished:** inferred-result declarations, dependent type/binder
slots, standard native `def` and `theorem` RHS, native tactic/do/contract
operands, complete high-postfix call heads, empty-call type-directed
completion inside `psTerm`, ambiguous parse coalescence, expression
source-provenance proof, and imported extension/DSL boundaries.
Only these two typed declaration aliases have migrated standard
body operands. Native `.lean` is unaffected.

The v1 coverage ledger has seven additional **standard-operand
candidate fixture links** on existing call-case IDs, not seven new
requirements or qualifying PASS records. All 242 entries remain
unqualified until an exact-commit Lean 4.35.0 CI result is examined.


### Inferred-result and private source alias parity

The same explicit `psTerm` standard-body adapter now covers
`function` and `const` with either a declared result type or Lean-inferred
result, plus typed/inferred `private function` and `private const`.
Inferred declarations reuse the official Lean elaborator, while source
`function f()` retains the synthetic required `Unit` binder; ordinary
native `def` and `.lean` remain unchanged.

`tests/v1/standard_host_declarations.ps` includes Lean `rfl`
oracles for the public/private and inferred variants, typed
host-call composition, and the source-nullary Unit conversion.
The existing Nat-only JS backend continues to accept the checked
typed/public subset and explicitly rejects inferred/private exports
until its IR/export contract is widened. This split is backend
capability, not a PS0 v1 language restriction.

**Implementation code and test fixtures are committed but still
unqualified:** no actual Lean 4.35.0 build or test run has been observed
for the branch. No v1 requirement was promoted to PASS.

