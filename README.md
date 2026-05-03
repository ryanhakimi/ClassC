# ClassC
Comp 430 ClassC Project

## Pipeline status

- ✅ Lexer
- ✅ Parser
- ⏳ Type checker
- ⏳ Code generator

## Supported language features

Lexer and parser accept the full grammar from the language proposal:

- **Types**: `Int`, `Boolean`, `Void`, and class types (`Object`, `String`, user-defined)
- **Expressions**: integer & string literals, variables, `this`, `true`/`false`, `(println e)`, arithmetic and relational ops `+ - * / < ==`, `(call recv method args...)`, `(new ClassName args...)`
- **Statements**: `(vardec T x)`, `(= x e)`, `(while cond stmts...)`, `break`, `(if cond then [else])`, `(return [e])`
- **Definitions**: `(method name (params) returnType body...)`, `(init (params) [(super args...)] body...)`, `(class Name [Parent] (fields) constructor methods...)`
- **Program**: zero or more class definitions followed by one or more entry-point statements

Comments are not supported (per spec). Type checking and code generation are pending.

## Project Structure
```
ClassC/
├── README.md
├── requirements.txt
├── src/
│   ├── tokenizer.py
│   └── parser.py
└── tests/
    ├── test_tokenizer.py
    └── test_parser.py
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

## Running Tests

```bash
pytest tests/
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
