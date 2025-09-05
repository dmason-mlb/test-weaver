# Task Completion Checklist

When completing any development task in this project, follow these steps:

## 1. Code Quality Checks (REQUIRED)
Run these commands after making any code changes:

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint code with flake8
flake8 src/ tests/

# Type check with mypy (optional but recommended)
mypy src/
```

## 2. Run Tests
```bash
# Run all tests to ensure nothing broke
pytest tests/ -v

# Check test coverage (must be >= 80%)
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80

# Run specific test if working on particular feature
pytest tests/test_N_*.py -v  # where N is the test number
```

## 3. Verify Docker Services (if needed)
```bash
# Check if services are running (when working with integrations)
docker-compose ps

# Restart services if needed
docker-compose restart [service_name]
```

## 4. Pre-commit Checklist
Before committing changes:
- [ ] All tests pass
- [ ] Code coverage >= 80%
- [ ] Code is formatted with Black
- [ ] Imports are sorted with isort
- [ ] No flake8 errors
- [ ] New features have corresponding tests
- [ ] Docstrings added for new classes/methods
- [ ] No hardcoded credentials or secrets
- [ ] Environment variables documented in .env.example if added

## 5. Documentation Updates
If you've added new features:
- [ ] Update relevant docstrings
- [ ] Add usage examples if applicable
- [ ] Update PROJECT_LAYOUT.md if new files added

## 6. TDD Workflow Reminder
This project follows Test-Driven Development:
1. Tests are numbered and should be run in order
2. Run the failing test first
3. Implement ONLY enough code to make the test pass
4. Don't implement features before their tests exist
5. Don't modify test files

## 7. Final Verification
```bash
# Run the complete quality check suite
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && pytest tests/ -v --cov=src --cov-fail-under=80
```

## 8. Error Resolution
If any step fails:
- Fix the specific issues reported
- Re-run the failed step
- Continue with remaining steps only after resolution

## Notes
- The project uses strict TDD methodology - follow test order
- Coverage requirement is 80% minimum
- All code must pass Black formatting
- Docker services must be running for integration tests
- Never commit without running the quality checks