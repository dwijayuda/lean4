import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';

if (process.argv.length !== 3) throw new Error('Expected one generated module path');
const module = await import(pathToFileURL(process.argv[2]).href);
assert.deepEqual(Object.keys(module), ['remaining']);
let observations = 0;
const check = (stock, requested) => {
  const actual = module.remaining(stock, requested);
  const expected = stock >= requested ? stock - requested : 0n;
  assert.equal(actual, expected);
  assert.equal(typeof actual, 'bigint');
  assert.ok(actual >= 0n && actual <= stock);
  if (requested <= stock) assert.equal(actual + requested, stock);
  observations++;
};
for (let stock = 0n; stock <= 25n; stock++) {
  for (let requested = 0n; requested <= 25n; requested++) check(stock, requested);
}
const boundaries = [0n, 1n, 2n, 9007199254740991n, 9007199254740993n, 1n << 64n, 1n << 256n, 1n << 1024n];
for (const stock of boundaries) for (const requested of boundaries) check(stock, requested);
let coerced = false;
const hostile = { [Symbol.toPrimitive]() { coerced = true; return 1n; } };
const invalid = [0, 1.5, NaN, Infinity, -1n, '1', null, undefined, {}, [], hostile];
for (const value of invalid) {
  assert.throws(() => module.remaining(value, 0n), TypeError);
  assert.throws(() => module.remaining(0n, value), TypeError);
}
assert.equal(coerced, false);
console.log(JSON.stringify({kind: 'runtime-regression-not-proof', observations, invalidBoundaryCalls: invalid.length * 2}));
