# Read the file
with open('backend/app/services/auth_service.py', 'r') as f:
    lines = f.readlines()

# Process line by line to remove UUID conversions
new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    line_num = i + 1
    
    # Skip lines that are part of removed UUID conversion blocks
    if line_num <= skip_until:
        continue
    
    # Fix around line 226 (get_user_by_id)
    if 'user_uuid = uuid.UUID(user_id)' in line and 'get_user_by_id' in ''.join(lines[max(0,i-10):i]):
        # Skip the try/except block (next 3 lines)
        skip_until = line_num + 2
        continue
    
    # Fix around line 289 (check_and_increment_usage)
    if 'user_uuid = uuid.UUID(user_id)' in line and 'check_and_increment_usage' in ''.join(lines[max(0,i-15):i]):
        # Skip the try/except block (next 3 lines) 
        skip_until = line_num + 2
        continue
    
    # Replace user_uuid with user_id in WHERE clauses
    if 'User.id == user_uuid' in line:
        line = line.replace('user_uuid', 'user_id')
    
    new_lines.append(line)

# Write back
with open('backend/app/services/auth_service.py', 'w') as f:
    f.writelines(new_lines)

print("Fixed all UUID conversions in auth_service.py")
