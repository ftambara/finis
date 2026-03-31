# Finis development guide

## Code Style

### Auto
- Use `mypy` in strict mode with `django-stubs`.
- Corollary: Every function signature must use fully-parameterized types.
- Use ruff format.
- Use ruff check with the selected rules.
- python/tests: do not add docstrings to test functions.

### Judgment-based
- ui/css: Use tailwind utility classes instead of inline styles
- config: Never access environment variables outside of `settings.py`. Use `from django.conf import settings`.
- errors: Prefer explicit error handling with typed errors
- comments: explain why, not what. Use proper punctuation.
- python/tests: use table-driven test style.
- reduce nesting by using early returns, guard clauses, helper methods and similar techniques.
- spelling: American English.
- sql: always review django migrations; the use of database-level constraints is encouraged.
- sql: Use auto_now is discouraged. Prefer DB triggers like SQL-alchemy does.
- sql: Nullable and blank fields are almost never the right call. If something might be missing initially, use a related model (e.g., `OneToOneField`) to avoid the nullable field.

## Commit style

- `feat`: New feature or functionality (touches production code)
- `fix`: Bug fix (touches production code)
- `chore`: Non-production changes (docs, tests, config, CI, refactoring agents instructions, etc.)
- commit message := <header>\n\n<body>
- header := <type>: <title>
- type := `feat` | `fix` | `chore`
- title := Short summary of the changes (keep under 72 characters). Lowercase. Does not end in a period.
- body := body 

Note: If the changes don't have a good title, it's a sign that your commit does too much.

## CI

- Automate all the "Code Style"."Auto" section checks
- Every job in `.github/workflows/` must declare `timeout-minutes` - prevents stuck runners from burning credits indefinitely

## Security

See [.agents/security.md](.agents/security.md) for SQL security guidelines.
