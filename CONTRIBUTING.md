# Contributing to AI Morning Brief

Thank you for your interest in contributing! This document covers coding standards, naming conventions, project structure guidelines, and the contribution workflow.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Branching Strategy](#branching-strategy)
- [Coding Standards](#coding-standards)
- [Naming Conventions](#naming-conventions)
- [Project Structure Guidelines](#project-structure-guidelines)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

---

## Getting Started

1. Fork the repository and clone your fork.
2. Create a virtual environment and install dev dependencies:

   ```bash
   uv venv
   uv pip install -e ".[dev]"
   ```

3. Create a feature branch from `development`:

   ```bash
   git checkout development
   git pull origin development
   git checkout -b feature/your-feature-name
   ```

---

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `master` | Production — deploys to prod Lambda |
| `development` | Integration — deploys to dev Lambda |
| `feature/*` | New features — branch from `development` |
| `fix/*` | Bug fixes — branch from `development` |
| `refactor/*` | Code improvements — branch from `development` |

All work merges into `development` first, then `development` merges into `master` for production releases.

---

## Coding Standards

### Python

- **Version:** Python 3.12+ (matches the Lambda runtime).
- **Style:** [PEP 8](https://peps.python.org/pep-0008/) — enforced by linting.
- **Line length:** 88 characters (Black default).
- **Type hints:** Use type annotations on all public function signatures.
- **Docstrings:** Required on all public functions, classes, and modules. Use [Google-style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) docstrings:

  ```python
  def fetch_brief() -> dict:
      """Search today's news and generate the morning brief.

      Returns:
          Parsed brief as a dict with keys: date, headline, bullets,
          sources, deepDive.

      Raises:
          RuntimeError: If Tavily returns no results.
      """
  ```

- **Imports:** Group in order: stdlib, third-party, local. Alphabetize within groups.
- **Constants:** `UPPER_SNAKE_CASE` for module-level constants. Prefix private constants with `_`.
- **Logging:** Use `logging` module (not `print()`). Logger names follow module hierarchy: `morning_brief.fetcher`, `morning_brief.sender`, etc.

### Terraform

- **Version:** Terraform >= 1.6.
- **Provider:** AWS provider `~> 5.0`.
- **Naming:** Resource names are suffixed with `var.environment` (e.g. `ai-morning-brief-dev`).
- **Secrets:** Always marked `sensitive = true` in variable definitions.
- **Structure:** Reusable module in `terraform/modules/`, consumed by environment roots.

### Templates

- **HTML email:** Table-based layout for email client compatibility. Inline styles only.
- **Plain text:** Clean fallback with no HTML. Mirrors the same content structure.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Python files | `snake_case.py` | `lambda_function.py` |
| Python functions | `snake_case` | `fetch_brief()` |
| Python classes | `PascalCase` | `ConfigError` |
| Python constants | `UPPER_SNAKE_CASE` | `MAX_LINKS` |
| Private members | `_leading_underscore` | `_conf()`, `_PROMPT_PATH` |
| Terraform resources | `snake_case` | `aws_lambda_function.morning_brief` |
| Terraform variables | `snake_case` | `lambda_timeout` |
| Git branches | `type/kebab-case` | `feature/add-retry-logic` |
| Environment variables | `UPPER_SNAKE_CASE` | `TAVILY_API_KEY` |

---

## Project Structure Guidelines

### Source code (`src/`)

All application code lives in `src/`. Each module has a single responsibility:

- `config.py` — Configuration loading (no business logic)
- `fetcher.py` — Web search and LLM interaction
- `renderer.py` — Template rendering (presentation layer)
- `sender.py` — Email delivery (I/O layer)
- `lambda_function.py` — Orchestration only (no business logic)

**Do not** add business logic to `lambda_function.py`. It should only wire together the pipeline stages.

### Templates (`src/templates/`)

Email templates are Jinja2 files. Keep presentation in templates, not in Python code.

### Prompts (`src/prompts/`)

LLM system prompts live in text files with `{placeholder}` syntax for runtime injection.

### Tests (`tests/`)

One test file per source module. Test file names mirror source files: `test_config.py` tests `config.py`.

### Infrastructure (`terraform/`)

- `modules/` — Reusable, environment-agnostic Terraform module.
- `environments/` — Environment-specific root modules that call the shared module.

---

## Testing

Run the full test suite before submitting any changes:

```bash
uv run pytest -v
```

### Test guidelines

- Mock all external services (Tavily API, LiteLLM, Gmail SMTP).
- Use the shared fixtures in `conftest.py` (`sample_brief`, `tavily_results`).
- Test both success and failure paths.
- Aim for clear, descriptive test names: `test_missing_key_raises`, not `test_1`.

---

## Commit Messages

Use clear, imperative-mood commit messages:

```
Add config validation for required secrets
Fix SMTP timeout not being applied
Refactor fetcher to validate LLM response structure
```

Keep commits logically grouped — one concern per commit.

---

## Pull Request Process

1. Ensure all tests pass: `uv run pytest -v`
2. Target `development` branch (not `master`).
3. Write a clear PR description explaining **what** changed and **why**.
4. Keep PRs focused — one feature or fix per PR.
5. Request review from a maintainer.

---

## Security

- **Never** commit secrets, API keys, or passwords.
- `config.ini` is git-ignored — keep it that way.
- All secrets in CI/CD flow through GitHub Secrets -> Terraform variables -> Lambda env vars.
- Mark sensitive Terraform variables with `sensitive = true`.
- Report security issues privately — do not open public issues for vulnerabilities.
