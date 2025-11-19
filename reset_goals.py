from backend.db import engine
from sqlalchemy import text

SQL = """
TRUNCATE goals, steps, user_steps, reflections, evidence, xp_log
RESTART IDENTITY CASCADE;
"""

with engine.connect() as conn:
    conn.execute(text(SQL))
    conn.commit()

print("Goals and related data wiped (users preserved).")
