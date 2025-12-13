# Read the file
with open('backend/app/db/models.py', 'r') as f:
    content = f.read()

# Replace uuid.UUID type hints with str
content = content.replace('Mapped[uuid.UUID]', 'Mapped[str]')

# Also replace the default value from uuid.uuid4 to a lambda that returns string
content = content.replace('default=uuid.uuid4,', 'default=lambda: str(uuid.uuid4()),')

# Write back
with open('backend/app/db/models.py', 'w') as f:
    f.write(content)

print("Fixed UUID type hints for SQLite")
