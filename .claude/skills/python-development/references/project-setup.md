# Project Setup

## New Project Initialization

```bash
# Create project
mkdir my-project && cd my-project
uv init

# Set Python version
echo "3.12" > .python-version
uv python pin 3.12

# Install core dev dependencies
uv add --dev ruff pytest pytest-mock pytest-asyncio
uv add loguru pydantic-settings
```

## pyproject.toml Template

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "loguru",
    "pydantic-settings",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade (modernize syntax)
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "N",    # pep8-naming
]

[tool.ruff.format]
quote-style = "double"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

## Directory Scaffold

```bash
mkdir -p app/services tests frontend/pages
touch app/__init__.py app/models.py app/config.py
touch app/services/__init__.py
touch tests/__init__.py tests/conftest.py
```

## Configuration Boilerplate

### app/config.py

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

### .env (gitignored)

```
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
DEBUG=true
```

## Pre-commit (Optional)

```bash
uv add --dev pre-commit
```

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```
