import sqlite3


def create_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS members (
                        id INTEGER PRIMARY KEY,
                        numberno INTEGER,
                        joined_date DATE,
                        realname TEXT,
                        name TEXT,
                        highest_role TEXT,
                        credit INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1
                   )
                   """)
    conn.commit()
    conn.close()

# create_db()

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM members")
result = cursor.fetchall()

print(result)
