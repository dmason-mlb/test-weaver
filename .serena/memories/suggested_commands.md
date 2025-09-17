# Suggested Commands for test-weaver

## Development Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Copy environment configuration
cp .env.example .env
# Then update .env with required API keys
```

## Docker Services Management
```bash
# Start all services (Qdrant, Neo4j, Redis)
docker-compose up -d

# Stop all services
docker-compose down

# View service logs
docker-compose logs -f [service_name]

# Check service status
docker-compose ps
```

## Testing Commands
```bash
# Run specific test (follow numbered order for TDD)
pytest tests/test_1_vector_store_initialization.py -v

# Run all tests with coverage (80% minimum required)
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80

# Run only failing tests
pytest tests/ --lf

# Run tests by marker
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only

# Run tests with short output
pytest tests/ -v --tb=short

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
# Report will be in htmlcov/index.html
```

## Code Quality Commands
```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint code with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/

# Run all code quality checks
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
```

## CLI Entry Point
```bash
# Run the main test generation pipeline
test-gen

# Alternative: run directly with Python
python -m src.pipeline
```

## Development Workflow
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start Docker services
docker-compose up -d

# 3. Run the next failing test
pytest tests/test_N_*.py -v  # where N is the next number

# 4. Implement code to make test pass

# 5. Run code quality checks
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/

# 6. Run all tests to ensure nothing broke
pytest tests/ -v

# 7. Check test coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Git Commands
```bash
# Check status
git status

# View recent commits
git log --oneline -10

# Create a new branch
git checkout -b feature/branch-name

# Stage changes
git add .

# Commit changes
git commit -m "Description of changes"
```

## Dependency Management
```bash
# Update requirements.txt from requirements.in
pip-compile requirements.in

# Install new package and add to requirements.in
pip install package-name
# Then manually add to requirements.in and run pip-compile

# Upgrade all packages
pip-compile --upgrade requirements.in
```

## System Utilities (macOS/Darwin)
```bash
# List files with details
ls -la

# Find files
find . -name "*.py" -type f

# Search in files (use ripgrep if available)
grep -r "pattern" src/
# or better:
rg "pattern" src/

# Check Python path
which python3

# Check environment variables
env | grep PYTHON
```