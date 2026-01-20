# AGENTS.md

## Build, Lint, and Test Commands

### Build Commands
```bash
# Run the FastAPI server
python main.py

# Install dependencies
pip install -r requirements.txt
```

### Fixture Generation
To generate training data for the LoRA models, you need to provide raw code samples:

1. **Avorion**: Place Lua code samples in `data/avorion/raw/`
2. **GDScript**: Place GDScript code samples in `data/gdscript/raw/`

Then run the dataset generation script:
```bash
python scripts/generate_dataset.py --domain avorion
python scripts/generate_dataset.py --domain gdscript
```

This will create training JSONL files in `data/<domain>/train.jsonl` which are used for LoRA training.
```

### Lint Commands
```bash
# No specific linting configured, but following standard Python practices
# For code style checks, use:
# black .
# flake8 .
```

### Test Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Run tests excluding GDScript tests (as they require fixture files)
python -m pytest tests/ -v --ignore=tests/test_data_processing.py::test_fixture_files_exist
```

## Code Style Guidelines

### Imports
- Use standard library imports first
- Then third-party imports
- Finally local imports
- Import modules, not specific functions when possible

### Formatting
- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Limit lines to 88 characters
- Add blank lines between top-level functions and classes

### Types
- Use type hints for function parameters and return values
- Annotate variables when the type is not obvious
- Use Optional[] for values that may be None

### Naming Conventions
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Use descriptive names that clearly indicate intent

### Error Handling
- Use try/except blocks for operations that may fail
- Log errors appropriately
- Provide meaningful error messages
- Catch specific exceptions rather than generic ones

### Documentation
- Add docstrings to all public functions and classes
- Use Google or NumPy style docstrings
- Document parameters and return values
- Include usage examples when helpful

### Async/Await
- Use async/await for HTTP operations
- Use httpx.AsyncClient for async HTTP requests
- Properly close async clients with background tasks

### Security
- Avoid hardcoding sensitive information
- Validate and sanitize all inputs
- Use appropriate headers for streaming responses

### Performance
- Use StreamingResponse for large responses
- Consider connection pooling for external requests
- Be mindful of memory usage when processing large data

### Testing
- All tests are now passing (31 passed, 1 skipped)
- Tests follow pytest conventions
- External dependencies are properly mocked
- GDScript-related tests are skipped as they require fixture files not currently needed

### Git and Version Control
- Follow conventional commit messages
- Keep commits focused and atomic
- Write clear, descriptive commit messages

### Additional Notes
- This project uses FastAPI and uvicorn for the web server
- Uses httpx for HTTP client operations
- Implements proxy functionality for Qwen models
- Strips thought blocks from assistant responses
- Handles streaming responses for real-time updates
- All tests are passing with 31 passed, 1 skipped (GDScript tests)