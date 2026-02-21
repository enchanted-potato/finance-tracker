---
name: python-development
description: Python development conventions and coding standards for writing clean, modern Python code. Use when writing or reviewing Python code, setting up new Python projects, writing tests, defining models, or making architectural decisions in Python codebases. Covers code style, project structure, testing, typing, configuration, and tooling preferences.
---

# Python Development

## Language & Tooling

- **Python 3.12+** — use modern syntax throughout:
  - `str | None` not `Optional[str]`
  - `list[int]` not `List[int]`
  - `match` statements where appropriate
  - f-strings everywhere (no `.format()` or `%`)
- **Package manager**: `uv` — use `uv add`, `uv sync`, `uv run`
- **Linting & formatting**: Ruff (linter + formatter). Let Ruff handle import sorting.
- **Logging**: `loguru` — no stdlib `logging` module. Use `from loguru import logger`.
- **Config**: `pydantic-settings` with `BaseSettings` and `.env` files for environment configuration.

## Project Structure

Use the `app/` layout pattern:

```
project-root/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── config.py          # BaseSettings class
│   └── services/
│       └── ...
├── frontend/              # if applicable (Streamlit, etc.)
│   └── pages/
├── tests/
│   ├── conftest.py
│   └── ...
├── pyproject.toml
└── uv.lock
```

For new project setup details, see [references/project-setup.md](references/project-setup.md).

## Code Style

### Naming

- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Prefix private helpers with `_`
- Name booleans as predicates: `is_active`, `has_permission`, `can_edit`

### Functions

- Keep functions short and single-purpose
- Use keyword-only arguments (`*`) for functions with 3+ parameters
- Return early to avoid deep nesting
- Use `pathlib.Path` over `os.path`

```python
def create_account(
    *,
    name: str,
    account_type: AccountType,
    balance: Decimal = Decimal("0"),
) -> Account:
    if not name:
        raise ValueError("Account name is required")
    return Account(name=name, account_type=account_type, balance=balance)
```

### Type Hints

- Type-hint all function signatures (parameters and return types)
- Use `Self` from `typing` for fluent interfaces
- Use `TypeAlias` for complex types
- Avoid `Any` — use `object` or proper generics instead

### Docstrings

Use Sphinx style for public functions and classes: Do not include types.

```python
def calculate_net_worth(accounts: list[Account]) -> Decimal:
    """Calculate total net worth from a list of accounts.

    :param accounts: All accounts to include in the calculation.
    :returns: The sum of all account balances (assets - liabilities).
    """
```

Skip docstrings for private helpers and obvious one-liners.

### Error Handling

- Use built-in exceptions (`ValueError`, `TypeError`, `KeyError`, etc.)
- No custom exception hierarchies unless truly warranted
- Let exceptions propagate — don't catch and re-raise without adding context
- Use loguru for logging errors: `logger.error(...)`, `logger.exception(...)`

### Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

## Testing

Use pytest with heavy fixture usage. See [references/testing-patterns.md](references/testing-patterns.md) for detailed patterns.

### Core Conventions

- File naming: `test_<module>.py`
- Test naming: `test_<behavior_being_tested>`
- Use `conftest.py` at each test directory level for shared fixtures
- Prefer `@pytest.fixture` over setup/teardown methods
- Use `@pytest.mark.parametrize` for testing multiple inputs
- Use `factory` fixtures for creating test data with sensible defaults
- Prefer real objects over mocks; mock only at external boundaries (DB, APIs, filesystem)

```python
@pytest.fixture
def make_account():
    def _make(name: str = "Savings", balance: Decimal = Decimal("1000")) -> Account:
        return Account(name=name, balance=balance)
    return _make

def test_net_worth_sums_balances(make_account):
    accounts = [make_account(balance=Decimal("100")), make_account(balance=Decimal("200"))]
    assert calculate_net_worth(accounts) == Decimal("300")
```
