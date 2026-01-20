# Real Anthropic Response Fixtures

This project supports using real Anthropic API responses for testing instead of mocked responses. This provides more realistic testing conditions and better coverage of actual API behavior.

## Workflows

There are two main workflows for using real responses:

### Workflow 1: Testing Pipeline Changes
When you've made changes to the training pipeline and want to test with real API responses:
1. Set your Anthropic API key in environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
2. Run tests normally - they will automatically use real responses if available

### Workflow 2: Generating New Fixtures
When you've updated the prompts in the pipeline and need new fixtures:
1. Set your Anthropic API key in environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
2. Generate new fixtures using the capture script:
   ```bash
   python scripts/capture_anthropic_responses.py
   ```

## Setup

To use real Anthropic responses in tests, you need to:

1. Set your Anthropic API key in environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

2. Generate real responses using the capture script:
   ```bash
   python scripts/capture_anthropic_responses.py
   ```

## Directory Structure

Real responses are stored in:
```
tests/fixtures/anthropic_responses/
```

The capture script generates the following files:
- `avorion_batch_responses.json` - Avorion domain responses (using exact same prompts as real pipeline)
- `gdscript_batch_responses.json` - GDScript domain responses (using exact same prompts as real pipeline)
- `error_responses.json` - Error response examples

## Usage in Tests

The test framework automatically detects and uses real responses when available. The `anthropic_responses` fixture in `conftest.py` loads these responses, and the mock helpers in `mock_helpers.py` can utilize them when creating mock clients.

## Backwards Compatibility

Tests will continue to work with mocked responses when real responses are not available, ensuring full backwards compatibility with existing test suites.

## Important Notes

- The capture script uses the EXACT SAME prompts that are used in the real pipeline
- This ensures that test responses match what will be produced in production
- Only generate new fixtures when you've updated the prompts in the training pipeline