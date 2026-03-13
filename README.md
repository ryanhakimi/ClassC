# ClassC
Comp 430 ClassC Project

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
