# Security guidelines for agents

## SQL Security

- **Never** use f-strings with user-controlled values in SQL queries - this creates SQL injection vulnerabilities
- Use parameterized queries for all VALUES: `cursor.execute("SELECT * FROM t WHERE id = %s", [id])`
- Table/column names from Django ORM metadata (`model._meta.db_table`) are trusted sources
- When raw SQL is necessary with dynamic table/column names:

  ```python
  # Build query string separately from execution, document why identifiers are safe
  table = model._meta.db_table  # Trusted: from Django ORM metadata
  query = f"SELECT COUNT(*) FROM {table} WHERE team_id = %s"
  cursor.execute(query, [team_id])  # Values always parameterized
  ```

## ORM Security

Django's `__` notation in ORM lookups allows FK traversal. If a user-controlled value is interpolated into a `.filter()`, `.exclude()`, or `Q()` dict key, an attacker can traverse relationships to exfiltrate sensitive fields (e.g. `user__password`, `team__api_token`).

**Vulnerable pattern** - Variable interpolated into filter key:

```python
# key is user-controlled — attacker can pass "user__password"
queryset.filter(**{f"{key}__icontains": value})  # VULNERABLE
```

**Safe patterns**:

```python
# Validate against an allowlist before use
ALLOWED_FIELDS = {"name", "email", "created_at"}
if key not in ALLOWED_FIELDS:
    raise ValueError(f"Invalid filter field: {key}")
queryset.filter(**{f"{key}__icontains": value})  # SAFE

# Hardcoded keys are always safe
queryset.filter(**{"name__icontains": value})  # SAFE
queryset.filter(name__icontains=value)  # SAFE
```

> **JSONField note:** If the first path segment is a JSONField (e.g. `detail__`), Django routes all subsequent `__` as JSON key lookups rather than FK traversals, which mitigates the risk. An allowlist is still recommended as defense in depth.
