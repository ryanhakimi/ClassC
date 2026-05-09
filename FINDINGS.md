# ClassC — Review Findings (no fixes applied)

**Reviewer:** Ethan (SwegCet)
**Date:** 2026-05-08
**Scope:** Full repo audit at `main` (HEAD = `fc24571`).
**Outcome:** All 122 tests pass; the Animals example compiles cleanly with `gcc`
and prints `1\n2\n` as expected. The bugs below do **not** break the happy path
but they do violate the `WORK_SPLIT.md` contract and/or the language spec's
stated semantics.

This document is **flagging only**. Per Ethan's instructions, no code is
modified by this review. Each finding is assigned to **Stealy** (codegen)
or **Revamp** (typechecker / non-codegen) for follow-up.

---

## Alignment with WORK_SPLIT.md

`WORK_SPLIT.md` is no longer in the repo (commit `fc84d1f` removed it after
the Phase 3+4 plan landed in `07073e6`). The canonical copy still lives at
`/Users/efan/CSUN/Spring_2026/COMP_430/WORK_SPLIT.md`. The review uses that
copy as the contract.

| Role           | Owned files (per WORK_SPLIT)                  | Status        |
|----------------|-----------------------------------------------|---------------|
| **Yuzu**       | `parser.py`, `tokenizer.py`, parser/tok tests | **Partial**   |
| **Accuraries** | `class_table.py`, `test_class_table.py`       | **Missing**   |
| **Revamp**     | `typechecker.py`, `test_typechecker.py`       | Mostly landed |
| **Stealy**     | `codegen.py`, `test_codegen.py`, fixtures     | Mostly landed |

Two structural deviations:

1. **`src/class_table.py` was never created.** Accuraries' deliverables
   (subtype relation, method lookup, vtable layout, field layout) are
   inlined into `typechecker.py` and partially **duplicated** in
   `codegen.py` (`_is_subtype`, `_more_specific`, `_resolve_call_method`,
   `_all_methods` exist in both files with subtly different shapes).
2. **Yuzu's "parser prep" was only ~50% delivered** — see Bugs #3a–#3d.

---

## Critical bugs

### Bug #1 — Typechecker accepts `(println obj)` for arbitrary class instances → **REVAMP**

**Where:** `src/typechecker.py:332-334` (`_type_of_expression` / `PrintlnExp`).
**WORK_SPLIT contract:** "PrintlnExp — argument must be `Int`/`Boolean`/`String`."
**Actual behavior:** any expression is accepted. Codegen falls through to
`ClassC_print_object` (codegen.py:321) and prints the pointer address.

Repro:
```lisp
(class A () (init ()))
(vardec A a)
(= a (new A))
(println a)
```
Typecheck succeeds. Compiled binary prints e.g. `0x102de5bc0`.

**Fix sketch:** in `PrintlnExp` branch, after typing the inner expression,
reject anything that is not `IntType`, `BooleanType`, or `ClassType("String")`.

---

### Bug #2 — Tokenizer regression: `//` line comments removed → **REVAMP**

**Where:** `src/tokenizer.py:119-121` (`skip_whitespace`).
**Git evidence:** commits `637453b "Add lookahead helper and support for //
line comments"` and `3618405 "Updated line comments"` added the feature, but
commit `cdab71d "Update tokenizer.py"` deleted both `peek_next` and
`skip_line_comment`, and the feature has not returned. (Same commit also
deleted `read_string`/`STRING_LITERAL`; those were re-added in `07073e6`.
Comments were not.)

Repro:
```
// hello
(println 42)
```
Tokenizer emits `DIVIDE DIVIDE IDENTIFIER('hello') ...` instead of skipping.
Any `.classc` source with comments fails to parse.

