# Contributing

Thank you for contributing to the LoRA Training Pipeline!

## Development Setup

```bash
git clone https://github.com/yourusername/lora-training.git
cd lora-training
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Before Committing

Always run quality checks:

```bash
make check          # Run all checks
make check-fix      # Auto-fix issues first
```

### Quality Standards

| Check | Requirement |
|-------|-------------|
| Linting | Zero ruff errors |
| Tests | All passing |
| Coverage | 80% minimum |
| Complexity | McCabe <= 15 per function |

## Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run `make check`
4. Commit with descriptive message
5. Push and create a pull request

## Code Style

- Use `ruff` for formatting (auto-fixed via `make check-fix`)
- Keep functions small and focused
- Add tests for new functionality
- Document complex logic with comments

## Testing

```bash
make test                               # Run tests with coverage
python -m pytest tests/test_config.py   # Run specific test file
```

## Common Tasks

### Adding a New Domain

1. Create config file: `config/<domain>.yaml`
2. Add prompt template to `scripts/prompts.py`
3. Create data directory: `data/<domain>/raw/`
4. Update tests if needed

### Modifying Training Parameters

1. Edit `config/base.yaml` for shared defaults
2. Override in domain configs as needed
3. Document significant changes

## Getting Help

- Check `CLAUDE.md` for AI assistant context
- Review `ideas/qwen3-80b-unified-adapter-plan.md` for architecture
- Open an issue for bugs or questions
