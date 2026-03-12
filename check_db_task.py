
import sqlite3
import os

db_paths = [
    r"c:\Users\mrshibly\Desktop\Research Agent\backend\research.db",
    r"c:\Users\mrshibly\Desktop\Research Agent\backend\data\research.db"
]
task_id = "7b6a0c161f8d4265a6be0d33c077b7d2"

for db_path in db_paths:
    print(f"Checking {db_path}...")
    if not os.path.exists(db_path):
        print(f" - ERROR: Not found.")
        continue
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, topic, status FROM research_tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            print(f" - FOUND: ID={row[0]}, Topic={row[1]}, Status={row[2]}")
        else:
            print(f" - NOT FOUND: Task missing.")
            cursor.execute("SELECT id, topic FROM research_tasks ORDER BY created_at DESC LIMIT 3")
            rows = cursor.fetchall()
            if rows:
                print("   Recent tasks:")
                for r in rows:
                    print(f"    * {r[0]}: {r[1]}")
        conn.close()
    except Exception as e:
        print(f" - DB Error: {e}")
