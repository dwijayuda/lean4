// Copyright (c) 2026 ProofScript contributors. All rights reserved.
// PSV0 is an independent experiment, not the PS0 compiler.
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const RESERVED = new Set(
  'as async await break case catch class const continue debugger default delete do else enum export extends false finally for function if import in instanceof interface let new null of package private protected public return static super switch this throw true try typeof var void while with yield arguments eval def theorem axiom sorry unsafe partial namespace end Nat Bool'.split(' ')
);
const OPERATORS = new Map([['+', 10], ['-', 10], ['*', 20]]);

function reject(message) { throw new Error('PSV0: ' + message); }
function nameOK(name, line) {
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) || RESERVED.has(name) || /^psv0/i.test(name)) {
    reject('unsupported or reserved identifier "' + name + '" on line ' + line);
  }
  return name;
}
function tokenize(expression, line) {
  const tokens = [];
  const pattern = /[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[()+*\-]/y;
  let index = 0;
  while (index < expression.length) {
    if (/\s/.test(expression[index])) { index++; continue; }
    pattern.lastIndex = index;
    const match = pattern.exec(expression);
    if (!match) reject('unsupported expression token at line ' + line + ', column ' + (index + 1));
    tokens.push(match[0]);
    index = pattern.lastIndex;
  }
  return tokens;
}
function parseExpression(source, parameters, line) {
  const tokens = tokenize(source, line);
  let at = 0;
  function atom() {
    const token = tokens[at++];
    if (token === '(') {
      const result = expression(0);
      if (tokens[at++] !== ')') reject('unclosed parenthesis on line ' + line);
      return result;
    }
    if (token && /^[0-9]+$/.test(token)) {
      if (token.length > 1024) reject('integer literal exceeds the 1024 digit limit on line ' + line);
      return { kind: 'nat', value: BigInt(token).toString() };
    }
    if (token && parameters.has(token)) return { kind: 'var', name: token };
    reject('unknown variable or invalid expression "' + (token ?? '<end>') + '" on line ' + line);
  }
  function expression(minimum) {
    let left = atom();
    while (OPERATORS.has(tokens[at]) && OPERATORS.get(tokens[at]) >= minimum) {
      const op = tokens[at++];
      const right = expression(OPERATORS.get(op) + 1);
      left = { kind: 'bin', op, left, right };
    }
    return left;
  }
  if (tokens.length === 0) reject('empty expression on line ' + line);
  const result = expression(0);
  if (at !== tokens.length) reject('unexpected token "' + tokens[at] + '" on line ' + line);
  return result;
}
export function parse(source) {
  if (typeof source !== 'string') reject('source must be text');
  const declarations = [];
  const seen = new Set();
  let namespace = null;
  let ended = false;
  for (const [index, raw] of source.split(/\r?\n/).entries()) {
    const line = index + 1;
    const text = raw.split('--', 1)[0].trim();
    if (!text) continue;
    if (ended) reject('unexpected code after end on line ' + line);
    const ns = /^namespace\s+(\S+)$/.exec(text);
    if (ns) {
      if (namespace !== null || declarations.length) reject('namespace must occur once before functions on line ' + line);
      namespace = nameOK(ns[1], line);
      continue;
    }
    const end = /^end\s+(\S+)$/.exec(text);
    if (end) {
      if (namespace === null || end[1] !== namespace) reject('mismatched namespace end on line ' + line);
      ended = true;
      continue;
    }
    const match = /^function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)\s*:\s*Nat\s*:=\s*(.+)$/.exec(text);
    if (!match) reject('unsupported declaration on line ' + line + '; PSV0 only accepts single-line Nat functions');
    const name = nameOK(match[1], line);
    if (seen.has(name)) reject('duplicate function "' + name + '" on line ' + line);
    seen.add(name);
    const params = [];
    if (match[2].trim()) {
      for (const part of match[2].split(',')) {
        const p = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*Nat\s*$/.exec(part);
        if (!p) reject('expected parameter name: Nat on line ' + line);
        const pName = nameOK(p[1], line);
        if (params.includes(pName)) reject('duplicate parameter "' + pName + '" on line ' + line);
        params.push(pName);
      }
    }
    const body = parseExpression(match[3], new Set(params), line);
    declarations.push({ name, params, body, line });
  }
  if (namespace !== null && !ended) reject('missing end ' + namespace);
  if (declarations.length === 0) reject('no supported functions found');
  return { namespace, declarations };
}
function emitExpr(node, language) {
  if (node.kind === 'nat') return node.value + (language === 'lean' ? '' : 'n');
  if (node.kind === 'var') return node.name;
  const left = emitExpr(node.left, language);
  const right = emitExpr(node.right, language);
  if (node.op === '-' && language !== 'lean') return 'psv0NatSub(' + left + ', ' + right + ')';
  return '(' + left + ' ' + node.op + ' ' + right + ')';
}
export function transpile(source) {
  const ast = parse(source);
  const lean = [
    '-- Generated by PSV0; Lean checking does not prove target-language equivalence.',
    ...(ast.namespace ? ['namespace ' + ast.namespace, ''] : []),
    ...ast.declarations.flatMap(d => [
      'def ' + d.name + ' ' + d.params.map(p => '(' + p + ' : Nat)').join(' ') +
      ' : Nat := ' + emitExpr(d.body, 'lean'), ''
    ]),
    ...(ast.namespace ? ['end ' + ast.namespace, ''] : [])
  ].join('\n');
  function emitTarget(typescript) {
    const lang = typescript ? 'ts' : 'js';
    const natArg = typescript ? 'value: bigint, label: string' : 'value, label';
    const natReturn = typescript ? ': bigint' : '';
    const helper = [
      '// Generated by PSV0. Target semantics are not formally certified.',
      'function psv0AssertNat(' + natArg + ')' + natReturn + ' {',
      '  if (typeof value !== "bigint" || value < 0n) throw new TypeError("Expected Nat bigint: " + label);',
      '  return value;',
      '}',
      'function psv0NatSub(' + (typescript ? 'a: bigint, b: bigint' : 'a, b') + ')' + natReturn + ' {',
      '  return a >= b ? a - b : 0n;',
      '}',
      ''
    ];
    return [...helper, ...ast.declarations.flatMap(d => {
      const args = d.params.map(p => p + (typescript ? ': bigint' : '')).join(', ');
      return [
        'export function ' + d.name + '(' + args + ')' + natReturn + ' {',
        ...d.params.map(p => '  ' + p + ' = psv0AssertNat(' + p + ', "' + p + '");'),
        '  return ' + emitExpr(d.body, lang) + ';',
        '}', ''
      ];
    })].join('\n');
  }
  return { lean, ts: emitTarget(true), js: emitTarget(false), ast };
}
function sha256(content) { return createHash('sha256').update(content).digest('hex'); }
function command(bin, args, cwd) {
  const result = spawnSync(bin, args, { cwd, encoding: 'utf8', timeout: 120000, maxBuffer: 4 * 1024 * 1024, shell: false });
  if (result.error || result.status !== 0 || result.signal) {
    reject('checker ' + bin + ' failed: ' + (result.error?.message ?? ((result.stderr || result.stdout || '') + ' (status ' + result.status + ')')));
  }
  return (result.stdout || '').trim();
}
function usage() {
  return 'Usage: node psv0/src/cli.mjs INPUT.ps --out DIRECTORY [--target lean,ts,js] [--mode fast|strict|verified] [--proof PROOF.lean] [--lean PATH] [--tsc PATH]\n';
}
function options(argv) {
  const result = { target: 'lean,ts,js', mode: 'fast', lean: 'lean', tsc: 'tsc' };
  const allowed = new Map([['--out', 'out'], ['--target', 'target'], ['--mode', 'mode'], ['--proof', 'proof'], ['--lean', 'lean'], ['--tsc', 'tsc']]);
  const provided = new Set();
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (allowed.has(arg)) {
      const key = allowed.get(arg);
      if (provided.has(key) || i + 1 === argv.length || argv[i + 1].startsWith('--')) reject('invalid or duplicated option ' + arg);
      provided.add(key);
      result[key] = argv[++i];
    } else if (!arg.startsWith('-') && !result.input) result.input = arg;
    else reject('unexpected argument ' + arg);
  }
  if (!result.input || !result.out || !result.input.endsWith('.ps')) reject(usage());
  if (!['fast', 'strict', 'verified'].includes(result.mode)) reject('invalid mode ' + result.mode);
  if (result.mode === 'verified') reject('verified mode is not implemented: no independently checked source-to-target semantics theorem exists');
  if (result.proof && result.mode !== 'strict') reject('--proof requires --mode strict');
  const targets = result.target.split(',');
  if (targets.some(t => !['lean', 'ts', 'js'].includes(t)) || new Set(targets).size !== targets.length || targets.length === 0) reject('unsupported or duplicate targets');
  result.targets = [...new Set(['lean', ...targets])];
  return result;
}
export function build(argv) {
  const opt = options(argv);
  const sourcePath = resolve(opt.input);
  const out = resolve(opt.out);
  const stem = basename(sourcePath, '.ps');
  nameOK(stem, 1);
  const source = readFileSync(sourcePath, 'utf8');
  const generated = transpile(source);
  const proof = opt.proof ? readFileSync(resolve(opt.proof), 'utf8') : null;
  const parent = dirname(out);
  mkdirSync(parent, { recursive: true });
  if (existsSync(out)) reject('output directory already exists: ' + out);
  const stage = mkdtempSync(join(parent, '.psv0-stage-'));
  let published = false;
  try {
    const text = { lean: generated.lean, ts: generated.ts, js: generated.js };
    const ext = { lean: '.lean', ts: '.ts', js: '.js' };
    const hashes = {};
    for (const target of opt.targets) {
      const file = stem + ext[target];
      writeFileSync(join(stage, file), text[target], { flag: 'wx' });
      hashes[file] = sha256(text[target]);
    }
    const versions = { node: process.version };
    if (opt.mode === 'strict') {
      const checkFile = 'PSV0Check.lean';
      writeFileSync(join(stage, checkFile), generated.lean + '\n' + (proof ?? ''), { flag: 'wx' });
      versions.lean = command(opt.lean, ['--version'], stage);
      command(opt.lean, [checkFile], stage);
      if (opt.targets.includes('ts')) {
        versions.typescript = command(opt.tsc, ['--version'], stage);
        command(opt.tsc, ['--noEmit', '--strict', '--target', 'ES2020', '--module', 'ES2020',
          '--skipLibCheck', '--pretty', 'false', stem + '.ts'], stage);
      }
      if (opt.targets.includes('js')) command(process.execPath, ['--check', stem + '.js'], stage);
      rmSync(join(stage, checkFile));
    }
    const manifest = {
      schema: 'psv0-build-v0',
      mode: opt.mode,
      assurance: opt.mode === 'strict' ? 'lean-checked-target-unverified' : 'unverified',
      source: { file: basename(sourcePath), sha256: sha256(source) },
      proof: proof === null ? null : { file: basename(opt.proof), sha256: sha256(proof) },
      outputs: hashes,
      toolchain: versions,
      source_to_lean_equivalence_proven: false,
      target_semantics_proven: false
    };
    writeFileSync(join(stage, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
    if (existsSync(out)) reject('output directory appeared during build: ' + out);
    renameSync(stage, out);
    published = true;
    return manifest;
  } finally {
    if (!published) rmSync(stage, { recursive: true, force: true });
  }
}
const invoked = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) {
  try {
    if (process.argv.includes('--help')) process.stdout.write(usage());
    else {
      const result = build(process.argv.slice(2));
      process.stdout.write('PSV0: ' + result.assurance + '\n');
    }
  } catch (error) {
    process.stderr.write(error.message + '\n');
    process.exitCode = 1;
  }
}
