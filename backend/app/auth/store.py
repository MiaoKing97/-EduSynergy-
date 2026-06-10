"""
SQLite-backed async user and authentication store.
Replaces the in-memory user list from frontend store.js.
"""
import aiosqlite
import os
from typing import Optional
from passlib.context import CryptContext
from .models import User, UserInDB, UserCreate, TokenPayload


PWD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "users.db")

# Default accounts that mirror frontend store.js defaultUsers
DEFAULT_USERS = [
    {"id": "u_admin", "username": "admin", "password": "123", "role": "admin", "subject": "全局管理"},
    {"id": "u_math1", "username": "张老师", "password": "123", "role": "teacher", "subject": "高等数学"},
    {"id": "u_math2", "username": "王老师", "password": "123", "role": "teacher", "subject": "高等数学"},
    {"id": "u_c1", "username": "李老师", "password": "123", "role": "teacher", "subject": "C语言"},
    {"id": "u_c2", "username": "赵老师", "password": "123", "role": "teacher", "subject": "C语言"},
    {"id": "u_web1", "username": "陈老师", "password": "123", "role": "web_teacher", "subject": "网页设计"},
    {"id": "u_web2", "username": "林老师", "password": "123", "role": "web_teacher", "subject": "网页设计"},
]


def hash_password(password: str) -> str:
    return PWD_CONTEXT.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return PWD_CONTEXT.verify(plain, hashed)


def get_password(password: str) -> str:
    """Public helper for one-off hashing (e.g. seeding)."""
    return hash_password(password)


class UserStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Create tables and seed default users if empty."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    subject TEXT DEFAULT '通用学科',
                    is_active INTEGER DEFAULT 1
                )
            """)
            # Check if already seeded
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            count = (await cursor.fetchone())[0]
            if count == 0:
                for u in DEFAULT_USERS:
                    await db.execute(
                        "INSERT INTO users (id, username, hashed_password, role, subject) VALUES (?, ?, ?, ?, ?)",
                        (u["id"], u["username"], hash_password(u["password"]), u["role"], u["subject"]),
                    )
                await db.commit()

    async def get_user(self, user_id: str) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            return UserInDB(**dict(row))

    async def get_user_by_username(self, username: str) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = await cursor.fetchone()
            if not row:
                return None
            return UserInDB(**dict(row))

    async def create_user(self, data: UserCreate) -> UserInDB:
        hashed = hash_password(data.password)
        user = UserInDB(
            id=data.id or data.username,
            username=data.username,
            hashed_password=hashed,
            role=data.role,
            subject=data.subject,
        )
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO users (id, username, hashed_password, role, subject) VALUES (?, ?, ?, ?, ?)",
                (user.id, user.username, user.hashed_password, user.role, user.subject),
            )
            await db.commit()
        return user

    async def update_user(self, user_id: str, **fields) -> Optional[User]:
        if "password" in fields:
            fields["hashed_password"] = hash_password(fields.pop("password"))
        if not fields:
            return await self.get_user(user_id)
        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [user_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            await db.commit()
        return await self.get_user(user_id)

    async def list_users(self) -> list[UserInDB]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users ORDER BY username")
            rows = await cursor.fetchall()
            return [UserInDB(**dict(row)) for row in rows]

    async def delete_user(self, user_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await db.commit()
            return cursor.rowcount > 0
