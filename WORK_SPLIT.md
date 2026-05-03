# ClassC — Phase 3 + 4 Work Split (TypeChecker + Code Generator)

Phases 1 (Lexer) and 2 (Parser) are done. Phases 3 (TypeChecker, 40%) and
4 (Code Generator, 40%) are the remaining 80% of the project. This document
splits the work across four people so that, after a one-person foundation
landing, the other three can work in parallel without fighting over files.

| Person      | Headline                                 | Primary files                                                   |
|-------------|------------------------------------------|-----------------------------------------------------------------|
| **Yuzu**       | Parser prep — the foundation             | `src/parser.py`, `src/tokenizer.py`, `tests/test_parser.py`, `tests/test_tokenizer.py` |
| **Accuraries** | Class table, subtyping, method lookup    | `src/class_table.py`, `tests/test_class_table.py`               |
| **Revamp**     | Typing for expressions and statements    | `src/typechecker.py`, `tests/test_typechecker.py`               |
| **Stealy**     | Code generator (Program → C)             | `src/codegen.py`, `tests/test_codegen.py`, `tests/fixtures/`    |

---

## Why this split is non-blocking

The seam between everyone is the AST + the `ClassTable` API:

```
            ┌──────────────┐
   Yuzu ──▶ │ AST (parser) │ ────────────────────────┐
            └──────────────┘                         │
                  │                                  │
                  ▼                                  ▼
        ┌────────────────────┐              ┌──────────────────┐
Accur. ▶│ class_table.py     │ ◀─ used by ─ │ codegen.py        │ ◀─ Stealy
        │   ClassTable       │              │  Program → C       │
        │   is_subtype()     │              │  (no TC dep)       │
        │   lookup_method()  │              └──────────────────┘
        │   field_layout()   │                       ▲
        │   vtable_layout()  │                       │
        └────────────────────┘                       │
                  ▲                                  │
                  │                                  │
       used by ───┴──────────────┐                   │
                                 │                   │
                          ┌──────┴──────────┐        │
                Revamp ─▶ │ typechecker.py  │        │
                          │  typeof_exp()    │       │
                          │  typecheck_stmt()│       │
                          └─────────────────┘        │
                                                     │
   (Stealy may optionally consume typed AST later, but the v1
    contract is "codegen runs on a parsed Program + ClassTable" —
    no typechecker dependency.)
```

Critical rule for parallelism: **Accuraries publishes the `ClassTable`
public API as stubs on day 1** (each method raises `NotImplementedError`
or returns a sentinel). Revamp and Stealy import that API immediately
and write code that compiles against the shape, even before Accuraries
fills in the bodies. Same trick for `typechecker.py` — Revamp commits
the function signatures + `IllTypedException` in the first PR.

---

## Yuzu — Parser prep & shared scaffolding

**Lands first. Everyone else is blocked on this PR.** Keep it focused so
it can ship in 2–3 days; do not let scope creep into typechecker logic.

### Deliverables

1. **Op sum type** (replaces `BinOpExp.op: str`)
   - Add `PlusOp`, `MinusOp`, `MultiplyOp`, `DivideOp`, `LessThanOp`,
     `EqualsOp` dataclasses to `parser.py`.
   - Define `Op = Union[...]`.
   - Update `_parse_paren_expression` to emit Op nodes via a
     `TokenType → OpClass` map.
   - Update tests that currently assert `result.op == "+"` to use
     `isinstance(result.op, PlusOp)`.

2. **Position tracking on AST nodes**
   - Add `Pos` dataclass with `line`, `col`, and `Pos.from_token(tok)`.
   - Add `pos: Optional[Pos] = field(default=None, compare=False)` to
     every AST dataclass (statements + expressions + definitions).
   - Set `pos` from the first token of each production in the parser.
   - `compare=False` keeps existing `==` assertions working.

3. **`Optional`/`Union` annotations**
   - Define `Expression`, `Statement` union aliases.
   - Replace `object` annotations on `parent`, `super_args`, `else_stmt`,
     `expression` (in `ReturnStmt`).
   - Add return type annotations on `parse_expression`, `parse_statement`,
     etc.

