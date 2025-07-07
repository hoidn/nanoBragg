# Contributing to nanoBragg PyTorch

## Development Environment Setup

### Prerequisites
- Python 3.8+
- Git

### Setup Steps
1. Clone the repository and navigate to the project directory
2. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate  # On Linux/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Development Workflow

#### Code Formatting
This project uses `black` and `isort` for code formatting:
```bash
make format  # Auto-format all code
```

#### Running Tests
```bash
make test    # Run the full test suite
```

#### Linting
```bash
make lint    # Check code formatting and style
```

### Project Structure
- `src/nanobrag_torch/`: Main PyTorch implementation
- `tests/`: Test suite including golden data validation
- `golden_suite_generator/`: Tools for generating reference test data from C code
- `torch/`: Architecture documentation and implementation plans

### Testing Strategy
The project uses a three-tier testing approach:
1. **Tier 1**: Translation correctness against C code "golden" outputs
2. **Tier 2**: Gradient correctness via automatic differentiation 
3. **Tier 3**: Scientific validation against physical principles

See `torch/Testing_Strategy.md` for detailed testing methodology.