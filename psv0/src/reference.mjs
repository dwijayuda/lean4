// Copyright (c) 2026 ProofScript contributors. All rights reserved.
// Executable reference interpretation for PSV0's restricted Nat expression IR.
function nat(value, label) {
  if (typeof value !== 'bigint' || value < 0n) {
    throw new TypeError('PSV0 reference: expected nonnegative bigint for ' + label);
  }
  return value;
}
function interpret(node, environment, depth) {
  if (depth > 512) throw new RangeError('PSV0 reference: expression depth exceeded');
  if (node.kind === 'nat') return nat(BigInt(node.value), 'literal');
  if (node.kind === 'var') {
    if (!environment.has(node.name)) throw new Error('PSV0 reference: missing parameter ' + node.name);
    return environment.get(node.name);
  }
  if (node.kind === 'bin') {
    const a = interpret(node.left, environment, depth + 1);
    const b = interpret(node.right, environment, depth + 1);
    switch (node.op) {
      case '+': return a + b;
      case '*': return a * b;
      case '-': return a >= b ? a - b : 0n;
      default: throw new Error('PSV0 reference: unsupported operator');
    }
  }
  throw new Error('PSV0 reference: unsupported expression');
}
export function evaluate(ast, functionName, argumentsList) {
  const definition = ast.declarations.find(d => d.name === functionName);
  if (!definition) throw new Error('PSV0 reference: unknown function ' + functionName);
  if (definition.params.length !== argumentsList.length) throw new RangeError('PSV0 reference: argument count differs');
  const environment = new Map(definition.params.map((name, i) => [name, nat(argumentsList[i], name)]));
  return interpret(definition.body, environment, 0);
}
