// Copyright (c) 2026 ProofScript contributors. All rights reserved.
import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluate } from '../src/reference.mjs';
import { renderLeanBridge } from '../src/bridge.mjs';

const id = name => ({ kind: 'var', name });
const literal = value => ({ kind: 'nat', value: String(value) });
const bin = (op, left, right) => ({ kind: 'bin', op, left, right });
const ast = {
  namespace: 'Inventory',
  declarations: [{
    name: 'remaining', params: ['stock', 'requested'],
    body: bin('-', id('stock'), id('requested'))
  }, {
    name: 'total', params: ['x', 'y'],
    body: bin('+', bin('*', id('x'), literal('3')), id('y'))
  }]
};

test('independent IR interpreter gives Nat semantics', () => {
  assert.equal(evaluate(ast, 'remaining', [7n, 2n]), 5n);
  assert.equal(evaluate(ast, 'remaining', [2n, 7n]), 0n);
  assert.equal(evaluate(ast, 'total', [2n ** 60n, 123n]), 3n * 2n ** 60n + 123n);
});
test('reference semantics fail closed on invalid inputs', () => {
  assert.throws(() => evaluate(ast, 'remaining', [-1n, 0n]), TypeError);
  assert.throws(() => evaluate(ast, 'remaining', [1, 0n]), TypeError);
  assert.throws(() => evaluate(ast, 'remaining', [1n]), RangeError);
  assert.throws(() => evaluate(ast, 'missing', [1n]), /unknown function/);
});
test('bridge references exact IR expressions and every function', () => {
  const proof = renderLeanBridge(ast);
  assert.match(proof, /theorem psv0_bridge_remaining/);
  assert.match(proof, /theorem psv0_bridge_total/);
  assert.match(proof, /PSV0Reference\.Expr\.sub \(PSV0Reference\.Expr\.arg 0\) \(PSV0Reference\.Expr\.arg 1\)/);
  assert.match(proof, /PSV0Reference\.Expr\.mul/);
  assert.equal((proof.match(/\bby\n  rfl\b/g) || []).length, 2);
});
test('bridge refuses unknown IR operators', () => {
  const bad = { namespace: null, declarations: [{ name: 'bad', params: ['x'], body: bin('/', id('x'), literal(1)) }] };
  assert.throws(() => renderLeanBridge(bad), /unknown operator/);
});
