# ClassC
Comp 430 ClassC Project

## Project Structure
```text
ClassC/
├── README.md
├── requirements.txt
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

1. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running All Tests

Run the full test suite:
```bash
pytest tests/
```

## Running Specific Test Suites

Run only tokenizer tests:
```bash
pytest tests/test_tokenizer.py
```

Run only parser tests:
```bash
pytest tests/test_parser.py
```

Run only type checker tests:
```bash
pytest tests/test_typechecker.py
```

Run only code generator tests:
```bash
pytest tests/test_codegen.py
```

Run only the semantic/code generation tests:
```bash
pytest tests/test_typechecker.py tests/test_codegen.py
```

Run tests with verbose output:
```bash
pytest -v tests/
```

## Code Coverage

To generate a coverage report in the terminal:
```bash
pytest --cov=src --cov-report=term tests/
```

To generate an HTML coverage report:
```bash
pytest --cov=src --cov-report=html tests/
```

Then open `htmlcov/index.html` in your browser to view line-by-line coverage details.

## Compiler Commands

The compiler entry point is `src/compiler.py`.

### Print tokens
```bash
python src/compiler.py tokens path/to/program.classc
```

### Parse a program
```bash
python src/compiler.py parse path/to/program.classc
```

### Run the type checker
```bash
python src/compiler.py typecheck path/to/program.classc
```

If the program is valid, the compiler prints:
```text
Typecheck succeeded
```

### Generate C code to the terminal
```bash
python src/compiler.py compile path/to/program.classc
```

### Generate C code into a file
```bash
python src/compiler.py compile path/to/program.classc out.c
```

## Fully Testing the Type Checker Manually

Create a small test file, for example `examples/typecheck_ok.classc`:

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

Then run:
```bash
python src/compiler.py typecheck examples/typecheck_ok.classc
```

You can also test that the type checker rejects bad programs. For example, create `examples/typecheck_bad.classc`:

```lisp
(vardec Int x)
(println x)
```

Then run:
```bash
python src/compiler.py typecheck examples/typecheck_bad.classc
```

This should fail because `x` is used before being initialized.

## Fully Testing the Code Generator Manually

Use a valid source program, for example `examples/animals.classc`:

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

Generate C code:
```bash
python src/compiler.py compile examples/animals.classc out.c
```

Compile the generated C program with GCC:
```bash
gcc out.c -o out
```

Run the executable:
```bash
./out
```

On Windows with MinGW, run:
```bash
gcc out.c -o out.exe
out.exe
```

## End-to-End Validation Commands

### 1. Typecheck the source program
```bash
python src/compiler.py typecheck examples/animals.classc
```

### 2. Generate C output
```bash
python src/compiler.py compile examples/animals.classc out.c
```

### 3. Compile the generated C file
```bash
gcc out.c -o out
```

### 4. Run the executable
```bash
./out
```

## Demo Commands

```bash
pytest tests/test_typechecker.py
pytest tests/test_codegen.py
python src/compiler.py typecheck examples/animals.classc
python src/compiler.py compile examples/animals.classc out.c
gcc out.c -o out
./out
```

