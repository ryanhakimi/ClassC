# ClassC

COMP 430 ClassC compiler is a small object-oriented language with classes,
inheritance, and method overriding, compiled to C.

Created by Ryan, Andrew, Courtney, and Ethan

## Project Structure

```text
ClassC/
├── src/
│   ├── tokenizer.py
│   ├── parser.py
│   ├── typechecker.py
│   ├── codegen.py
│   └── compiler.py
└── tests/
    ├── test_tokenizer.py
    ├── test_parser.py
    ├── test_typechecker.py
    └── test_codegen.py
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
pytest tests/                          # all tests
pytest tests/test_tokenizer.py         # one suite
pytest -v tests/                       # verbose
pytest --cov=src --cov-report=html tests/   # coverage → htmlcov/index.html
```

## Compiler Usage

`src/compiler.py` exposes four commands:

```bash
python src/compiler.py tokens     program.classc          # print tokens
python src/compiler.py parse      program.classc          # print AST
python src/compiler.py typecheck  program.classc          # type-check only
python src/compiler.py compile    program.classc out.c    # emit C
```

## End-to-End Example

Save as `examples/animals.classc`:

```lisp
(class Animal
  ()
  (init ())
  (method speak () Void
    (return (println 0))))

(class Cat Animal
  ()
  (init ()
    (super))
  (method speak () Void
    (return (println 1))))

(vardec Animal pet)
(= pet (new Cat))
(call pet speak)
```

Compile and run:

```bash
python src/compiler.py compile examples/animals.classc out.c
gcc out.c -o out      # use `gcc out.c -o out.exe` on Windows/MinGW
./out                 # prints: 2
```

To reject ill-typed input, point `typecheck` at a bad program:

```bash
echo '(vardec Int x) (println x)' > bad.classc
python src/compiler.py typecheck bad.classc      # fails: x used before init
```
