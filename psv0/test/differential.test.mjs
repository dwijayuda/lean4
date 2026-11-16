// Copyright (c) 2026 ProofScript contributors. All rights reserved.
// Differential regressions: tests are not a semantic-preservation proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import { transpile } from '../src/cli.mjs';
import { evaluate } from '../src/reference.mjs';

const SOURCE = [
  'namespace Arithmetic',
  'function remaining(stock: Nat, requested: Nat): Nat := stock - requested',
  'function mixed(x: Nat, y: Nat): Nat := (x + 2) * (y + 1) - (x * y)',
  'function zero(): Nat := 0',
  'end Arithmetic'
].join('\n');

async function loadJs(text) {
  return import('data:text/javascript;charset=utf-8,' + encodeURIComponent(text));
}

test('generated JS agrees with independently evaluated Nat IR for deterministic samples', async () => {
  const { ast, js } = transpile(SOURCE);
  const implementation = await loadJs(js);
  const boundaries = [0n, 1n, 2n, 3n, 100n, (2n ** 53n) - 1n, 2n ** 53n, 2n ** 100n];
  let state = 0x123456789abcdefn;
  const next = () => {
    state = (state * 6364136223846793005n + 1442695040888963407n) % (2n ** 128n);
    return state;
  };
  const values = [...boundaries, ...Array.from({ length: 40 }, () => next())];
  for (const [i, x] of values.entries()) {
    for (const y of [0n, 1n, x, values[values.length - 1 - i]]) {
      for (const name of ['remaining', 'mixed']) {
        const expected = evaluate(ast, name, [x, y]);
        assert.equal(implementation[name](x, y), expected, `${name}(${x}, ${y})`);
      }
    }
  }
  assert.equal(implementation.zero(), evaluate(ast, 'zero', []));
});

test('differential oracle detects an intentionally corrupted JS operator', async () => {
  const { ast, js } = transpile(SOURCE);
  const altered = js.replace('return psv0NatSub(stock, requested);', 'return (stock + requested);');
  assert.notEqual(altered, js);
  const implementation = await loadJs(altered);
  assert.notEqual(implementation.remaining(7n, 2n), evaluate(ast, 'remaining', [7n, 2n]));
});