**Fix sketch:** in `skip_whitespace` (or a new `skip_whitespace_and_comments`
called from `tokenize`'s loop), if `self.peek()=="/"` and
`self.source[self.pos+1]=="/"`, advance until newline. Add a regression test
to `test_tokenizer.py`.

---

### Bug #3 — Yuzu's parser-prep deliverables not delivered → **REVAMP**

`WORK_SPLIT.md` "Yuzu — Parser prep & shared scaffolding" listed 5
deliverables. Status:

| Deliverable | Spec'd | Actual |
|-------------|--------|--------|
| 3a. Op sum type (`PlusOp`, `MinusOp`, …) | required | **Missing.** `BinOpExp.op` is still `str` (`parser.py:65`). Tests assert `result.op == "+"`. |
| 3b. `Pos` dataclass on every AST node (`pos: Optional[Pos] = field(default=None, compare=False)`) | required | **Missing.** No `Pos` class anywhere; AST nodes don't carry positions; `TypecheckError` has no position info. |
| 3c. Replace `object` annotations with `Optional`/`Union` types (`Expression`, `Statement` aliases) | required | **Missing.** `parser.py` still uses bare `object` on `parent`, `super_args`, `else_stmt`, `expression`, etc. |
| 3d. String literal support (`STRING_LITERAL` token, `read_string`, `StringLiteralExp`, escape handling) | required | **Done.** Present in tokenizer/parser. |
| 3e. `WORK_SPLIT.md` itself | required | Landed then removed (`fc84d1f`). |

3a–3c are spec deviations rather than runtime bugs (the existing code
works). They become bugs only if you care about: (i) static analysis
quality (`pyright`/`mypy` will not flag misuse of `BinOpExp.op`), (ii)
error messages with file positions (mandated by WORK_SPLIT — see Bug #6).

---

### Bug #4 — Errors carry no `Pos` info → **REVAMP**

**Where:** `src/typechecker.py:71-72` (`TypecheckError(Exception): pass`),
`src/parser.py:155` (`ParseError` has token-based position but `TypecheckError`
does not).
**WORK_SPLIT contract:** "All errors carry a `Pos`. `Pos`-less errors are
acceptable only for 'the whole program' failures."

Most TypecheckError messages currently say *what* but not *where*. Without
Bug #3b (no `Pos` on AST nodes), even adding position info to errors
requires the AST work first.

---

### Bug #5 — Exception class name mismatch → **REVAMP**

**Where:** `src/typechecker.py:71` defines `TypecheckError`.
**WORK_SPLIT contract:** "`IllTypedException(Exception) carrying optional
Pos`."

Cosmetic, but the rest of the spec text refers to `IllTypedException`. Tests
import the actual name (`TypecheckError`), so a rename touches the test
file too.

---

### Bug #6 — `compiler.py` shows raw Python tracebacks on user errors → **SHARED (assign Stealy)**

**Where:** `src/compiler.py:32-36, 38-44`.
**Repro:** `python src/compiler.py typecheck program-with-typo.classc` prints
the full Python traceback ending in `typechecker.TypecheckError: …`.

For end-user demos and graders, this is jarring. Catch
`TypecheckError`/`ParseError`/`TokenizerError`/`CodegenError`, print the
message, exit `1`.

Assigning to **Stealy** because compiler.py is downstream "user-facing
plumbing" closer to codegen output than to typechecker semantics.

---

## Codegen bugs

### Bug #7 — `self_this` cast variable emitted even when unused → **STEALY**

**Where:** `src/codegen.py:222-223` (in `_emit_methods`).
**Effect:** every override generates `Cat* self_this = (Cat*) self;` whose
binding is never read inside the method body. Under `gcc -Wall -Wextra`:
```
warning: unused variable 'self_this' [-Wunused-variable]
warning: unused parameter 'self' [-Wunused-parameter]
```
WORK_SPLIT "Done when": "compiles with `cc -Wall -Wextra`" (no warning
constraint stated, but a clean build is the obvious target).

**Fix sketch:** only emit `self_this` if the body actually references
`this` or any field of the current class. Or `(void) self_this;` to
silence the warning. Or rename `self`→`self_this` directly when
`slot_owner != class_name` and skip the cast variable.

---

### Bug #8 — Constructor double-writes `super.vtable` → **STEALY**

**Where:** `src/codegen.py:175-184` (`_emit_constructors`).
**Generated for `Animal_init`:**
```c
self->super.vtable = &Object_vtable_instance;                    // line 1
((Animal*) self)->super.vtable = (Object_vtable*) &Animal_vtable_instance; // line 2 — overwrites line 1
```
Line 1 is unconditionally clobbered by line 2. Wasted store; harmless but
signals a logic redundancy.

**Fix sketch:** drop the `self->super.vtable = &Object_vtable_instance;`
emission in the parent==Object branch — the `{class_name}_vtable_instance`
write that always follows handles it.

---

### Bug #9 — `new_X` emitted for every class even when never instantiated → **STEALY**

**Where:** `src/codegen.py:191-205`.
**Effect:** `new_Animal` is emitted in the Animals example even though
`(new Animal)` never occurs. `gcc -Wall` warns
`unused function 'new_Animal'`.

**Fix sketch:** track which class names appear in `NewExp` nodes (anywhere
in classes' bodies + program statements), only emit `new_X` for those.
Or mark them `__attribute__((unused))`. Or just emit them all without
`static` so the warning never triggers (but then linker may pull them in).

---

### Bug #10 — Print helpers emitted unconditionally → **STEALY**

**Where:** `src/codegen.py:69-91` (`_emit_prelude`).
**Effect:** all four `ClassC_print_*` helpers and `Object_vtable_instance`
are emitted in the prelude. If a program only uses `(println int)`, the
other three helpers are dead and `-Wall` warns.

**Fix sketch:** scan the AST for `PrintlnExp` types up-front (or track
during emission) and only emit the helpers actually used. Or mark the
helpers `__attribute__((unused))`.

---

### Bug #11 — `_resolve_call_method` defensively re-implements method
overload resolution → **STEALY** (or punt to shared `class_table.py`)

**Where:** `src/codegen.py:416-439`. Mirrors `typechecker._resolve_method`.
**Effect:** code duplication. If the typechecker accepts a call, this
re-resolves it. Subtle drift between the two could cause "compiles but
behaves differently" outcomes. Per WORK_SPLIT this logic belongs in
`class_table.py` and both consumers should call into it.

**Fix sketch (large):** extract a `ClassTable` module per WORK_SPLIT and
have both `typechecker.py` and `codegen.py` consume it. Owners would be
Accuraries originally — since Accuraries' deliverable was skipped, this
becomes a Stealy/Revamp shared cleanup. Defaulting to **Stealy** since
the codegen side is where the duplicated code currently lives.

---

## Test bugs

### Bug #12 — `test_parser.py` defines 21 tests twice → **REVAMP**

**Where:** `tests/test_parser.py`. 120 `def test_` lines, but
`awk '/^def test_/' | sort | uniq -d` lists 21 duplicates:
```
test_parse_boolean_expression_in_condition
test_parse_call_expression_as_arg
test_parse_constructor_with_multiple_params_and_super
test_parse_deeply_nested_expression
test_parse_error_attributes
test_parse_error_expect_end_of_input
test_parse_error_expect_wrong_token
test_parse_error_missing_closing_paren
test_parse_error_no_token
test_parse_if_else_in_method
test_parse_method_with_while_loop
test_parse_multiple_classes_inheritance_chain
test_parse_new_expression_complex_args
test_parse_new_in_assignment
test_parse_println_in_expression
test_parse_while_with_break
test_parse_while_with_if_and_break
test_parser_advance
test_parser_at_end
test_parser_at_end_false
test_parser_peek_returns_none_at_end
```
Python keeps only the last definition; the earlier 21 functions are dead
code that never runs. **Pytest reports 122 passing tests but 21 of those
"function bodies" are silently dropped.**

**Fix sketch:** delete the earlier copy of each (or merge any divergent
assertions into the surviving copy).

---

### Bug #13 — Test coverage gaps relative to WORK_SPLIT done-when criteria → **SPLIT**

**`test_typechecker.py` — only 9 tests.** Missing per WORK_SPLIT
"negative-test fixtures":
- Ambiguous overload resolution → **REVAMP**
- Cyclic inheritance, duplicate class, duplicate field, duplicate parameter → **REVAMP**
- While-loop assignment does not propagate to post-loop scope → **REVAMP** (works in
  practice — see manual test in `/tmp/classc_review/while_init.classc` — but
  no automated test pins the behavior)
- If-without-else does not initialize at join → **REVAMP**
- Override return-type mismatch (works manually; not asserted) → **REVAMP**
- Wrong-arg-type call (subtype violation) → **REVAMP**
- `Cat = new Dog` (sibling assignment failure) → **REVAMP**
- `(new String)` rejection → **REVAMP**
- Calling method on built-in `String` → **REVAMP**

**`test_codegen.py` — only 3 tests, all string-grep on the emitted C.**
Missing per WORK_SPLIT "Done when":
- End-to-end fixture harness (`tests/fixtures/*.classc` + expected stdout,
  invoke `cc`, run, diff) → **STEALY**
- Multi-method inheritance with overrides + while/if round-trip → **STEALY**
- Field access through inheritance → **STEALY**
- Boolean and string `println` → **STEALY**
- Constructor with `super` arg passing → **STEALY**

`tests/fixtures/` directory does not exist (`ls tests` confirms).

---

## Smaller / questionable issues (not flagged for immediate fix)

### Issue #14 — Typechecker `VarExp` branch has dead-code redundancy

**Where:** `src/typechecker.py:329-331`:
```python
if is_field and allow_uninitialized_fields:
    return var_type
return var_type
```
Both branches return the same value, so the `allow_uninitialized_fields`
flag has no effect inside `_type_of_expression`. Either the gating logic
was lost in a refactor or the flag is now dead. Suggest **REVAMP** review.

---

### Issue #15 — Order-of-checks: "method on String" obscured by "uninitialized" check

`(call s length)` where `s: String` is uninitialized fails with
`Variable 's' may be used before it is initialized` instead of the more
specific `Built-in String does not support methods` (typechecker.py:371).
The String-rejection branch is reachable only after `s` is initialized
first. Cosmetic. **REVAMP** can revisit.

---

### Issue #16 — Duplicate subtype/overload logic between `typechecker.py` and `codegen.py`

`_is_subtype`, `_more_specific`/`_is_more_specific`, `_all_methods`,
`_all_fields` all exist in both files with subtly different shapes
(typechecker uses dicts; codegen uses lists). Not currently a bug because
both implementations agree on every input the test suite exercises, but
fragile. Tied to the missing `class_table.py` (Bug #11).

---

### Issue #17 — No initialization-of-fields enforcement

A class can declare `(vardec Int x)` and never assign to `x` in its
constructor. Reading `x` later returns whatever `malloc` left in memory.
WORK_SPLIT does not explicitly require this check, and many ClassC-style
languages don't enforce it. Flagging here so it's a deliberate decision,
not an oversight.

---

## Summary — work split

### To Stealy (codegen.py + tests/fixtures + compiler.py glue)

- **Bug #6** — make `compiler.py` print clean errors instead of stacktraces.
- **Bug #7** — drop unused `self_this` (or silence the warning).
- **Bug #8** — drop redundant `super.vtable = Object_vtable_instance`.
- **Bug #9** — only emit `new_X` for classes that get instantiated.
- **Bug #10** — only emit print helpers actually used.
- **Bug #11** — extract overload resolution into a shared module (or, at
  minimum, consume the typechecker's resolution result).
- **Bug #13 (codegen half)** — build a real fixture-based codegen test
  harness; add inheritance/override, field access, boolean/string println,
  super-arg constructor cases. Create `tests/fixtures/`.

### To Revamp (typechecker.py + tokenizer.py + parser.py + tests)

- **Bug #1** — reject non-Int/Boolean/String args to `println`.
- **Bug #2** — reinstate `//` line comments in the tokenizer.
- **Bug #3a-c** — implement Op sum type, `Pos` dataclass, and Optional/Union
  annotations on AST nodes (Yuzu's missing parser prep).
- **Bug #4** — propagate `Pos` into `TypecheckError` messages.
- **Bug #5** — rename `TypecheckError` → `IllTypedException` (low priority,
  cosmetic, but per spec).
- **Bug #12** — delete the 21 duplicated tests in `test_parser.py`.
- **Bug #13 (typechecker half)** — add the 9 missing negative-test
  fixtures listed above.
- **Issue #14** — clean up the dead `allow_uninitialized_fields` branch.

### Pure judgement calls (please decide before assigning)

- **Issue #16** / re-introducing `class_table.py`. Doing so cleanly is a
  multi-file refactor — both Stealy and Revamp would touch it. If we punt
  this, document the duplication as a known-debt item.
- **Issue #17** — should we enforce field initialization in constructors,
  or leave the current "fields get whatever `malloc` produced" semantic?

---

## Test-suite snapshot at review time

```
$ pytest tests/ -q --tb=no
122 passed in 0.17s
```

End-to-end:
```
$ python src/compiler.py compile examples/animals.classc out.c
$ gcc -Wall -Wextra out.c -o out
out.c:130: warning: unused parameter 'self'   ← Bug #7
out.c:136: warning: unused variable 'self_this' ← Bug #7
out.c:142: warning: unused variable 'self_this' ← Bug #7
out.c: warning: unused function 'ClassC_print_bool'    ← Bug #10
out.c: warning: unused function 'ClassC_print_string'  ← Bug #10
out.c: warning: unused function 'ClassC_print_object'  ← Bug #10
out.c: warning: unused function 'new_Animal'           ← Bug #9
$ ./out
1
2
```

The happy path works. Everything in this document is about closing the
gap between "it works on the demo" and "it matches the contract we wrote
ourselves in WORK_SPLIT.md."
