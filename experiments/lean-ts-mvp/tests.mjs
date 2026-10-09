import assert from "node:assert/strict";
import { increment } from "./dist/increment.js";
import { square } from "./dist/square.js";
import { saturatingSub } from "./dist/saturatingSub.js";

assert.equal(increment(0n), 1n);
assert.equal(increment(20n), 21n);
assert.equal(increment(9007199254740993123456789n), 9007199254740993123456790n);
assert.equal(square(0n), 0n);
assert.equal(square(12n), 144n);
assert.equal(square(123456789123456789n), 15241578780673678515622620750190521n);
assert.equal(saturatingSub(9n, 4n), 5n);
assert.equal(saturatingSub(4n, 9n), 0n);
assert.equal(saturatingSub(0n, 0n), 0n);
assert.throws(() => increment(-1n), RangeError);
assert.throws(() => increment(3), RangeError);

console.log("Lean -> TypeScript 7 -> Node MVP assertions passed");
