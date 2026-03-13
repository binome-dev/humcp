---
name: querying-postgresql-database
description: Connects to PostgreSQL databases to execute SQL queries and explore schema. Use when the user asks to query a database, list tables, describe table structure, or perform any database operations.
---

# PostgreSQL Database Tools

Tools for connecting to and querying PostgreSQL databases using SQLAlchemy async.

## Setup

Set the `DATABASE_URL` environment variable:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
```

## Execute SQL Queries

```python
# SELECT query - returns all matching rows
result = await execute_query("SELECT * FROM users")
# Returns: {"success": True, "data": {"rows": [...], "row_count": N}}
# NOTE: Do NOT add LIMIT unless the user explicitly asks to limit results

# INSERT/UPDATE/DELETE - returns status
result = await execute_query("INSERT INTO users (name) VALUES ('Alice')")
# Returns: {"success": True, "data": {"status": "INSERT 0 1", "message": "..."}}

# Complex queries with CTEs
result = await execute_query("""
    WITH active_users AS (
        SELECT * FROM users WHERE status = 'active'
    )
    SELECT * FROM active_users WHERE created_at > '2024-01-01'
""")
```

## List Tables

```python
# List tables in public schema (default)
result = await list_tables()
# Returns: {"success": True, "data": {"schema": "public", "tables": ["users", "orders"], "count": 2}}

# List tables in specific schema
result = await list_tables(schema="analytics")
```

## Describe Table Structure

```python
result = await describe_table("users")
# Returns column definitions:
# {
#   "success": True,
#   "data": {
#     "schema": "public",
#     "table": "users",
#     "columns": [
#       {"name": "id", "type": "integer", "nullable": False, ...},
#       {"name": "email", "type": "character varying", "nullable": False, ...}
#     ],
#     "column_count": 2
#   }
# }

# Describe table in specific schema
result = await describe_table("events", schema="analytics")
```

## Error Handling

All tools return `{"success": False, "error": "..."}` on failure:
- Missing DATABASE_URL environment variable
- Connection failures
- SQL syntax errors
- Permission denied
- Table not found
