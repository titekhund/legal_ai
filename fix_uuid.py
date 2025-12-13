import sys

# Read the file
with open('backend/app/db/models.py', 'r') as f:
    content = f.read()

# Replace PostgreSQL UUID with SQLite-compatible String
content = content.replace(
    'from sqlalchemy.dialects.postgresql import UUID',
    'from sqlalchemy import String'
)

# Replace UUID columns with String(36) for SQLite
content = content.replace(
    'UUID(as_uuid=True)',
    'String(36)'
)

# Write back
with open('backend/app/db/models.py', 'w') as f:
    f.write(content)

print("Fixed UUID compatibility for SQLite")
