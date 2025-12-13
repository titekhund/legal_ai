# Read the file
with open('backend/app/services/auth_service.py', 'r') as f:
    content = f.read()

# Replace timezone-aware datetime with naive datetime
content = content.replace(
    'datetime.now(timezone.utc)',
    'datetime.utcnow()'
)

# Write back
with open('backend/app/services/auth_service.py', 'w') as f:
    f.write(content)

print("Fixed timezone issues - using naive UTC datetimes")
