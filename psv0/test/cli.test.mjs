// Copyright (c) 2026 ProofScript contributors. All rights reserved.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, existsSync, writeFileSync, rmSync, chmodSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { parse, transpile, build } from '../src/cli.mjs';

const SOURCE = 'namespace Inventory\nfunction remaining(stock: Nat, requested: Nat): Nat := stock - requested\nend Inventory\n';
const ERRORS = [
  'function f(x: Int): Nat := x',
  'function f(x: Nat): Nat := x / 2',
  'function f(x: Nat): Nat := unknown',
  'function f(x: Nat): Nat := x + )',
  'function f(x: Nat, x: Nat): Nat := x',
  'function f(x: Nat): Nat := x\nfunction f(y: Nat): Nat := y',
  'namespace N\nfunction f(x: Nat): Nat := x',
  'function f(x: Nat): Nat := x\nend N',
  'function f(x: Nat): Nat := x\n#eval 1',
  'function f(x: Nat): Nat := x + 1\nfunction g(x: Nat): Nat := f(x)',
  'function f(x: Nat): Nat := 1 // 2',
  'function f(x: Nat): Nat := 3.1'
];
test('reject unsupported language and unsupported constructs rather than silently converting them', () => {
  for (const source of ERRORS) assert.throws(() => parse(source), /PSV0:/, source);
});
test('deterministic outputs with mathematical Nat subtraction', () => {
  const first = transpile(SOURCE);
  assert.deepEqual(first, transpile(SOURCE));
  assert.match(first.lean, /def remaining \(stock : Nat\) \(requested : Nat\) : Nat := \(stock - requested\)/);
  assert.match(first.ts, /bigint/);
  assert.match(first.js, /return psv0NatSub\(stock, requested\);/);
});
test('generated JavaScript implements saturating subtraction including large inputs and boundary checks', async () => {
  const result = transpile(SOURCE);
  const module = await import('data:text/javascript;charset=utf-8,' + encodeURIComponent(result.js));
  assert.equal(module.remaining(10n, 3n), 7n);
  assert.equal(module.remaining(3n, 10n), 0n);
  assert.equal(module.remaining(2n ** 100n, 1n), 2n ** 100n - 1n);
  assert.throws(() => module.remaining(10, 3n), TypeError);
  assert.throws(() => module.remaining(-1n, 0n), TypeError);
  assert.throws(() => module.remaining(0n, '1'), TypeError);
});
test('fast mode stages and publishes with explicit unverified manifest', () => {
  const temp = mkdtempSync(join(tmpdir(), 'psv0-test-'));
  try {
    const source = join(temp, 'Inventory.ps');
    writeFileSync(source, SOURCE);
    const out = join(temp, 'result');
    const result = build([source, '--out', out, '--mode', 'fast', '--target', 'lean,ts,js']);
    assert.equal(result.assurance, 'unverified');
    assert.equal(result.source_to_lean_equivalence_proven, false);
    assert.equal(result.target_semantics_proven, false);
    assert.ok(readFileSync(join(out, 'Inventory.lean'), 'utf8').includes('def remaining'));
    assert.equal(JSON.parse(readFileSync(join(out, 'Inventory.ir.json'), 'utf8')).schema, 'psv0-ir-v0');
    assert.equal(result.outputs['Inventory.ir.json'].length, 64);
    assert.ok(readFileSync(join(out, 'Inventory.ts'), 'utf8').includes('bigint'));
    assert.ok(readFileSync(join(out, 'Inventory.js'), 'utf8').includes('psv0NatSub'));
    assert.throws(() => build([source, '--out', out]), /already exists/);
  } finally { rmSync(temp, { recursive: true, force: true }); }
});
test('verified mode is fail closed, not an alias for a Lean syntax check', () => {
  assert.throws(() => build(['input.ps', '--out', 'dest', '--mode', 'verified']), /not implemented/);
});
test('strict mode never publishes if Lean is unavailable', () => {
  const temp = mkdtempSync(join(tmpdir(), 'psv0-strict-'));
  try {
    const source = join(temp, 'Inventory.ps');
    writeFileSync(source, SOURCE);
    const out = join(temp, 'strict');
    assert.throws(() => build([source, '--out', out, '--mode', 'strict', '--lean', '/nonexistent/psv0-lean']), /checker/);
    assert.equal(existsSync(out), false);
  } finally { rmSync(temp, { recursive: true, force: true }); }
});
test('strict and fast modes reject verification claims not supported by evidence', () => {
  assert.throws(() => build(['i.ps', '--out', 'x', '--proof', 'fake.lean']), /requires --mode strict/);
  assert.throws(() => build(['i.ps', '--out', 'x', '--target', 'rust']), /unsupported/);
  assert.throws(() => build(['i.ps', '--out', 'x', '--target', 'ts,ts']), /duplicate/);
});

test('strict bridge artifact is retained and explicitly non-verified (fake checker smoke test only)', () => {
  const temp = mkdtempSync(join(tmpdir(), 'psv0-bridge-smoke-'));
  try {
    const source = join(temp, 'Inventory.ps');
    const fake = join(temp, 'lean-stub.cjs');
    writeFileSync(source, SOURCE);
    writeFileSync(fake, '#!/usr/bin/env node\n' +
      'const fs=require("node:fs");\n' +
      'if(process.argv[2]==="--version"){console.log("FAKE-LEAN-TEST-ONLY");process.exit(0)}\n' +
      'const checked=fs.readFileSync(process.argv[2],"utf8");\n' +
      'if(!checked.includes("theorem psv0_bridge_remaining") || !checked.includes("targetModel_correct"))process.exit(37);\n');
    chmodSync(fake, 0o755);
    const out = join(temp, 'strict');
    const result = build([source, '--out', out, '--mode', 'strict', '--target', 'lean', '--lean', fake]);
    assert.equal(result.assurance, 'lean-checked-target-unverified');
    assert.equal(result.toolchain.lean, 'FAKE-LEAN-TEST-ONLY');
    assert.equal(result.source_to_lean_equivalence_proven, false);
    assert.equal(result.target_semantics_proven, false);
    assert.equal(result.lean_ir_bridge.scope, 'checked-IR-to-generated-Lean-only');
    const checked = readFileSync(join(out, 'PSV0Check.lean'), 'utf8');
    assert.match(checked, /theorem psv0_bridge_remaining/);
    assert.match(checked, /theorem targetModel_correct/);
  } finally { rmSync(temp, { recursive: true, force: true }); }
});