4. **String literal support**
   - Tokenizer: `STRING_LITERAL` token type, `read_string()` with `\n`,
     `\t`, `\\`, `\"` escapes, error on unterminated/embedded newline.
   - Parser: `StringLiteralExp` AST node, branch in `parse_expression`,
     add to `Expression` union.
   - Tests: tokenizer + parser coverage for all the above.

5. **`WORK_SPLIT.md`** — this document.

### Out of scope for Yuzu

- Anything in `src/typechecker.py` or `src/codegen.py` — those files do not
  exist yet. Yuzu does **not** create skeletons for them; the people who
  own those modules create them in their first PR.
- No nominal wrappers for `Variable` / `ClassName` / `MethodName`.
- No `String` class implementation — only the literal plumbing.

### Coverage target

≥ 98% on `src/`. The new code (Op classes, `Pos`, `StringLiteralExp`,
`read_string`) is small and trivially covered by the new tests.

### Done when

- All 110 existing tests still pass.
- New tests for Op nodes, position attachment, string literals all pass.
- `pyright` / `mypy` (if configured) is happy with the new annotations.

---

## Accuraries — Class table, subtyping, method dispatch

**Starts when Yuzu lands.** Owns the `ClassTable` module, which is the
shared infrastructure between TypeChecker and Code Generator. Ship the
public API as stubs in PR #1 so Revamp and Stealy aren't blocked.

### Deliverables

1. **`ClassTable` construction**
   - `ClassTable.from_program(p: Program) -> ClassTable`
   - Walks `program.classes`, builds a `dict[class_name, ClassInfo]`.
   - Detects duplicate class names, duplicate field/method names within a
     class, and unknown parent classes.
   - Detects inheritance cycles (`A extends B extends A`).
   - Implicitly inserts `Object` as the root.

2. **Subtype relation** — `is_subtype(t1: Type, t2: Type) -> bool`
   - Reflexive: every type is a subtype of itself.
   - Transitive class chain via `parent`.
   - `Int`/`Boolean`/`Void` only relate to themselves.
   - Every class type is a subtype of `Object`.

3. **Field layout for inheritance**
   - `field_layout(class_name) -> list[(name, Type)]`
   - Returns parent fields first, then this class's fields, in declared
     order. Used by both TC (for `this.foo` typing later) and codegen
     (for struct member ordering).

4. **Method lookup with overloading**
   - `lookup_method(class_name, method_name, arg_types) -> MethodSig`
   - Walks up the class chain.
   - When multiple overloads with the right name exist, picks the one
     whose parameter types are most-specific subtypes of `arg_types`.
   - Raises `IllTypedException` (from `typechecker.py`) on ambiguity or
     no match.

5. **Vtable layout**
   - `vtable_layout(class_name) -> list[MethodSig]`
   - Parent's vtable order first, with overrides slotted in place; new
     methods appended after. Pure infrastructure for Stealy.

6. **Constructor / `super` validation hook**
   - `super_arg_types(class_name) -> list[Type] | None`
   - Returns the parent constructor's parameter types, or `None` if no
     parent. Revamp uses this to typecheck `(super exp*)`.

### Day-1 stub API

```python
# src/class_table.py
class ClassTable:
    @classmethod
    def from_program(cls, p): raise NotImplementedError
    def is_subtype(self, t1, t2): raise NotImplementedError
    def lookup_method(self, cn, mn, arg_types): raise NotImplementedError
    def lookup_field(self, cn, fn): raise NotImplementedError
    def field_layout(self, cn): raise NotImplementedError
    def vtable_layout(self, cn): raise NotImplementedError
    def super_arg_types(self, cn): raise NotImplementedError
```

Land this stub first so Revamp and Stealy can `from class_table import
ClassTable` from day 1.

### Done when

- A representative class hierarchy (Animal/Cat/Dog from `ClassC.docx`)
  passes construction without errors.
- Subtype assertions match the spec (`Cat <: Animal`, `Animal <: Object`,
  `Cat </: Dog`, etc.).
- Method overload resolution picks the most-specific match and rejects
  ambiguous ones.
- Cyclic / duplicate / unknown-parent inputs raise sensible errors.

---

## Revamp — Typechecker for expressions and statements

**Starts as soon as Accuraries' stub lands.** Owns `src/typechecker.py`.
Defines `IllTypedException` here (Accuraries' module imports it for the
overload-error path).

### Deliverables

