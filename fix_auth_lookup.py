# Read the file
with open('backend/app/services/auth_service.py', 'r') as f:
    content = f.read()

# Replace the get_user_by_id function to use string comparison
old_code = """    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        \"\"\"Get user by ID\"\"\"
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        result = await self.session.execute(
            select(User).where(User.id == user_uuid)
        )
        return result.scalar_one_or_none()"""

new_code = """    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        \"\"\"Get user by ID\"\"\"
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()"""

content = content.replace(old_code, new_code)

# Write back
with open('backend/app/services/auth_service.py', 'w') as f:
    f.write(content)

print("Fixed get_user_by_id to use string comparison")
