#!/usr/bin/env python3
"""Reviewed-fixture PS0 Nat2 vertical slice; Linux Actions only.

The Lean extractor and candidate files do not authorize publication. Two
independent official comparator invocations, exact candidate validation,
a real TS consumer and both runtime executions are required. The explicit
conditional profile trusts this host and the target realization; it is NOT
a hostile-build sandbox or a formally verified serializer/runtime.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Sequence

LEAN_PIN = "eb6cafb7290e8bd5f2937522d8d804f58f02bafc"
PROFILE = "conditional-nat2-reviewed-v0"
ROOT = "Inventory.remaining"
AXIOMS = ["propext", "Quot.sound", "Classical.choice"]
SCHEMA = "ps0-nat2-candidate/1"
MAX_BYTES = 65536
NODE_VERSION = "v22.23.3"
TSC_VERSION = "Version 5.7.3"


class Refusal(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular_bytes(path: Path, limit: int = MAX_BYTES) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise Refusal(f"PS0-FILE: not a regular input: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise Refusal(f"PS0-FILE: cannot open regular input: {path}") from exc
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise Refusal(f"PS0-FILE: not a regular input: {path}")
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise Refusal(f"PS0-SIZE: oversized input: {path}")
    return data


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("PS0-JSON: duplicate object key")
        result[key] = value
    return result


def validate_ir(value: Any, depth: int = 0, budget: list[int] | None = None) -> list[Any]:
    if budget is None:
        budget = [256]
    budget[0] -= 1
    if depth > 32 or budget[0] < 0:
        raise Refusal("PS0-IR-BUDGET: tree too large")
    if not isinstance(value, list) or not value or not isinstance(value[0], str):
        raise Refusal("PS0-IR: malformed node")
    tag = value[0]
    if tag in {"first", "second"} and len(value) == 1:
        return value
    if tag == "literal" and len(value) == 2:
        n = value[1]
        if not isinstance(n, str) or len(n) > 1024 or re.fullmatch(r"0|[1-9][0-9]*", n) is None:
            raise Refusal("PS0-IR-LITERAL: expected bounded canonical Nat decimal")
        return value
    if tag in {"add", "mul", "sub"} and len(value) == 3:
        validate_ir(value[1], depth + 1, budget)
        validate_ir(value[2], depth + 1, budget)
        return value
    raise Refusal("PS0-IR-OP: unknown primitive or wrong arity")


def lean_expr(ir: list[Any]) -> str:
    tag = ir[0]
    if tag in {"first", "second"}:
        return "." + tag
    if tag == "literal":
        return f"(.literal {ir[1]})"
    return f"(.{tag} {lean_expr(ir[1])} {lean_expr(ir[2])})"


def target_size(ir: list[Any]) -> int:
    """Saturating byte count before expanding repeated subtraction operands.

    Call only after validate_ir. Every emitted atom is ASCII. Counting the
    tree does not allocate the potentially exponential target expression.
    """
    tag = ir[0]
    if tag == "first":
        return 5
    if tag == "second":
        return 9
    if tag == "literal":
        return len(ir[1]) + 1
    children = target_size(ir[1]) + target_size(ir[2])
    return min(MAX_BYTES + 1, 2 * children + 21 if tag == "sub" else children + 5)


def target_expr(ir: list[Any]) -> str:
    tag = ir[0]
    if tag == "first":
        return "stock"
    if tag == "second":
        return "requested"
    if tag == "literal":
        return ir[1] + "n"
    left, right = target_expr(ir[1]), target_expr(ir[2])
    if tag == "sub":
        return f"(({left} >= {right}) ? ({left} - {right}) : 0n)"
    return f"({left} {'+' if tag == 'add' else '*'} {right})"


def expected_source(ir: list[Any], typed: bool) -> bytes:
    validate_ir(ir)
    # Reserve more than the complete fixed JS/TS wrapper before allocating.
    if target_size(ir) + 512 > MAX_BYTES:
        raise Refusal("PS0-OUTPUT-SIZE: target expansion too large")
    args = "stock: bigint, requested: bigint" if typed else "stock, requested"
    ret = ": bigint" if typed else ""
    text = (
        "// PS0 experimental conditional Nat2 slice; see evidence.json.\n"
        f"export function remaining({args}){ret} {{\n"
        '  if (typeof stock !== "bigint" || stock < 0n) throw new TypeError("Expected Nat bigint: stock");\n'
        '  if (typeof requested !== "bigint" || requested < 0n) throw new TypeError("Expected Nat bigint: requested");\n'
        f"  return {target_expr(ir)};\n"
        "}\n"
    ).encode()
    if len(text) > MAX_BYTES:
        raise Refusal("PS0-OUTPUT-SIZE: target expansion too large")
    return text


def read_candidate(directory: Path) -> tuple[list[Any], dict[str, bytes]]:
    if directory.is_symlink() or not directory.is_dir():
        raise Refusal("PS0-CANDIDATE: missing private candidate directory")
    names = {p.name for p in directory.iterdir()}
    if names != {"ir.json", "inventory.js", "inventory.ts"}:
        raise Refusal("PS0-CANDIDATE: missing or unexpected files")
    files = {name: regular_bytes(directory / name) for name in sorted(names)}
    try:
        payload = json.loads(files["ir.json"], object_pairs_hook=unique_object)
    except (ValueError, UnicodeError) as exc:
        raise Refusal("PS0-JSON: malformed candidate") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema", "root", "ir"}:
        raise Refusal("PS0-CANDIDATE: invalid envelope")
    if payload["schema"] != SCHEMA or payload["root"] != ROOT:
        raise Refusal("PS0-CANDIDATE: wrong schema or source root")
    ir = validate_ir(payload["ir"])
    for name, typed in [("inventory.js", False), ("inventory.ts", True)]:
        if files[name] != expected_source(ir, typed):
            raise Refusal(f"PS0-ARTIFACT: {name} does not encode the proposed IR")
    return ir, files


# Only the exact generated fragment is tokenized here. This is NOT a JS parser.
# Canonical candidate validation already fixes its grammar and all identifiers.
TOKEN = re.compile(r'//[^\n]*|"(?:[^"\\]|\\.)*"|[A-Za-z_][A-Za-z_0-9]*|[0-9]+n|!==|>=|\|\||[{}(),;:<+*?\-]')


def target_tokens(data: bytes) -> list[str]:
    text = data.decode("utf-8")
    tokens: list[str] = []
    pos = 0
    for match in TOKEN.finditer(text):
        if text[pos:match.start()].strip():
            raise Refusal("PS0-TS-ERASURE: unexpected token")
        token = match.group()
        if not token.startswith("//"):
            tokens.append(token)
        pos = match.end()
    if text[pos:].strip():
        raise Refusal("PS0-TS-ERASURE: trailing unknown token")
    return tokens


def run(command: Sequence[str], cwd: Path, log: Path, code: str) -> str:
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(list(command), cwd=cwd, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=900, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log.write_text(f"COMMAND: {list(command)!r}\n{exc}\n")
        raise Refusal(f"{code}: tool unavailable, timed out or failed to start; {log}") from exc
    log.write_text(f"COMMAND: {list(command)!r}\nEXIT: {result.returncode}\n"
                   f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    if result.returncode:
        raise Refusal(f"{code}: exit {result.returncode}; inspect {log}")
    return result.stdout


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def comparator_config(challenge: str, solution: str, theorems: list[str]) -> str:
    # definition_names is deliberately omitted: upstream uses it for definition
    # holes, not for a generic list of bodies whose hashes should be compared.
    return json.dumps({"challenge_module": challenge, "solution_module": solution,
                       "theorem_names": theorems, "permitted_axioms": AXIOMS}, indent=2) + "\n"


def challenge_goal(name: str, proposition: str) -> str:
    """Upstream comparator requires theorem/theorem declaration-kind parity.

    This is a goal template, never solution evidence. The pinned comparator
    compares its exact statement and dependencies, then checks axioms and
    replays ONLY the solution export. The solution may not import a challenge;
    sorryAx remains forbidden by AXIOMS and the proof-hole negative test.
    """
    return f"theorem {name} {proposition} := by sorry\n"


def snapshot_files(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".lake" in relative.parts:
            continue
        if path.is_symlink():
            raise Refusal(f"PS0-SNAPSHOT: symbolic-link input: {relative}")
        if path.is_file():
            result[str(relative)] = digest(regular_bytes(path, 1024 * 1024))
    return result


def verify_snapshot(root: Path, expected: dict[str, str],
                    allowed_new: Sequence[str] = ()) -> dict[str, str]:
    actual = snapshot_files(root)
    if any(actual.get(name) != value for name, value in expected.items()):
        raise Refusal("PS0-SNAPSHOT: an identified input changed or disappeared")
    if set(actual) - set(expected) - set(allowed_new):
        raise Refusal("PS0-SNAPSHOT: unexpected input added")
    return actual


def prepare_workspace(root: Path, work: Path, source: bytes, proof: bytes) -> dict[str, str]:
    work.mkdir(parents=True, exist_ok=False)
    vendor = work / ".lake/packages/ps0"
    vendor.mkdir(parents=True)
    # Snapshot only package inputs, never existing binaries, caches or build trees.
    for path in root.glob("*.lean"):
        shutil.copyfile(path, vendor / path.name)
    shutil.copytree(root / "PS0", vendor / "PS0")
    for name in ["lakefile.toml", "lean-toolchain", "lake-manifest.json"]:
        shutil.copyfile(root / name, vendor / name)
    write(work / "lean-toolchain", "leanprover/lean4:v4.35.0\n")
    libraries = ["Admitted", "proofs", "ChallengeSource", "SourceProof", "Candidate", "Challenge", "Solution"]
    config = ('name = "ps0_verified_inventory"\nversion = "0.0.0"\n'
              'defaultTargets = ["Solution"]\n\n[[require]]\nname = "ps0"\n'
              'path = ".lake/packages/ps0"\n')
    config += "".join(f'\n[[lean_lib]]\nname = "{name}"\n' for name in libraries)
    write(work / "lakefile.toml", config)
    (work / "source.ps").write_bytes(source)
    # A bounded import-free headerless-source harness, not general translation.
    # Original body bytes are preserved; PS0's own parser/macros elaborate them.
    header = b"module\nimport PS0.Policy\npublic section\n"
    (work / "Admitted.lean").write_bytes(header + source + b"\n#ps0_evidence\n")
    (work / "proofs").mkdir()
    (work / "proofs/Inventory.lean").write_bytes(proof)
    # Public interface names and private body access are different imports.
    # `public import all` is not a legal substitute in modern Lean modules.
    prefix = "module\npublic import Admitted\nimport all Admitted\npublic section\n"
    proposition = "(stock requested : Nat) : Inventory.remaining stock requested = stock - requested"
    write(work / "ChallengeSource.lean", prefix + challenge_goal("source_spec", proposition))
    write(work / "SourceProof.lean",
          "module\npublic import Admitted\nimport all Admitted\nimport proofs.Inventory\nimport PS0.Verified.Extract\npublic section\n"
          + "theorem source_spec " + proposition + " := InventoryProof.remaining_spec stock requested\n"
          + "#ps0_extract Inventory.remaining\n")
    write(work / "source-comparator.json", comparator_config("ChallengeSource", "SourceProof", ["source_spec"]))
    return snapshot_files(vendor)


def write_correspondence(work: Path, ir: list[Any]) -> None:
    validate_ir(ir)
    write(work / "Candidate.lean", "module\npublic import PS0.Verified.Core\npublic section\n"
          f"@[expose] def candidateIR : PS0.Verified.NatExpr := {lean_expr(ir)}\n")
    prelude = "module\npublic import Admitted\nimport all Admitted\npublic import Candidate\nimport all Candidate\n"
    statements = {
        "extraction_correct": "(stock requested : Nat) : candidateIR.eval stock requested = Inventory.remaining stock requested",
        "target_correct": "(stock requested : Nat) : (PS0.Verified.lower candidateIR).eval stock requested = some (Inventory.remaining stock requested)",
        "release_spec": "(stock requested : Nat) : (PS0.Verified.lower candidateIR).eval stock requested = some (stock - requested)",
    }
    challenge = prelude + "public section\n"
    for name, proposition in statements.items():
        challenge += challenge_goal(name, proposition)
    solution = prelude + "import proofs.Inventory\npublic section\n"
    solution += "theorem extraction_correct " + statements["extraction_correct"] + " := by rfl\n"
    solution += "theorem target_correct " + statements["target_correct"] + " := by\n  rw [PS0.Verified.lower_correct, extraction_correct]\n"
    solution += "theorem release_spec " + statements["release_spec"] + " := by\n  rw [target_correct, InventoryProof.remaining_spec]\n"
    write(work / "Challenge.lean", challenge)
    write(work / "Solution.lean", solution)
    write(work / "target-comparator.json", comparator_config("Challenge", "Solution", list(statements)))


def publish_noreplace(stage: Path, output: Path) -> None:
    """Linux atomic no-replacement rename, including the empty-directory race."""
    if sys.platform != "linux":
        raise Refusal("PS0-PUBLISH: Linux no-replacement publication required")
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise Refusal("PS0-PUBLISH: renameat2 unavailable; no unsafe fallback")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(stage), -100, os.fsencode(output), 1) != 0:
        raise Refusal(f"PS0-PUBLISH: atomic no-replacement rename refused ({os.strerror(ctypes.get_errno())})")


def check_targets(root: Path, work: Path, files: dict[str, bytes], logs: Path) -> dict[str, str]:
    tsc = Path(os.environ.get("PS0_TSC", ""))
    if not tsc.is_absolute() or not tsc.is_file():
        raise Refusal("PS0-TSC: PS0_TSC must identify the pinned TypeScript compiler")
    target = work / ".lake/ps0-target-check"
    target.mkdir()
    node_version = run(["node", "--version"], target, logs / "node-version.log", "PS0-NODE").strip()
    ts_version = run(["node", str(tsc), "--version"], target, logs / "ts-version.log", "PS0-TSC").strip()
    if node_version != NODE_VERSION or ts_version != TSC_VERSION:
        raise Refusal("PS0-TARGET-PIN: unsupported Node/TypeScript version")
    tsc_hash = digest(regular_bytes(tsc, 20 * 1024 * 1024))
    harness = root / "tests/proof-linked-runtime.mjs"
    harness_hash = digest(regular_bytes(harness))
    for name in ["inventory.js", "inventory.ts"]:
        (target / name).write_bytes(files[name])
    write(target / "package.json", '{"type":"module"}\n')
    write(target / "consumer.ts", 'import { remaining } from "./inventory.js";\n'
          'const value: bigint = remaining(100n, 30n);\nvoid value;\n'
          '// @ts-expect-error a JS number is not a Nat bigint\nremaining(1, 2n);\n'
          '// @ts-expect-error the result is bigint, not number\nconst wrong: number = remaining(1n, 2n);\nvoid wrong;\n')
    common = ["node", str(tsc), "--strict", "--target", "ES2020", "--module", "ES2020", "--moduleResolution", "node"]
    run(common + ["--noEmit", "consumer.ts"], target, logs / "ts-consumer.log", "PS0-TSC-CONSUMER")
    run(common + ["--declaration", "--outDir", "compiled", "inventory.ts"], target, logs / "ts-compile.log", "PS0-TSC-COMPILE")
    compiled = regular_bytes(target / "compiled/inventory.js")
    if target_tokens(compiled) != target_tokens(files["inventory.js"]):
        raise Refusal("PS0-TS-ERASURE: compiled JS differs beyond formatting/comments")
    declarations = regular_bytes(target / "compiled/inventory.d.ts")
    if declarations != b"export declare function remaining(stock: bigint, requested: bigint): bigint;\n":
        raise Refusal("PS0-TSC-ABI: unexpected declaration interface")
    run(["node", str(harness), str(target / "inventory.js")], target, logs / "js-runtime.log", "PS0-JS-RUNTIME")
    run(["node", str(harness), str(target / "compiled/inventory.js")], target, logs / "ts-runtime.log", "PS0-TS-RUNTIME")
    if digest(regular_bytes(tsc, 20 * 1024 * 1024)) != tsc_hash or digest(regular_bytes(harness)) != harness_hash:
        raise Refusal("PS0-SNAPSHOT: target tool or runtime harness changed")
    files["inventory.d.ts"] = declarations
    files["inventory.from-ts.js"] = compiled
    return {"node": node_version, "typescript": ts_version,
            "tsc_sha256": tsc_hash, "runtime_harness_sha256": harness_hash}


def build(root: Path, example: Path, output: Path, profile: str) -> Path:
    if profile != PROFILE:
        raise Refusal("PS0-POLICY: strict verified execution is unavailable; explicitly select the reviewed conditional profile")
    if sys.platform != "linux":
        raise Refusal("PS0-PLATFORM: independent official sandbox replay requires Linux")
    if output.exists() or output.is_symlink():
        raise Refusal("PS0-OUTPUT-EXISTS: refusing to replace an existing bundle")
    source = regular_bytes(example / "src/Inventory.ps")
    proof = regular_bytes(example / "proofs/Inventory.lean")
    host_path = root / "scripts/proof_linked.py"
    host_hash = digest(regular_bytes(host_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    logs = output.parent / (output.name + "-logs")
    logs.mkdir(exist_ok=False)
    holder = Path(tempfile.mkdtemp(prefix=".ps0-proof-linked-", dir=output.parent))
    work = holder / "work"
    stage = holder / "bundle"
    try:
        vendor_before = prepare_workspace(root, work, source, proof)
        inputs_before = snapshot_files(work)
        # The original CLI remains independently covered; it is not the proof authority.
        run(["lake", "exe", "ps0", "check", str(work / "source.ps")], root, logs / "ps0-check.log", "PS0-SOURCE-CHECK")
        verify_snapshot(work, inputs_before)
        run(["lake", "update"], work, logs / "resolve.log", "PS0-RESOLVE")
        inputs_before = verify_snapshot(work, inputs_before, ["lake-manifest.json"])
        run(["lake", "comparator", "--config", "source-comparator.json"], work, logs / "source-proof.log", "PS0-SOURCE-PROOF")
        verify_snapshot(work, inputs_before)
        ir, files = read_candidate(work / ".lake/ps0-candidate")
        frozen_candidates = {name: digest(data) for name, data in files.items()}
        write_correspondence(work, ir)
        inputs_before = verify_snapshot(work, inputs_before,
                                        ["Candidate.lean", "Challenge.lean", "Solution.lean", "target-comparator.json"])
        run(["lake", "comparator", "--config", "target-comparator.json"], work, logs / "target-proof.log", "PS0-TARGET-PROOF")
        verify_snapshot(work, inputs_before)
        # A stale or rewritten private candidate is never combined with old proofs.
        ir_after, after = read_candidate(work / ".lake/ps0-candidate")
        if ir_after != ir or {n: digest(b) for n, b in after.items()} != frozen_candidates:
            raise Refusal("PS0-SNAPSHOT: candidate changed during proof replay")
        verify_snapshot(work / ".lake/packages/ps0", vendor_before)
        if regular_bytes(work / "source.ps") != source or regular_bytes(work / "proofs/Inventory.lean") != proof:
            raise Refusal("PS0-SNAPSHOT: source/proof bytes changed during build")
        runtimes = check_targets(root, work, files, logs)
        # Check again after target tools, immediately before release staging.
        verify_snapshot(work, inputs_before)
        verify_snapshot(work / ".lake/packages/ps0", vendor_before)
        if digest(regular_bytes(host_path)) != host_hash:
            raise Refusal("PS0-SNAPSHOT: publication host changed")
        _, final_candidates = read_candidate(work / ".lake/ps0-candidate")
        if {n: digest(b) for n, b in final_candidates.items()} != frozen_candidates:
            raise Refusal("PS0-SNAPSHOT: candidate changed during target qualification")
        stage.mkdir()
        for name, data in files.items():
            (stage / name).write_bytes(data)
        write(stage / "package.json", '{"private":true,"type":"module"}\n')
        evidence = {
            "schema": "ps0-proof-linked-inventory/1", "profile": PROFILE,
            "strict_verified_execution": False, "root": ROOT,
            "claim": "source specification and exact IR/target-model correspondence, conditional on reviewed realization",
            "lean_commit": LEAN_PIN, "permitted_axioms": AXIOMS,
            "source_sha256": digest(source), "proof_sha256": digest(proof),
            "compiler_inputs": vendor_before, "challenge_inputs": inputs_before,
            "publication_host_sha256": host_hash,
            "artifacts": {name: digest(data) for name, data in sorted(files.items())},
            "runtime_tools": runtimes,
            "proof_replay": {"source": digest(regular_bytes(logs / "source-proof.log", 20 * 1024 * 1024)),
                             "target": digest(regular_bytes(logs / "target-proof.log", 20 * 1024 * 1024))},
            "assumptions": ["official Lean kernel and the listed logical axioms", "reviewed PS0 source adapters and import-free harness", "reviewed Python validator/publication host", "restricted BigInt model realized by the recorded JS engine", "recorded TypeScript compiler with checked fragment erasure", "sufficient memory/stack/time resources"],
            "not_claimed": ["full R2 conformance", "formal serialization proof", "verified JS engine or tsc", "hostile compile-time-code isolation", "foreign-library correctness", "production release qualification"],
        }
        write(stage / "evidence.json", json.dumps(evidence, sort_keys=True, indent=2) + "\n")
        for path in stage.iterdir():
            with path.open("rb") as stream:
                os.fsync(stream.fileno())
        publish_noreplace(stage, output)
        return output
    finally:
        shutil.rmtree(holder, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--example", type=Path, default=Path("examples/verified-inventory"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        result = build(root, args.example.resolve(), args.out.absolute(), args.profile)
        print(f"PS0-CONDITIONAL-BUNDLE: {result}")
        return 0
    except (Refusal, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