1. **Module skeleton + exceptions** (PR #1, lands fast)
   - `IllTypedException(Exception)` carrying optional `Pos`.
   - `def typecheck_program(p: Program) -> ClassTable:` signature only.
   - `def typeof_exp(exp, env, ct) -> Type:` signature only.
   - `def typecheck_stmt(stmt, env, return_type, ct) -> Env:` signature only.

2. **`typeof_exp`** — full expression typing
   - `IntLiteralExp` → `IntType`
   - `StringLiteralExp` → `ClassType("String")`
   - `TrueExp`/`FalseExp` → `BooleanType`
   - `VarExp` → env lookup or `IllTypedException`
   - `ThisExp` → `ClassType(current_class)` (env carries current class)
   - `BinOpExp` — pattern-match `(left_type, op, right_type)`:
     - `(Int, Plus|Minus|Multiply|Divide, Int) → Int`
     - `(Int, LessThan, Int) → Boolean`
     - `(t, Equals, t) → Boolean` for any equal `t`
   - `PrintlnExp` — argument must be `Int`/`Boolean`/`String` (decide
     and document); result `Void` (or whatever the spec says).
   - `CallExp` — typecheck receiver, recursively type each arg,
     delegate to `ct.lookup_method(class_name, method_name, arg_types)`,
     return its return type.
   - `NewExp` — delegate to `ct.lookup_method(class_name, "init",
     arg_types)` for the constructor; return `ClassType(class_name)`.

3. **`typecheck_stmt`** — full statement typing
   - `VarDecStmt` — refuse redeclaration in the same scope; record type;
     mark variable as declared but NOT initialized.
   - `AssignStmt` — variable must be declared, RHS type must be subtype
     of declared type, mark variable as initialized.
   - `IfStmt`/`WhileStmt` — condition must be `Boolean`; recurse into
     bodies in fresh nested scopes.
   - `ReturnStmt` — expr type (or `Void` if none) must be subtype of
     `return_type`.
   - `BreakStmt` — only allowed inside a `while`. Track loop depth in env.
   - `ExpStmt` — typecheck the expression, discard result.

4. **Variable-initialized-before-use check**
   - Env tracks two sets: declared, initialized.
   - `typeof_exp(VarExp(v))` requires `v ∈ initialized`.
   - For `IfStmt`: a variable becomes initialized at the join only if
     both branches initialized it.
   - For `WhileStmt`: assignments inside the loop body do NOT count as
     definitely initialized after the loop (the loop may not execute).

5. **Definite-return analysis**
   - Separate function `returns_definitely(stmt) -> bool`.
   - True for `ReturnStmt`.
   - For `IfStmt`: true iff both branches do.
   - For sequences: true iff any statement does.
   - For methods with non-`Void` return type: assert `returns_definitely`
     over the body, else `IllTypedException`.

6. **`typecheck_program` orchestration**
   - Build `ClassTable` (Accuraries).
   - Typecheck each class body: each method (against its declared return
     type) and the constructor (with `super` arg types from `ct.super_arg_types`).
   - Typecheck the program-entry statements with no `this`.
   - Return the `ClassTable` (codegen needs it).

### Done when

- The Animal/Cat/Dog example in `ClassC.docx` typechecks clean.
- Negative-test fixtures (`Cat = new Dog`, missing return, uninitialized
  use, wrong-arg-type call, etc.) all raise `IllTypedException` with the
  position of the offending node.
- ≥95% line coverage on `src/typechecker.py`.

---

## Stealy — Code Generator (ClassC → C)

**Starts as soon as Accuraries' stub lands.** No dependency on Revamp
— codegen runs on `(Program, ClassTable)`. The assumption is that the
program has already been typechecked; codegen is allowed to be sloppy
about ill-typed input.

### Deliverables

1. **Module skeleton** (PR #1)
   - `src/codegen.py`
   - `class CodegenError(Exception): ...`
   - `def generate_c(p: Program, ct: ClassTable) -> str:` signature only.

2. **Per-class C struct emission**
   - Each class becomes a `struct ClassName { ... }` containing:
     - A `struct ClassName_vtable* vtable` pointer as the first member.
     - All inherited fields (in inheritance order), then own fields.
   - Field types map: `Int → int`, `Boolean → int`, `Void → void`,
     `ClassType("X") → struct X*`, `ClassType("String") → const char*`.

3. **Vtable emission**
   - For each class, emit `struct ClassName_vtable { void (*fn)(...); ... }`.
   - For each class, emit a `static const ClassName_vtable
     ClassName_vt = { &ClassName_method, ... };` initializer.
   - Ordering matches `ct.vtable_layout(class_name)`.

4. **Method emission**
   - Each `MethodDef` becomes a free C function `ClassName_methodName_<sigHash>`
     with `struct ClassName* this` as the first parameter (mangled name
     to disambiguate overloads).
   - Body emits each statement / expression recursively.

5. **Constructor (`init`) emission**
   - Each class gets a `ClassName_new(...) -> struct ClassName*` that
     `malloc`s, sets the vtable pointer, recursively calls
     `super`'s `_new`-equivalent, then runs the constructor body.

6. **Statement / expression emission**
   - Straightforward C translation.
   - `(call recv m args...)` → look up vtable slot via
     `ct.vtable_layout(static_type_of_recv)`, emit
     `recv->vtable->m(recv, args...)`.
   - `(new C args...)` → `C_new(args...)`.
   - `(println e)` → `printf` with the right format string for `e`'s type
     (Stealy can carry a tiny `typeof_exp`-lite or rely on `ct` to know
     enough; document the choice).

7. **`main()` generation**
   - Wraps the program-entry statements in `int main(void) { ... return 0; }`.
   - Includes `#include <stdio.h>` and `#include <stdlib.h>`.

8. **Tests**
   - `tests/fixtures/*.classc` source + `*.expected` stdout pairs.
   - Test harness: write generated C to a temp file, invoke `cc`,
     run the binary, compare stdout. Skip the suite gracefully if `cc`
     isn't on `PATH` (CI concern).

### Out of scope for v1

- Garbage collection (the spec explicitly says no memory reclamation).
- Optimizations (also out per spec).
- Anything beyond `Object`, `String`, user classes, `Int`, `Boolean`,
  `Void`.

### Done when

- The Animal/Cat/Dog example produces a C file that compiles with
  `cc -Wall -Wextra` and prints `0\n1\n2\n` (or whatever the corrected
  example output is).
- A second nontrivial test case (multi-method inheritance with overrides
  and a `while`/`if`) round-trips correctly.
- ≥90% line coverage on `src/codegen.py`.

---

## Suggested PR cadence

```
day 0          Yuzu: parser prep PR opens
day 2-3        Yuzu: parser prep merges                ◀── unblocks the rest

day 3          Accuraries: ClassTable stub PR (signatures only)
               Revamp:     typechecker.py stub PR (signatures + IllTyped)
               Stealy:     codegen.py stub PR (signatures + CodegenError)
day 4          All three stubs merge.

day 4-7        All three implement in parallel.
day 7-12       Continue; integration tests start landing on day 10.
day 12-15      Bug fixes, end-to-end tests with the Animal example.
day 15-17      Buffer / write-up / final coverage push.
```

## Integration touchpoints (where the seams come together)

- **Yuzu → Everyone**: AST shape is frozen after Yuzu's PR. Any later
  AST change requires re-coordination.
- **Accuraries → Revamp**: `ClassTable.lookup_method` must return enough
  info for Revamp to type the call (`return_type`, `param_types`).
  Agreed shape: `MethodSig(name, param_types, return_type, owner_class)`.
- **Accuraries → Stealy**: `field_layout` and `vtable_layout` must be
  *stable orderings* — Stealy emits structs in that order, so changing
  the order silently breaks every fixture.
- **Revamp → Stealy**: there is **no direct dependency** in v1. If we
  decide later to attach types to AST nodes (a "typed AST"), that
  becomes Revamp's output and Stealy's input — but defer that until v1
  works end-to-end.

## Conventions

- All modules use absolute imports (`from class_table import ClassTable`,
  not relative). Matches existing `parser.py` style.
- All errors carry a `Pos` (made available by Yuzu's PR). `Pos`-less
  errors are acceptable only for "the whole program" failures (e.g.,
  duplicate class names where you might pick either definition).
- Tests live under `tests/test_<module>.py`, mirroring the source layout.
- One assertion per concept per test. Negative tests use
  `pytest.raises(SpecificException)` rather than bare `Exception`.
