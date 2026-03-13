import sqlite3

conn = sqlite3.connect("booth.db")
cursor = conn.cursor()

cursor.execute("SELECT id, email, verified_at, used FROM booth_sessions")
rows = cursor.fetchall()

print("\nBooth Sessions\n")
print(f"{'ID':<5}{'EMAIL':<25}{'VERIFIED_AT':<25}{'USED'}")
print("-"*70)

for r in rows:
    id, email, verified_at, used = r
    print(f"{id:<5}{email:<25}{verified_at:<25}{used}")

print()
