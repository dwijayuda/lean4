// Copyright (c) 2026 ProofScript contributors. All rights reserved.
// Produce Lean obligations for the parsed PSV0 expression tree.
function expr(node, params) {
  if (node.kind === 'nat') return `(PSV0Reference.Expr.lit ${node.value})`;
  if (node.kind === 'var') {
    const index = params.indexOf(node.name);
    if (index < 0) throw new Error('PSV0: unknown variable in bridge');
    return `(PSV0Reference.Expr.arg ${index})`;
  }
  if (node.kind === 'bin') {
    const operator = new Map([['+', 'add'], ['-', 'sub'], ['*', 'mul']]).get(node.op);
    if (!operator) throw new Error('PSV0: unknown operator in bridge');
    return `(PSV0Reference.Expr.${operator} ${expr(node.left, params)} ${expr(node.right, params)})`;
  }
  throw new Error('PSV0: unknown IR node in bridge');
}

export function renderLeanBridge(ast) {
  return [
    '-- Generated candidate obligations. Lean must independently check every `by rfl`.',
    ...ast.declarations.flatMap(d => {
      const qualifiedName = ast.namespace ? `${ast.namespace}.${d.name}` : d.name;
      const binder = d.params.map(p => `(${p} : Nat)`).join(' ');
      const application = [qualifiedName, ...d.params].join(' ');
      const argumentsList = `[${d.params.join(', ')}]`;
      return [
        `theorem psv0_bridge_${d.name}${binder ? ' ' + binder : ''} :`,
        `    (${application}) = PSV0Reference.Expr.eval ${argumentsList} ${expr(d.body, d.params)} := by`,
        '  rfl', ''
      ];
    })
  ].join('\n');
}
